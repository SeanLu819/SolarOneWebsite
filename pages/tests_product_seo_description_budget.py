"""v1.9.8 guard: product descriptions fit the SERP budget in *every* locale.

v1.9.7 shipped the non-English branch of ``Product.seo_description`` returning
the translated ``description`` verbatim:

    if lang == 'en':
        return build_seo_description(self, lang)
    return self.t('description', lang)          # <- raw body copy

Most products have no translated description at all, so those branches fell back
to the English original and shipped 168-387 characters into a tag Google cuts at
about 155. ``/fr/products/fl6m/`` served 343 characters while ``/products/fl6m/``
served the 156-char formula. The project side never had this gap:
``_DictProject.seo_description`` clamps in every locale.

The English formula is deliberately not reused for non-English: it is English
prose, and putting it on a /fr/ page would contradict the hreflang signal that
same page emits. Clamping the locale's own copy keeps it localised and inside
the budget, on the same sentence/word-boundary policy as the project formula.

Both code paths must agree — production runs ``IS_VERCEL`` off the seed mirror,
so a one-sided fix would only ever be wrong in one environment.
"""
import json
import os

from django.test import SimpleTestCase, TestCase
from django.test import Client as TestClient

from pages.utils import (
    MAX_SEO_DESCRIPTION_LEN,
    build_seo_description,
    fit_description,
)
from pages.views.utils import _DictProduct, _load_seed

LANGS = ['en', 'fr', 'es', 'de', 'ru', 'ar']

MAX_SEO_TITLE = 60
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

# news_detail.html appends a site suffix to the article's stored title.
NEWS_TITLE_SUFFIX = ' — SolarOne News'
NEWS_SLUG = 'low-cct-high-cri-high-mast-led-retrofit'


def _descriptions(seed_products):
    """Every product x locale, through the seed path production actually uses."""
    out = []
    for item in seed_products:
        p = _DictProduct(item)
        for lang in LANGS:
            out.append((item['slug'], lang, p.seo_description(lang)))
    return out


class FitDescriptionPolicyTests(SimpleTestCase):
    """The clamp itself: boundary aware, never over budget, never empty."""

    def test_short_text_passes_through_untouched(self):
        prose = 'A short description.'
        self.assertEqual(fit_description(prose), prose)

    def test_sentence_boundary_is_preferred(self):
        prose = ('First sentence is comfortably long enough to fit. ' * 4).strip()
        self.assertGreater(len(prose), MAX_SEO_DESCRIPTION_LEN)
        out = fit_description(prose)
        self.assertLessEqual(len(out), MAX_SEO_DESCRIPTION_LEN)
        self.assertTrue(out.endswith('.'), out)
        self.assertIn('First sentence', out)

    def test_word_boundary_fallback_adds_ellipsis(self):
        prose = 'x' * 300
        out = fit_description(prose)
        self.assertLessEqual(len(out), MAX_SEO_DESCRIPTION_LEN)
        self.assertIn('…', out)

    def test_never_exceeds_the_budget(self):
        for n in (120, 159, 160, 161, 200, 400, 900):
            with self.subTest(n=n):
                self.assertLessEqual(len(fit_description('word ' * n)),
                                     MAX_SEO_DESCRIPTION_LEN)

    def test_empty_input_degrades_gracefully(self):
        self.assertEqual(fit_description(''), '')
        self.assertEqual(fit_description(None), '')


