"""P4 guards — the stadium-lighting landing page and the hub internal links.

The plan this batch implements proposed **six** category landing pages. Measuring
the portfolio first rejected four of them:

    category          products  projects  page worth building?
    SPORTS_LIGHTING        2        20    yes — 5 010/mo of measured volume
    AREA_SITE             11         1    yes
    FLOODLIGHT             4         0    no — four products is a thin page
    HIGHBAY_LOWBAY         2         0    no
    ROADWAY                2         1    no
    ACCESSORY              3         0    no

So this file guards **one** page, and — just as importantly — it locks the
*rejection* in: a future batch must not quietly add a page for a category that
cannot fill one. The category count is pinned literally so the decision has to
be re-made on purpose.

Expectation sourcing (iron law 4b): every threshold and word list below is a
product decision written out literally. Nothing is derived from the constant it
validates.
"""

import re

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.utils import CATEGORY_KEYWORD
from pages.views.data_loaders import get_products, get_projects
from pages.views.related_links import (
    PRODUCT_CATEGORY_TO_PROJECT_SPORTS,
    PROJECT_SPORT_TO_PRODUCT_CATEGORIES,
)
from pages.views.utils import _load_seed
from pages.views.views_stadium import (
    FEATURED_PRODUCT_SLUGS,
    STADIUM_CATEGORY,
    VENUE_PROJECT_LIMIT,
)

LANGS = ('en', 'fr', 'es', 'de', 'ru', 'ar')

#: SERP budgets this project holds every page to.
MAX_TITLE_LEN = 60
MAX_DESCRIPTION_LEN = 160

#: Product decisions:
#:
#: * a landing page below this many body words has nothing to say; the four
#:   rejected categories sit at 2–4 products, well under it.
#: * every section needs a real heading, because v1.10.20 found the product
#:   pages presenting theirs as <span>s.
MIN_BODY_WORDS = 250

#: The one category allowed its own landing page. Literal: adding a second is a
#: copy decision that has to be re-argued, not an accident of the code.
CATEGORIES_WITH_LANDING_PAGES = frozenset({'SPORTS_LIGHTING'})

#: Categories explicitly measured and rejected, with the reason. Kept so the
#: next batch reads this before building them.
REJECTED_CATEGORIES = {
    'FLOODLIGHT': '4 products, 0 projects — thin page',
    'HIGHBAY_LOWBAY': '2 products, 0 projects — thin page',
    'ROADWAY': '2 products, 1 project — thin page',
    'ACCESSORY': '3 products, 0 projects — thin page',
}

HREF_RE = re.compile(r'href="([^"]+)"')
HREFLANG_RE = re.compile(r'hreflang="([a-z-]+)"')
IMG_TAG_RE = re.compile(r'<img[^>]*>')
ALT_RE = re.compile(r'alt="([^"]*)"')
H_TAG_RE = re.compile(r'<h([1-3])[^>]*>(.*?)</h\1>', re.S)


def _body_words(html):
    """Visible word count with nav / footer / scripts removed."""
    body = html[html.find('<body'):]
    body = re.sub(r'<(nav|footer|header)[^>]*>.*?</\1>', '', body, flags=re.S)
    body = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', '',
                  body, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', body)
    return len(re.sub(r'\s+', ' ', text).strip().split())


def _text(fragment):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', fragment)).strip()


