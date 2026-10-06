"""
B3 — per-page SEO keyword guards (L1 unit tests).

Covers the B3 batch from docs/seo-growth-plan.md:
  * Category keyword map (CATEGORY_KEYWORD) covers every product category.
  * Every product <title> (English) contains its category keyword + brand signature.
  * Every product meta description (English) is unique and 50–160 chars.
  * seo_title / seo_description fall back to the formula (English) or the
    translated description (non-English) and never silently regress.
  * The product detail template actually renders the per-page seo_title_t /
    seo_description_t (end-to-end wiring check).

Pure SEO helpers live in pages.utils (no Django import); the seed shims
(_DictProduct / _DictProject) mirror the model methods so the production
(seed) path and the DB path emit identical titles/descriptions.
"""
import re

from django.test import Client, TestCase

from pages.models import Product
from pages.utils import (
    CATEGORY_KEYWORD,
    CATEGORY_KEYWORD_I18N,
    SLUG_KEYWORD_OVERRIDE,
    build_seo_description,
    build_seo_title,
    fit_description,
    get_seo_override,
    translate,
)
from pages.views.utils import _DictProduct, _DictProject, _load_seed


class _FakeObj:
    """Minimal stand-in so the seo model methods can be unit-tested without DB."""

    def __init__(self, **kw):
        self.slug = kw.get('slug', '')
        self.name = kw.get('name', '')
        self.category = kw.get('category', '')
        self.model_number = kw.get('model_number', '')
        self.power = kw.get('power', '')
        self.title = kw.get('title', '')
        self.translations = kw.get('translations', {}) or {}

    def t(self, field, lang='en'):
        return translate(self, field, lang)

    def seo_title(self, lang='en'):
        explicit = get_seo_override(self, 'seo_title', lang)
        if explicit:
            return explicit
        return build_seo_title(self, lang)

    def seo_description(self, lang='en'):
        explicit = get_seo_override(self, 'seo_description', lang)
        if explicit:
            return explicit
        if lang == 'en':
            return build_seo_description(self, lang)
        return fit_description(self.t('description', lang))


class CategoryKeywordMappingTests(TestCase):
    def test_category_keyword_covers_all_seed_categories(self):
        seed = _load_seed()
        cats = {p.get('category', '') for p in seed['products']}
        for c in cats:
            self.assertIn(c, CATEGORY_KEYWORD, f'category {c!r} missing from CATEGORY_KEYWORD')
        for k, v in CATEGORY_KEYWORD.items():
            self.assertTrue(v and isinstance(v, str), f'CATEGORY_KEYWORD[{k}] empty')

    def test_slug_override_keys_are_valid_slugs(self):
        seed = _load_seed()
        slugs = {p.get('slug', '') for p in seed['products']}
        for s in SLUG_KEYWORD_OVERRIDE:
            self.assertIn(s, slugs, f'SLUG_KEYWORD_OVERRIDE key {s!r} is not a real slug')


class ProductSeoTitleKeywordTests(TestCase):
    def test_all_product_titles_contain_category_keyword(self):
        """Every title carries a keyword — the slug one if there is one.

        🔴 v1.10.20 (P2-A) — this used to assert the *category* phrase is
        always present, which made a per-slug override impossible by
        construction: eleven products share ``AREA_SITE``, so the M Series
        modules (which the repository's own copy calls floodlights) were all
        opening with ``LED Area & Site Lighting`` and bidding against each
        other. The contract is now "a keyword is present", not "this specific
        keyword is present" — the phrase a page leads with is a per-slug copy
        decision recorded in ``SLUG_KEYWORD_OVERRIDE``.
        """
        seed = _load_seed()
        for item in seed['products']:
            p = _DictProduct(item)
            title = p.seo_title('en')
            override = SLUG_KEYWORD_OVERRIDE.get(p.slug, '')
            category_kw = CATEGORY_KEYWORD.get(p.category, '')
            expected = override or category_kw
            self.assertTrue(
                expected,
                f'{p.slug}: category {p.category!r} has neither a slug '
                f'override nor a category keyword')
            self.assertIn(
                expected, title,
                f'{p.slug} title missing its keyword {expected!r}: {title!r}')
            self.assertIn('| SolarOne', title)

    def test_title_formula_appends_power_only_when_absent_from_identifier(self):
        # model_number embeds wattage -> power must NOT be appended again
        p = _DictProduct({
            'slug': 'fl6m', 'name': 'FL6M', 'category': 'AREA_SITE',
            'model_number': 'FL6M-480W-30K-S', 'power': '480W',
        })
        title = p.seo_title('en')
        self.assertIn('FL6M-480W-30K-S', title)
        self.assertNotIn('— 480W', title)
        # a product whose identifier lacks power gets it appended
        p2 = _DictProduct({
            'slug': 'ms', 'name': 'M Series', 'category': 'AREA_SITE',
            'model_number': '', 'power': '80~1280W+',
        })
        self.assertIn('— 80~1280W+', p2.seo_title('en'))