class ProductDescriptionBudgetTests(SimpleTestCase):
    """All 24 products x 6 locales stay inside the SERP budget."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rows = _descriptions(_load_seed()['products'])

    def test_no_locale_exceeds_the_budget(self):
        over = [(s, l, len(v), v) for s, l, v in self.rows if len(v) > MAX_SEO_DESCRIPTION_LEN]
        self.assertEqual(over, [], 'over budget: %s' % over[:3])

    def test_every_language_produced_a_non_empty_description(self):
        empty = [(s, l) for s, l, v in self.rows if not v.strip()]
        self.assertEqual(empty, [], 'empty descriptions: %s' % empty)

    def test_if_the_sweep_finds_nothing_the_test_is_vacuous(self):
        self.assertGreaterEqual(len(self.rows), 24 * 6)

    def test_english_stays_inside_the_budget_and_unique(self):
        """English mixes hand-written overrides with the formula; what must hold
        is that the clamp applies to both and that no two pages collide."""
        en = [(s, v) for s, l, v in self.rows if l == 'en']
        over = [(s, len(v)) for s, v in en if len(v) > MAX_SEO_DESCRIPTION_LEN]
        self.assertEqual(over, [], 'over budget: %s' % over)
        slugs = [s for s, _v in en]
        self.assertEqual(len(slugs), len(set(slugs)))
        texts = [v for _s, v in en]
        self.assertEqual(len(texts), len(set(texts)),
                         'two product pages share a description')

    def test_non_english_is_not_the_english_formula(self):
        """The clamp must not leak English copy onto a /fr/ page."""
        leaked = []
        for slug, lang, out in self.rows:
            if lang == 'en':
                continue
            seed = {p['slug']: p for p in _load_seed()['products']}[slug]
            fake = type('O', (), {'name': seed.get('name', ''),
                                  'model_number': seed.get('model_number', ''),
                                  'power': seed.get('power', '')})()
            if out == build_seo_description(fake):
                leaked.append((slug, lang))
        self.assertEqual(leaked, [], 'English formula on %s' % leaked[:3])

    def test_non_english_is_derived_from_the_locale_copy(self):
        """Clamped, not replaced: the output must start like the source text."""
        seed_by_slug = {p['slug']: p for p in _load_seed()['products']}
        for slug, lang, out in self.rows:
            if lang == 'en':
                continue
            source = (seed_by_slug[slug].get('translations', {}) or {}).get(lang, {})
            raw = (source.get('description') or
                   seed_by_slug[slug].get('description', ''))
            if not raw:
                continue
            # clamped iff the source was longer than the budget
            if len(raw) > MAX_SEO_DESCRIPTION_LEN:
                self.assertTrue(len(out) <= MAX_SEO_DESCRIPTION_LEN)


class ProductDescriptionModelPathTests(TestCase):
    """The DB path must clamp identically to the seed mirror.

    A mutation probe showed the seed-path tests alone stayed green when the
    clamp was deleted from ``Product.seo_description``, because the rendered
    pages are served from the seed mirror in the test environment. Both
    mirrors are held here, or the fix silently exists in only one of them.
    """

    def test_model_clamps_every_locale(self):
        from pages.models import Product

        for item in _load_seed()['products']:
            product = Product(
                slug=item.get('slug', ''),
                name=item.get('name', ''),
                description=item.get('description', ''),
                translations=item.get('translations', {}) or {},
            )
            for lang in LANGS:
                with self.subTest(slug=item['slug'], lang=lang):
                    out = product.seo_description(lang)
                    self.assertTrue(out.strip())
                    self.assertLessEqual(len(out), MAX_SEO_DESCRIPTION_LEN,
                                         '%s/%s served %d chars: %r'
                                         % (item['slug'], lang, len(out), out))

    def test_model_and_seed_paths_agree(self):
        """The mirrors are two copies of one formula; drift ships reality-only bugs."""
        from pages.models import Product

        for item in _load_seed()['products']:
            product = Product(slug=item.get('slug', ''),
                              name=item.get('name', ''),
                              description=item.get('description', ''),
                              translations=item.get('translations', {}) or {})
            seed_obj = _DictProduct(item)
            for lang in LANGS:
                with self.subTest(slug=item['slug'], lang=lang):
                    self.assertEqual(product.seo_description(lang),
                                     seed_obj.seo_description(lang))


class SiteTitleBudgetTests(SimpleTestCase):
    """v1.9.8: the two <title> strings that were still over the 60-char budget.

    ``/products/`` carried a 64-char literal in a ``{% blocktrans %}`` block,
    and ``news_detail.html`` appends ' — SolarOne News' to the stored article
    title, which put that page at 80. Both now fit; both are locked here.
    """

    def test_products_title_literal_fits(self):
        import re
        path = os.path.join(TEMPLATE_DIR, 'products.html')
        with open(path, encoding='utf-8') as fh:
            src = fh.read()
        m = re.search(r'{% block title %}{% blocktrans %}(.*?){% endblocktrans %}',
                      src)
        self.assertTrue(m, 'products.html has a {{% blocktrans %}} title block')
        self.assertLessEqual(len(m.group(1)), MAX_SEO_TITLE,
                             'products <title> is %d chars: %r'
                             % (len(m.group(1)), m.group(1)))

    def test_title_and_og_title_stay_paired(self):
        """A half-applied edit is what put the 64-char literal back on the
        og:title block while the <title> was already shortened: the i18n
        coverage guard then failed on a string the page no longer used."""
        import re
        for name in os.listdir(TEMPLATE_DIR):
            if not name.endswith('.html'):
                continue
            with open(os.path.join(TEMPLATE_DIR, name), encoding='utf-8') as fh:
                src = fh.read()
            pairs = {}
            for block in ('title', 'og_title'):
                m = re.search(r'\{%% block %s %%\}%% blocktrans %%'
                              r'(.*?){%% endblocktrans %%}' % block, src)
                if m:
                    pairs[block] = m.group(1)
            if len(pairs) == 2 and pairs['title'] != pairs['og_title']:
                self.fail('%s: <title> and og:title diverged — %r vs %r'
                          % (name, pairs['title'], pairs['og_title']))

    def test_every_blocktrans_title_fits(self):
        import re
        over = []
        for name in os.listdir(TEMPLATE_DIR):
            if not name.endswith('.html'):
                continue
            with open(os.path.join(TEMPLATE_DIR, name), encoding='utf-8') as fh:
                src = fh.read()
            for m in re.finditer(r'{% block title %}{% blocktrans %}(.*?)'
                                 r'{% endblocktrans %}', src):
                n = len(m.group(1))
                if n > MAX_SEO_TITLE:
                    over.append('%s = %d' % (name, n))
        self.assertEqual(over, [], 'titles over %d: %s' % (MAX_SEO_TITLE, over))

    @staticmethod
    def _seed_json_news():
        path = os.path.join(os.path.dirname(__file__), '..', 'seed_data.json')
        with open(path, encoding='utf-8') as fh:
            return {n.get('slug'): n.get('title', '') for n in json.load(fh)['news']}

    @staticmethod
    def _build_artifact_news():
        return {n.get('slug'): n.get('title', '')
                for n in _load_seed()['news']}

    def test_news_title_in_seed_data_json_fits(self):
        for slug, title in self._seed_json_news().items():
            with self.subTest(slug=slug):
                total = len(title) + len(NEWS_TITLE_SUFFIX)
                self.assertLessEqual(total, MAX_SEO_TITLE,
                                     'seed json title renders %d chars: %r'
                                     % (total, title))
                # v1.10.2: the keyword assertions below used to run for EVERY
                # article, so the Tianjin case study's required terms became an
                # accidental contract for all future news. They are scoped to
                # that one slug now; the 60-char budget above still guards
                # every title. ('Tianjin Binhai Airport' was also wrong — the
                # real title says "Tianjin Binhai International Airport", so
                # this assertion could never have passed once the length check
                # above was fixed.)
                if slug == 'low-cct-high-cri-high-mast-led-retrofit':
                    for term in ('FL6M-480W', 'Binhai'):
                        self.assertIn(term, title)

    def test_news_title_in_the_build_artifact_fits(self):
        for slug, title in self._build_artifact_news().items():
            with self.subTest(slug=slug):
                total = len(title) + len(NEWS_TITLE_SUFFIX)
                self.assertLessEqual(total, MAX_SEO_TITLE,
                                     'news <title> renders %d chars: %r'
                                     % (total, title))

    def test_both_seed_mirrors_will_not_drift(self):
        """_load_seed() prefers pages/seed_data.py over seed_data.json. A probe
        showed a guard reading only that artifact stays green when the JSON is
        edited, so both are read here and cross-checked against each other."""
        js = self._seed_json_news()
        artifact = self._build_artifact_news()
        for slug in set(js) | set(artifact):
            with self.subTest(slug=slug):
                if slug in js and slug in artifact:
                    self.assertEqual(js[slug], artifact[slug],
                                     'seed_data.json and pages/seed_data.py '
                                     'disagree on the news title')


class ProductDescriptionRenderTests(TestCase):
    """What a /fr/ visitor actually receives."""

    def _get(self, url):
        response = TestClient().get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200,
                         '%s returned %s' % (url, response.status_code))
        return response.content.decode('utf-8')

    def _meta(self, html):
        return html

    def test_french_product_pages_render_within_budget(self):
        """Regression lock for the 343-character description on /fr/products/fl6m/."""
        for slug in ('fl6m', 'fl4m', 'fl1m', 'fl9m'):
            with self.subTest(slug=slug):
                page = self._get('/fr/products/%s/' % slug)
                import re as _re
                import html as _html
                m = _re.search(r'<meta name="description" content="([^"]*)"', page)
                self.assertTrue(m, '%s served no meta description' % slug)
                desc = _html.unescape(m.group(1))
                self.assertLessEqual(len(desc), MAX_SEO_DESCRIPTION_LEN,
                                     '%s served a %d-char description'
                                     % (slug, len(desc)))

    def test_english_product_pages_are_unchanged(self):
        page = self._get('/products/fl6m/')
        self.assertIn('SolarOne FL6M', page)
        import re as _re
        m = _re.search(r'<meta name="description" content="([^"]*)"', page)
        self.assertTrue(m)
        self.assertLessEqual(len(m.group(1)), MAX_SEO_DESCRIPTION_LEN)