class StadiumPageTests(TestCase):
    """P4-A — /stadium-lighting/ renders, and renders one page's worth."""

    @classmethod
    def setUpTestData(cls):
        cls.seeds = _load_seed()
        cls.product_categories = {
            p.get('category') for p in cls.seeds.get('products', [])}

    def _get(self, path):
        return Client().get(path, HTTP_HOST='localhost').content.decode('utf-8')

    def test_the_page_exists_in_every_locale(self):
        for lang in LANGS:
            prefix = '' if lang == 'en' else '/%s' % lang
            with self.subTest(lang=lang):
                response = Client().get('%s/stadium-lighting/' % prefix,
                                        HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)

    def test_it_is_not_an_orphan(self):
        """Reachable from the two pages a buyer actually lands on.

        A landing page linked only from the sitemap is how one quietly fails:
        crawlers follow it, humans never see it.
        """
        index = self._get('/products/')
        self.assertIn(reverse('stadium_lighting'), index,
                      '/products/ does not link to the stadium page')
        for path in ('/projects/football/', '/projects/tennis/'):
            with self.subTest(path=path):
                body = self._get(path)
                self.assertIn(reverse('stadium_lighting'), body,
                              '%s does not link to the stadium page' % path)

    def test_the_hand_off_is_absent_from_the_general_project_index(self):
        """/projects/ is not a collection page; the link would be noise there."""
        self.assertNotIn(reverse('stadium_lighting'), self._get('/projects/'))

    def test_body_copy_meets_the_word_budget(self):
        for lang in LANGS:
            prefix = '' if lang == 'en' else '/%s' % lang
            with self.subTest(lang=lang):
                words = _body_words(
                    self._get('%s/stadium-lighting/' % prefix))
                self.assertGreaterEqual(
                    words, MIN_BODY_WORDS,
                    'stadium page has only %d visible words in %s — a landing '
                    'page thinner than this cannot rank for a generic term'
                    % (words, lang))

    def test_title_and_description_fit_the_serp_budget(self):
        for lang in LANGS:
            prefix = '' if lang == 'en' else '/%s' % lang
            body = self._get('%s/stadium-lighting/' % prefix)
            title = re.search(r'<title>(.*?)</title>', body, re.S).group(1)
            desc = re.search(
                r'<meta name="description" content="([^"]*)"', body).group(1)
            with self.subTest(lang=lang):
                self.assertLessEqual(
                    len(title), MAX_TITLE_LEN,
                    'title is %d chars: %r' % (len(title), title))
                # Measured after unescaping: `&` costs four characters in the
                # raw attribute and one in the text a crawler parses.
                import html as html_mod
                self.assertLessEqual(
                    len(html_mod.unescape(desc)), MAX_DESCRIPTION_LEN,
                    'description is %d chars: %r'
                    % (len(html_mod.unescape(desc)), desc))

    def test_canonical_is_self_referencing(self):
        """A collection page whose canonical points elsewhere is not indexable."""
        for lang in ('en', 'fr', 'de'):
            prefix = '' if lang == 'en' else '/%s' % lang
            body = self._get('%s/stadium-lighting/' % prefix)
            canonical = re.search(
                r'<link rel="canonical" href="([^"]*)"', body).group(1)
            expected = settings.CANONICAL_ORIGIN
            expected += '' if lang == 'en' else '/%s' % lang
            with self.subTest(lang=lang):
                self.assertEqual(canonical, expected + '/stadium-lighting/')

    def test_all_six_locales_are_declared(self):
        body = self._get('/stadium-lighting/')
        declared = set(HREFLANG_RE.findall(body))
        self.assertEqual(
            declared, set(LANGS) | {'x-default'},
            'the stadium page must declare every locale plus x-default')

    def test_every_section_is_a_real_heading(self):
        """Not styled <span>s — v1.10.20's lesson for the product pages."""
        body = self._get('/stadium-lighting/')
        headings = [_text(t) for _lvl, t in H_TAG_RE.findall(body)]
        self.assertEqual(
            len([h for h in headings if h]), len(headings),
            'an empty heading slipped in')
        self.assertGreaterEqual(
            len(headings), 5,
            'expected an H1 plus at least four sections, found %r' % headings)
        self.assertIn('LED Stadium Lighting', headings)

    def test_no_template_comment_reaches_the_output(self):
        """``{# #}`` is single-line in Django; a multi-line one renders.

        Two such comments leaked into the product pages during v1.10.20 and
        v1.10.22 and shipped as visible body copy before this page was written.
        """
        for path in ('/stadium-lighting/', '/products/',
                     '/products/m-series/', '/products/fl6m/'):
            with self.subTest(path=path):
                body = self._get(path)
                self.assertNotIn('{#', body,
                                 '%s renders a template comment' % path)
                self.assertNotIn('#}', body,
                                 '%s renders a template comment' % path)

    def test_every_image_carries_an_alt(self):
        body = self._get('/stadium-lighting/')
        tags = [t for t in IMG_TAG_RE.findall(body) if ' src=' in t]
        self.assertTrue(tags, 'no images rendered at all')
        missing = [t for t in tags if 'alt=' not in t]
        self.assertEqual(missing, [], 'img without alt: %r' % missing)

    def test_it_links_out_to_products_and_projects(self):
        """A landing page that links nowhere is a dead end for a crawler."""
        body = self._get('/stadium-lighting/')
        hrefs = set(HREF_RE.findall(body))
        self.assertGreaterEqual(
            len([h for h in hrefs if h.startswith('/products/')]), 3,
            'the page names fixtures but does not link to them')
        self.assertGreaterEqual(
            len([h for h in hrefs if h.startswith('/projects/')]), 5,
            'the page shows venue projects but does not link to them')

    def test_it_appears_in_the_sitemap_with_images(self):
        body = self._get('/sitemap.xml')
        blocks = re.findall(r'<url>(.*?)</url>', body, re.S)
        target = [b for b in blocks
                  if '/stadium-lighting' in re.search(r'<loc>(.*?)</loc>',
                                                      b).group(1)]
        self.assertEqual(
            len(target), 1,
            'the stadium page must appear exactly once in the sitemap')
        self.assertIn(
            '<image:image>', target[0],
            'the page renders a dozen images; the sitemap lists none')