class ProductSeoTitleLocalizedTests(TestCase):
    """P2-B: the non-English keyword comes from ``CATEGORY_KEYWORD_I18N``.

    🔴 v1.10.20 — this used to assert the keyword is read from the product's
    ``translations[lang]['category']``. That is the chain that put the raw enum
    ``AREA_SITE`` into 100 non-English titles: ``translate()`` falls back to the
    English value when a translation is missing, and the English value of
    ``category`` is the stored enum. The wording now comes from
    ``CATEGORY_KEYWORD_I18N`` — the same label the site already shows in the
    sidebar and on the cards, in every locale.
    """

    def test_non_english_title_uses_the_category_i18n_map(self):
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            for category, phrases in CATEGORY_KEYWORD_I18N.items():
                with self.subTest(lang=lang, category=category):
                    p = _DictProduct({
                        'slug': 'a', 'name': 'Alpha', 'category': category,
                        'model_number': 'A-1',
                    })
                    self.assertIn(phrases[lang], p.seo_title(lang))

    def test_i18n_map_covers_every_category_in_use(self):
        """A category missing from the map would silently fall back to English.

        Asserted rather than assumed: the fallback is *safe* (English beats an
        enum) but it is still a regression of the localisation this batch
        exists to deliver, so it has to be loud.
        """
        used = {p.get('category', '') for p in _load_seed()['products']}
        missing = sorted(used - set(CATEGORY_KEYWORD_I18N))
        self.assertEqual(
            missing, [],
            'categories with no localised SEO keyword — their non-English '
            'titles will fall back to the English phrase: %r' % (missing,))

    def test_i18n_map_matches_the_sidebar_wording(self):
        """The title, the sidebar and the cards must say the same thing.

        The map reuses the site's existing category labels rather than new
        copy. That is only a virtue while it stays true, and a reviewer who
        later swaps in proper search phrases should update this deliberately.
        """
        from pages.views.i18n import _SIDEBAR_I18N

        expected = {
            'AREA_SITE': 'Area and Site',
            'SPORTS_LIGHTING': 'Sports Lighting System',
            'FLOODLIGHT': 'Flood Lighting',
            'HIGHBAY_LOWBAY': 'Highbay & Low Bay',
            'ROADWAY': 'Roadway',
            'ACCESSORY': 'Accessory',
        }
        for category, label in expected.items():
            sidebar = _SIDEBAR_I18N[label]
            for lang in ('fr', 'es', 'de', 'ru', 'ar'):
                with self.subTest(category=category, lang=lang):
                    self.assertEqual(
                        CATEGORY_KEYWORD_I18N[category][lang], sidebar[lang],
                        'CATEGORY_KEYWORD_I18N and the sidebar label have '
                        'drifted apart for %s/%s' % (category, lang))

    def test_no_locale_ever_emits_the_stored_enum(self):
        """The regression this batch exists to prevent, asserted end to end.

        Checked against the real seed data rather than a synthetic product, so
        a category that is only used by one page cannot slip through.
        """
        enums = {c for c, _ in Product.CATEGORY_CHOICES}
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            for lang in ('fr', 'es', 'de', 'ru', 'ar'):
                with self.subTest(slug=p.slug, lang=lang):
                    title = p.seo_title(lang)
                    for enum in enums:
                        self.assertNotIn(
                            enum, title,
                            '%s/%s title leaks the stored enum %r: %r'
                            % (p.slug, lang, enum, title))


class MetaDescriptionUniquenessTests(TestCase):
    def test_all_product_descriptions_unique_and_length(self):
        seed = _load_seed()
        descs = [_DictProduct(item).seo_description('en')
                 for item in seed['products']]
        self.assertEqual(len(descs), len(set(descs)), 'product descriptions not unique')
        for d in descs:
            self.assertTrue(50 <= len(d) <= 160,
                            f'desc length out of range: {len(d)} -> {d!r}')

    def test_description_embeds_identifier_for_uniqueness(self):
        p = _DictProduct({
            'slug': 'x', 'name': 'UniqueX', 'category': 'AREA_SITE',
            'model_number': 'UX-1', 'power': '',
        })
        # identifier = model_number (preferred over name) -> guarantees uniqueness
        self.assertIn('UX-1', p.seo_description('en'))


