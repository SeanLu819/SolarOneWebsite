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

from pages.utils import (
    CATEGORY_KEYWORD,
    SLUG_KEYWORD_OVERRIDE,
    build_seo_description,
    build_seo_title,
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
        return self.t('description', lang)


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
        seed = _load_seed()
        for item in seed['products']:
            p = _DictProduct(item)
            title = p.seo_title('en')
            kw = CATEGORY_KEYWORD.get(p.category, '')
            self.assertTrue(kw, f'{p.slug} category {p.category!r} has no keyword')
            self.assertIn(kw, title, f'{p.slug} title missing category keyword: {title!r}')
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
    def test_non_english_title_uses_localized_keyword(self):
        p = _DictProduct({
            'slug': 'a', 'name': 'Alpha', 'category': 'FLOODLIGHT',
            'model_number': 'A-1', 'translations': {'fr': {'category': 'Projecteurs LED'}},
        })
        self.assertIn('Projecteurs LED', p.seo_title('fr'))


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
    （本站体积/难度性价比最好的机会）。故重切为 ``LED Stadium Lights``。

    这两个用例锁住"按搜索需求而非内部分类名措辞"的决策，防止有人照着
    ``Product.CATEGORY_CHOICES`` 把它改回内部叫法。
    """

    def test_sports_lighting_phrase_uses_the_wording_buyers_search(self):
        kw = CATEGORY_KEYWORD['SPORTS_LIGHTING']
        self.assertIn('Stadium Lights', kw,
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
                title.startswith('LED Stadium Lights'),
                f"{p.slug} title must lead with the searched phrase: {title!r}")
            self.assertIn('Stadium Lights', p.seo_description('en'), p.slug)


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