class StadiumContentSourcingTests(TestCase):
    """The page must list what it claims to list."""

    def test_the_featured_products_are_the_two_vsp_models(self):
        """The page features exactly the two broadcast models, not a generic list.

        Iron law 4b: the expected roster is written out literally as a product
        decision; the view's ``FEATURED_PRODUCT_SLUGS`` constant is checked
        against it so a change to either side fails loudly. The original
        "first N of the category" read as a VSP-series list rather than the two
        specific luminaires the page exists to present.
        """
        EXPECTED_SLUGS = ('vsp-xxxxw-9m-yp', 'vsp-xxxxw-12m-yp')
        self.assertEqual(
            FEATURED_PRODUCT_SLUGS, EXPECTED_SLUGS,
            'the featured roster changed without a product decision')
        body = Client().get('/stadium-lighting/',
                            HTTP_HOST='localhost').content.decode()
        for slug in EXPECTED_SLUGS:
            with self.subTest(slug=slug):
                self.assertIn(
                    reverse('product_detail', args=[slug]), body,
                    '%s must be featured on the stadium page' % slug)

    def test_the_featured_grid_uses_two_columns_on_desktop(self):
        """Exactly two featured products → desktop grid must stay at two columns.

        The global .products-grid switches to three columns at >=1200px; with
        only two stadium products that leaves a blank right-hand third. This
        guard checks both the template markup and the CSS override so the layout
        cannot accidentally revert to three columns on PC browsers.
        """
        template_path = settings.BASE_DIR / 'templates' / 'stadium_lighting.html'
        template_src = template_path.read_text(encoding='utf-8')
        self.assertIn(
            'class="products-grid stadium-products-grid"',
            template_src,
            'stadium template must tag the grid for a two-column override')

        css_path = settings.BASE_DIR / 'static' / 'css' / 'base.css'
        css = css_path.read_text(encoding='utf-8')
        # Strip comments so the assertion cannot be satisfied by a comment.
        css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        self.assertIn(
            '.stadium-products-grid { grid-template-columns: repeat(2, 1fr); }',
            css_no_comments,
            'base.css must override the desktop grid to two columns')

        body = Client().get('/stadium-lighting/',
                            HTTP_HOST='localhost').content.decode()
        self.assertIn(
            'stadium-products-grid',
            body,
            'rendered stadium page must carry the two-column grid class')

    def test_the_intro_copy_fills_the_available_width(self):
        """The hero area has a blank right-hand third because the intro copy is
        capped at 860px. Remove the cap so the text fills the container on PC
        browsers.

        Guard checks the template and the CSS so the cap cannot be re-added by an
        inline style or by the global .section-body max-width.
        """
        template_path = settings.BASE_DIR / 'templates' / 'stadium_lighting.html'
        template_src = template_path.read_text(encoding='utf-8')
        intro = re.search(
            r'<div class="stadium-intro"[^>]*>(.*?)</div>.*?<h2',
            template_src, re.S)
        self.assertIsNotNone(intro, 'stadium intro div not found in template')
        self.assertNotIn(
            'max-width', intro.group(1),
            'stadium intro must not inline a max-width cap')

        lead = re.search(
            r'<p class="section-body stadium-section-lead"[^>]*>',
            template_src)
        self.assertIsNotNone(lead, 'stadium section lead not found in template')
        self.assertNotIn(
            'max-width', lead.group(0),
            'stadium section lead must not inline a max-width cap')

        css_path = settings.BASE_DIR / 'static' / 'css' / 'base.css'
        css = css_path.read_text(encoding='utf-8')
        css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        self.assertIn(
            '.stadium-intro,\n  .stadium-intro .section-body,\n  '
            '.stadium-section-lead { max-width: none; }',
            css_no_comments,
            'base.css must remove the max-width cap on stadium intro copy')

        body = Client().get('/stadium-lighting/',
                            HTTP_HOST='localhost').content.decode()
        self.assertIn('stadium-intro', body)
        self.assertIn('stadium-section-lead', body)

    def test_the_featured_product_images_are_capped_on_desktop(self):
        """The two product cards are oversized for a two-column grid, pushing
        the table and venue projects below the fold. The stadium override must
        cap the image container height and use a flatter aspect ratio on
        desktop breakpoints.
        """
        css_path = settings.BASE_DIR / 'static' / 'css' / 'base.css'
        css = css_path.read_text(encoding='utf-8')
        css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        self.assertIn(
            '.stadium-products-grid .product-card-img',
            css_no_comments,
            'base.css must scope the stadium image override')
        self.assertIn(
            'aspect-ratio: 2 / 1;',
            css_no_comments,
            'stadium product images must use a 2:1 aspect ratio')
        self.assertIn(
            'max-height: 220px;',
            css_no_comments,
            'stadium product images must be height-capped on tablet')
        self.assertIn(
            'max-height: 240px;',
            css_no_comments,
            'stadium product images must be height-capped on desktop')

    def test_the_featured_vsp_copy_omits_box_dimensions(self):
        """Iron law: enclosure sizes vary per project, so they must never be
        hard-coded. The VSP series is described only as a remote LED driver
        enclosure for easy operation and maintenance.

        Pinned literally (iron law 4b): the copy must contain the remote-enclosure
        phrase and must NOT contain dimension tokens (mm / stainless steel / a
        W×H×D triple). The expected strings are written out, not derived from the
        implementation, so a future edit that re-adds dimensions fails loudly.
        """
        REMOTE_PHRASE = 'remote LED driver enclosure'
        DIM_RE = re.compile(r'\d+\s*[×xX]\s*\d+')
        products = {p.slug: p for p in get_products('en')}
        for slug in FEATURED_PRODUCT_SLUGS:
            with self.subTest(slug=slug):
                product = products.get(slug)
                self.assertIsNotNone(product, '%s missing from seed' % slug)
                desc = product.description
                self.assertIn(
                    REMOTE_PHRASE, desc,
                    '%s must describe the remote LED driver enclosure' % slug)
                self.assertNotIn(
                    'mm', desc,
                    '%s must not hard-code millimetre dimensions' % slug)
                self.assertNotIn(
                    'stainless steel', desc,
                    '%s must not hard-code enclosure material/size' % slug)
                self.assertFalse(
                    DIM_RE.search(desc),
                    '%s must not hard-code W×H×D dimensions' % slug)
                self.assertNotIn(
                    'box', desc.lower(),
                    '%s must not use the unprofessional word "box" — '
                    'use "enclosure" / "LED driver enclosure"' % slug)

    def test_no_box_word_anywhere_in_seed_copy(self):
        """Iron-law lock for the global "no box" copy policy.

        The user ruled that "box" is unprofessional and must read "enclosure"
        / "LED driver enclosure" everywhere. A future editor who writes
        "driver boxes" or "AC box" must fail here, not ship it.
        """
        seeds = _load_seed()
        offenders = []
        for kind in ('products', 'projects'):
            for item in seeds.get(kind, []):
                text = ' '.join(str(item.get(f, '') or '')
                               for f in ('description', 'name', 'seo_keyword'))
                if re.search(r'[Bb]ox', text):
                    offenders.append((kind, item.get('slug'), text))
        self.assertEqual(
            offenders, [],
            'copy still contains "box": %r' % offenders)

    def test_the_venue_list_matches_the_sport_mapping(self):
        """Same table the product pages use for "Application Cases".

        Written against the constant on purpose here: the assertion is not
        "the page and the table agree" but "the page shows only venues from the
        stadium sport set, and shows at least one" — which holds whichever way
        the table is later corrected, and fails loudly if the page starts
        listing airports on a stadium page.
        """
        sports = PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(STADIUM_CATEGORY, [])
        self.assertTrue(sports, 'the stadium category maps to no sports')
        expected = [p for p in get_projects('en')
                    if getattr(p, 'sport_type', '') in sports
                    and getattr(p, 'image_url', '')]
        self.assertGreaterEqual(
            len(expected), VENUE_PROJECT_LIMIT,
            'only %d venues carry an image; the page promises %d'
            % (len(expected), VENUE_PROJECT_LIMIT))
        body = Client().get('/stadium-lighting/',
                            HTTP_HOST='localhost').content.decode()
        for project in expected[:VENUE_PROJECT_LIMIT]:
            with self.subTest(slug=project.slug):
                self.assertIn(reverse('project_detail', args=[project.slug]),
                              body)

    def test_no_roadway_or_airport_project_leaks_onto_the_page(self):
        """The failure mode of a category page is drifting into the neighbours."""
        sports = set(PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(STADIUM_CATEGORY, []))
        seeds = _load_seed()
        for project in seeds.get('projects', []):
            if getattr(project, 'sport_type', '') in sports:
                continue
            if project.get('sport_type') in ('CITY_EXPRESSWAY', 'AIRPORT'):
                with self.subTest(slug=project['slug']):
                    self.assertNotIn(
                        reverse('project_detail', args=[project['slug']]),
                        Client().get('/stadium-lighting/', HTTP_HOST='localhost')
                        .content.decode())

    def test_the_mapping_is_inverse_consistent(self):
        """Iron law for ``related_links``: every sport maps both ways."""
        for sport, categories in PROJECT_SPORT_TO_PRODUCT_CATEGORIES.items():
            if STADIUM_CATEGORY not in categories:
                continue
            with self.subTest(sport=sport):
                self.assertIn(
                    sport,
                    PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(STADIUM_CATEGORY, []),
                    '%s claims the stadium category but the reverse map omits it'
                    % sport)

    def test_the_category_is_actually_a_stadium_term(self):
        """Cross-check: the one landing page's keyword must say "stadium"."""
        keyword = CATEGORY_KEYWORD.get(STADIUM_CATEGORY, '')
        self.assertTrue(keyword, 'the category has no SEO keyword')
        self.assertIn('Stadium', keyword)

    def test_the_limits_are_product_decisions(self):
        """Pinned so raising them is a deliberate act."""
        self.assertEqual(VENUE_PROJECT_LIMIT, 9)
        self.assertEqual(
            FEATURED_PRODUCT_SLUGS, ('vsp-xxxxw-9m-yp', 'vsp-xxxxw-12m-yp'))