class SeoFieldFallbackTests(TestCase):
    def test_no_explicit_seo_uses_formula_en(self):
        p = _FakeObj(slug='a', name='Alpha', category='FLOODLIGHT',
                     model_number='A-1', power='100W')
        self.assertEqual(p.seo_title('en'), build_seo_title(p, 'en'))
        self.assertEqual(p.seo_description('en'), build_seo_description(p, 'en'))
        self.assertTrue(p.seo_title('en'))
        self.assertTrue(p.seo_description('en'))

    def test_explicit_seo_title_override_wins(self):
        p = _FakeObj(slug='a', name='Alpha', category='FLOODLIGHT', model_number='A-1',
                     translations={'en': {'seo_title': 'Custom Title | SolarOne'}})
        self.assertEqual(p.seo_title('en'), 'Custom Title | SolarOne')

    def test_non_english_description_falls_back_to_translation_not_formula(self):
        p = _FakeObj(slug='a', name='Alpha', category='FLOODLIGHT', model_number='A-1',
                     translations={'fr': {'description': 'Lumière LED française'}})
        self.assertNotEqual(p.seo_description('fr'), build_seo_description(p, 'en'))
        self.assertEqual(p.seo_description('fr'), 'Lumière LED française')


class CategoryKeywordSearchDemandTests(TestCase):
    """SPORTS_LIGHTING 的品类词必须按**实测搜索习惯**措辞，不是内部 taxonomy 直译。

    旧值 ``LED Sports Stadium Lighting`` 来自模型 choices 的 'Sports Lighting
    System' 直译，两个高频词都吃不到：SEMrush US（2026-09-29）显示需求落在
    ``stadium lights`` 2,900/mo 与 ``led stadium lights`` 1,000/mo 且 KD 6
    （本站体积/难度性价比最好的机会）。故重切为 ``LED Stadium Light``。

    2026-09-30 二次收敛（方案 A）：**复数头部词归 /products/sports-lighting/
    hub 独占**（一词一页），产品详情 title 走单数词族 ``LED Stadium Light``，
    避免两个页面抢同一查询；描述侧保留 ``stadium light`` 自然提及继续强化
    相关性。这两个用例锁住"按搜索需求而非内部分类名措辞"的决策，防止有人照着
    ``Product.CATEGORY_CHOICES`` 把它改回内部叫法。
    """

    def test_sports_lighting_phrase_uses_the_wording_buyers_search(self):
        kw = CATEGORY_KEYWORD['SPORTS_LIGHTING']
        self.assertIn('Stadium Light', kw,
                      f'SPORTS_LIGHTING keyword lost the searched phrase: {kw!r}')
        self.assertNotEqual(kw, 'LED Sports Stadium Lighting',
                            'internal-taxonomy phrasing came back')

    def test_seed_sports_products_lead_with_stadium_lights(self):
        seed = _load_seed()
        sports = [i for i in seed['products']
                  if i.get('category') == 'SPORTS_LIGHTING']
        self.assertTrue(sports, 'seed has no SPORTS_LIGHTING product to guard')
        for item in sports:
            p = _DictProduct(item)
            title = p.seo_title('en')
            self.assertTrue(
                title.startswith('LED Stadium Light'),
                f"{p.slug} title must lead with the searched phrase: {title!r}")
            # Case-insensitive: body copy naturally reads "stadium light pole".
            self.assertIn('stadium light', p.seo_description('en').lower(), p.slug)


class SeoTitleLengthTests(TestCase):
    """Title 长度守卫：Google SERP 约在 60 字符处截断，超出即白写。"""

    #: 当前最长 58（Glare Shield for RT410 / FL9M-720W-XXK-S — 630W）。
    MAX_TITLE_LEN = 60

    def test_all_product_titles_fit_serp_display(self):
        seed = _load_seed()
        for item in seed['products']:
            title = _DictProduct(item).seo_title('en')
            self.assertLessEqual(
                len(title), self.MAX_TITLE_LEN,
                f"{item.get('slug')}: title would be truncated in SERP "
                f'({len(title)} chars) -> {title!r}')


class SeoTemplateRenderTests(TestCase):
    """End-to-end: the product detail template renders per-page seo_title_t."""

    def test_product_detail_renders_seo_title_and_description(self):
        seed = _load_seed()
        slug = seed['products'][0]['slug']
        prod = next(p for p in seed['products'] if p['slug'] == slug)
        kw = CATEGORY_KEYWORD.get(prod['category'], '')
        client = Client()
        resp = client.get(f'/products/{slug}/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        m = re.search(r'<title>(.*?)</title>', html, re.S)
        self.assertIsNotNone(m, 'no <title> rendered')
        title = m.group(1)
        self.assertIn(kw, title, f'title missing category keyword: {title!r}')
        self.assertIn('| SolarOne', title)
        dm = re.search(r'name="description" content="(.*?)"', html)
        self.assertIsNotNone(dm, 'no meta description rendered')
        self.assertTrue(len(dm.group(1)) >= 20, 'meta description too short')