class RejectedCategoryTests(TestCase):
    """🔴 The rejection is the valuable part of this batch.

    Four of the six proposed category pages were measured and refused. Without
    a guard, the next person to read the original plan will build them — the
    plan is still in ``docs/``.
    """

    def test_no_category_page_exists_beyond_the_one_that_earned_it(self):
        """Scan urlpatterns for a landing page per category.

        Only ``stadium_lighting`` is expected. A future ``highbay_lighting`` or
        ``roadway_lighting`` route fails here until the corresponding entry is
        removed from ``REJECTED_CATEGORIES`` with a fresh measurement.
        """
        from pages import urls as url_module

        names = {p.name for p in url_module.urlpatterns if p.name}
        # ``stadium_lighting`` is the one that earned its page; anything else
        # ending in _lighting is an unmeasured category page.
        landing = {n for n in names if n.endswith('_lighting')} - {
            'stadium_lighting'}
        self.assertEqual(
            landing, set(),
            'unexpected lighting landing page(s): %r — each needs a '
            'measurement, not just a route' % sorted(landing))
        self.assertIn('stadium_lighting', names)

    def test_the_rejected_list_matches_the_measured_portfolio(self):
        """If the seed gains products, a rejected category may deserve a page."""
        seeds = _load_seed()
        counts = {}
        for product in seeds.get('products', []):
            counts[product.get('category')] = counts.get(
                product.get('category'), 0) + 1
        for category, reason in sorted(REJECTED_CATEGORIES.items()):
            with self.subTest(category=category):
                self.assertLessEqual(
                    counts.get(category, 0), 5,
                    '%s now holds %d products — the measurement behind its '
                    'rejection (%s) is stale, re-argue it'
                    % (category, counts.get(category, 0), reason))

    def test_only_one_category_has_a_landing_page_by_decision(self):
        self.assertEqual(
            CATEGORIES_WITH_LANDING_PAGES, frozenset({STADIUM_CATEGORY}))


class HubInternalLinkTests(TestCase):
    """P4-B — the hub pages must list their sub-models in the content area.

    🔴 The premise of this batch was wrong and the correction matters. A first
    scan reported that ``/products/m-series/`` linked to none of its six
    modules — but that scan stripped ``<nav>`` elements, and the series
    navigation *is* a ``<nav>``, so the filter sidebar's links were removed
    before counting. The sidebar has linked to every sub-model all along.

    The selector is still worth having, for two reasons a sidebar does not
    cover: it sits in the content area rather than behind a filter control, and
    each row carries the wattage and the keyword phrase, so the hub page picks
    up the per-module search terms. But "the hub is a dead end" was never true
    and must not be repeated.

    The assertions below therefore match the selector's **own markup**
    (``class="series-child"``). An earlier version asserted a bare
    ``assertIn(child_url, body)``, which the sidebar satisfied on its own — the
    mutation probe caught it by passing with the selector removed entirely.
    """

    #: hub slug -> the children it is supposed to list. Literal, so adding a
    #: module to a series without listing it fails here.
    HUB_CHILDREN = {
        'm-series': ('fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m'),
        'rgb-rgbw': ('rt410-rgbw', 'fl9m-rgbw'),
        'accessory': ('mseries-gs', 'glare-shield-for-rt410'),
    }

    #: The selector's own anchor class. Named here so the guard and the probe
    #: cannot drift onto a different element.
    SELECTOR_CLASS = 'series-child'

    @classmethod
    def setUpTestData(cls):
        cls.by_parent = {}
        for product in _load_seed().get('products', []):
            parent = product.get('parent_slug') or ''
            if parent:
                cls.by_parent.setdefault(parent, []).append(product['slug'])

    def _selector_links(self, hub):
        """Only the links rendered by the selector, ignoring the sidebar."""
        body = Client().get('/products/%s/' % hub,
                            HTTP_HOST='localhost').content.decode()
        return re.findall(
            r'<a href="(/products/[^"]+)" class="%s"' % self.SELECTOR_CLASS,
            body)

    def test_each_hub_has_children_in_the_seed(self):
        """Anti-vacuity: the fixture above must match reality."""
        for hub, children in sorted(self.HUB_CHILDREN.items()):
            with self.subTest(hub=hub):
                actual = set(self.by_parent.get(hub, []))
                self.assertTrue(
                    actual, 'no product declares %r as its parent — the '
                            'fixture in this test is stale' % hub)
                self.assertEqual(
                    set(children) - actual, set(),
                    'these fixtures are not children of %s: %r'
                    % (hub, sorted(set(children) - actual)))

    def test_every_hub_lists_every_child_in_the_selector(self):
        for hub, children in sorted(self.HUB_CHILDREN.items()):
            listed = self._selector_links(hub)
            with self.subTest(hub=hub):
                self.assertEqual(
                    sorted(listed),
                    sorted(reverse('product_detail', args=[c])
                           for c in children),
                    '%s does not list its children in the selector' % hub)

    def test_a_leaf_product_has_no_selector(self):
        """The guard must be able to see the selector *disappear*."""
        self.assertEqual(
            self._selector_links('fl6m'), [],
            'a leaf product rendered a sub-model selector')
        self.assertEqual(
            self._selector_links('rt590fl-s'), [],
            'a leaf product rendered a sub-model selector')

    def test_the_selector_carries_the_wattage_and_the_keyword(self):
        """The reason the selector exists beyond the links.

        The sidebar shows a model name; the selector also shows the wattage and
        the phrase the child page bids on. Without those it would be a
        duplicate of the navigation.
        """
        body = Client().get('/products/m-series/',
                            HTTP_HOST='localhost').content.decode()
        block = re.search(
            r'<div class="detail-series-children">(.*?)</div>\s*</div>',
            body, re.S)
        self.assertIsNotNone(block, 'the selector block is missing entirely')
        markup = block.group(1)
        self.assertEqual(
            len(re.findall(r'class="series-child-power"', markup)), 6,
            'every child row must show its wattage')
        self.assertIn(
            'Modular LED Flood Light', markup,
            'the selector must carry the per-module search phrase')