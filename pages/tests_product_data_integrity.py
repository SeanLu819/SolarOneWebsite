"""产品数据完整性守卫 —— 长尾 SEO P0 批次 (v1.10.19)

背景（2026-10-06 审计实测，非推断）
------------------------------------
一次针对 24 个产品页 × 6 语种 = 144 个 URL 的长尾关键词审计挖出四个
数据缺陷。它们**互不相同根因**，但都在同一个位置炸：SEO 公式
（``pages/utils.py`` 的 ``build_seo_title`` / ``build_seo_description``）
直接消费 ``model_number`` / ``power`` / ``category`` 三个字段。

P0-A  **页面上肉眼可见的枚举常量**
    ``product_detail.html:72`` / ``product_overview.html:76`` 渲染
    ``<span class="series-hero-label">{{ banner_label }}</span>``，
    而 ``views_products.py:333`` 把它设为 ``product.category_t`` ——
    那是 ``Product.category`` 的**枚举值**（``AREA_SITE`` /
    ``FLOODLIGHT`` / …），不是文案。线上实测 ``/fr|de|ar/products/fl6m/``
    的 hero 标签都是 ``AREA_SITE``。这不是 SEO 问题而是**转化问题**：
    访客在产品页左上角看到数据库枚举码。现已改用
    ``product.category_display``（``enrich.py`` 里已走 ``_t()`` 的 6 语种
    译法）。

P0-B  **``rt220ub`` 的型号是别人的**
    ``rt220ub.model_number == 'FL1M-80W'`` —— 那是 ``fl1m`` 的型号，
    而且是 ``models.py`` 里 ``default="FL1M-80W"`` 静默填进去的
    （新建产品继承默认值的经典污染）。同一产品的
    ``energy_data[0]`` 写着 ``RT220UB``、``ordering_info[1]`` 写着
    ``40W``，三处自相矛盾。线上标题实测
    ``LED Flood Lights FL1M-80W | SolarOne`` ⇒ 与 ``/products/fl1m/``
    争同一个型号词。

P0-C  **功率字段互相矛盾 / 缺失**
    ``fl9m.power == '630W'`` 而 ``specs`` / ``energy_data`` /
    ``ordering_info`` / ``model_number`` 四处都是 ``720W`` ⇒ 标题与
    规格卡显示两个数。另有 13 个产品 ``power`` 为空，导致
    ``build_seo_title`` 的 ``if power and power not in core`` 分支
    整段跳过，标题里一个瓦数都不出现。

P0-E  **光束角图挂在错误的目录**
    ``beamangle-120d-1.webp`` 画的是 120° 配光。``rt420fs-s`` 卖
    ``120=120°``，``rt220ub`` 只卖 ``100=100°`` —— 文件却在
    ``rt220ub/`` 目录下，且 ``rt420fs-s`` 跨 slug 引用它。

本守卫锁死的不变量
----------------
1. 可见 hero 标签**不得**是 ``Product.CATEGORY_CHOICES`` 的裸枚举值，
   且六语种都必须给出非空译文。
2. ``model_number`` 非空时，其型号前缀必须与产品名/slug 同源
   （防止再次出现"借别人型号"）。三条豁免写死并注明理由。
3. 同一产品的瓦数在 ``power`` / ``specs[Power]`` /
   ``energy_data[System Wattage]`` / ``ordering_info[1]`` /
   ``model_number`` 五个来源中**不得互相矛盾**。
4. ``beam_angle_image`` 指向的文件必须真实存在于磁盘，且与
   ``ordering_info`` 里声明的角度集合一致（不跨 slug 借用）。
5. 守卫断言的期望值全部是**独立的产品决策**（写死的常量 / 从
   ``_load_seed()`` 派生），不得从被测实现里反推（铁律 4b）。

DB 与 seed 双向核对：本守卫同时读 ``_load_seed()``（生产走的路径）
和 ``Product`` 模型（本地路径），两处不一致即失败 —— 这是发现
seed_sync 漂移的唯一手段。
"""
import os
import re

from django.conf import settings
from django.test import TestCase

from pages.models import Product
from pages.views.utils import _DictProduct, _load_seed

#: The six stored category values. Written out literally rather than read
#: from ``Product.CATEGORY_CHOICES`` (iron law 4b: an expectation derived
#: from the implementation moves with the implementation). If a category is
#: ever added, the literal set must be updated here on purpose.
CATEGORY_ENUM_VALUES = frozenset({
    'AREA_SITE', 'SPORTS_LIGHTING', 'FLOODLIGHT',
    'HIGHBAY_LOWBAY', 'ROADWAY', 'ACCESSORY', 'MODULAR', 'OTHER',
})

LANGS = ('en', 'fr', 'es', 'de', 'ru', 'ar')

#: Products whose ``model_number`` deliberately carries a platform code that
#: is not a literal substring of the display name. Each entry records why,
#: because "the guard was just wrong" and "the data is wrong" look identical
#: from the outside.
MODEL_NUMBER_PREFIX_EXEMPT = {
    # The line is sold as RT410FL on the sidebar ("RT410FL-S") while the
    # catalogue calls the series "RT410 Series"; RT410FL is the real name.
    'rt410-series': 'RT410FL is the product-line name (sidebar renders RT410FL-S)',
    # Suffix glued to the prefix with no separator: RT420FS + S100W.
    'rt420fs-s': 'model is RT420FS-S100W, glued suffix (no hyphen before 100W)',
}

#: Products with genuinely no wattage. All four are either accessories
#: (a glare shield draws no power) or a concept page (RGB / RGBW is a
#: technology, not a single luminaire), so there is nothing to backfill.
NO_WATTAGE_EXPECTED = {
    'accessory': 'accessory hub page, not a luminaire',
    'glare-shield-for-rt410': 'glare shield, draws no power',
    'mseries-gs': 'glare shield, draws no power',
    'rgb-rgbw': 'RGB/RGBW technology page, not a single fixture',
}


def _wattage(text):
    """First integer followed by W/w in ``text``, or ``''``."""
    m = re.search(r'(\d+)\s*[wW]', str(text or ''))
    return m.group(1) if m else ''


def _strip_images_prefix(path):
    """``images/products/<slug>/<file>`` -> ``<slug>/<file>``."""
    return str(path or '').replace('\\', '/').replace('images/products/', '')


class ProductDataIntegrityTests(TestCase):
    """Data-level invariants. Uses ``TestCase`` (DB access required)."""

    @classmethod
    def setUpTestData(cls):
        cls.seed = _load_seed()
        cls.seed_products = {p['slug']: p for p in cls.seed.get('products', [])}
        cls.db_products = {p.slug: p for p in Product.objects.all()}

    # ------------------------------------------------------------------
    # P0-A — no raw enum in the visible hero label
    # ------------------------------------------------------------------
    def test_banner_label_never_exposes_category_enum(self):
        """``views_products.py:333`` must not feed the raw enum to the page.

        Asserts on the *source* rather than the rendered HTML: the test DB
        is empty in this project's test runs, so a rendered assertion would
        pass vacuously (iron law: assert behaviour, but derive what you can
        from data that actually exists).
        """
        path = os.path.join(settings.BASE_DIR, 'pages', 'views', 'views_products.py')
        with open(path, 'rb') as fh:
            raw = fh.read()
        source = raw.decode('utf-8')
        self.assertIn(
            "context['banner_label'] = product.category_display",
            source,
            'views_products.py must set banner_label from category_display '
            '(the translated label), not from the raw category enum',
        )
        self.assertNotIn(
            "context['banner_label'] = product.category_t",
            source,
            'banner_label = product.category_t renders AREA_SITE / FLOODLIGHT '
            'to visitors (P0-A regression)',
        )

    def test_every_category_has_a_translated_display_label(self):
        """All six languages must produce a non-enum label per category.

        ``_PRODUCT_CAT_TO_SIDEBAR_LABEL`` -> ``_t()`` is the lookup chain
        ``enrich.py:150-151`` uses. If a language falls through to English
        that is acceptable (never empty); if it falls through to the *enum*
        the visitor sees ``AREA_SITE``.
        """
        from pages.views.enrich import _PRODUCT_CAT_TO_SIDEBAR_LABEL
        from pages.views.i18n import _t

        for cat in sorted(_PRODUCT_CAT_TO_SIDEBAR_LABEL):
            label = _PRODUCT_CAT_TO_SIDEBAR_LABEL[cat]
            for lang in LANGS:
                shown = _t(label, lang)
                self.assertTrue(shown, '%s / %s produced an empty label' % (cat, lang))
                self.assertNotIn(
                    shown, CATEGORY_ENUM_VALUES,
                    'category %s renders the raw enum in %s' % (cat, lang),
                )

    def test_rendered_hero_label_is_never_an_enum(self):
        """End-to-end: hit one detail page per language, read the label.

        Uses the real client so the template is exercised too. The local
        dev path falls back to the seed, which is populated, so this is not
        a vacuous pass.
        """
        from django.urls import reverse

        for lang in LANGS:
            with self.subTest(lang=lang):
                slug = 'fl6m' if lang == 'en' else slug_of(lang)
                with translation_override(lang):
                    url = reverse('product_detail', args=[slug])
                    response = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)
                body = response.content.decode('utf-8')
                labels = re.findall(
                    r'series-hero-label">(.*?)</span>', body, re.S)
                self.assertEqual(len(labels), 1,
                                 'expected exactly one hero label in %s' % url)
                for label in labels:
                    self.assertNotIn(
                        label.strip(), CATEGORY_ENUM_VALUES,
                        '%s shows the raw enum %r' % (url, label))


def slug_of(lang):
    """Same slug for every language — slugs are not translated."""
    return 'fl6m'


def translation_override(lang):
    from django.utils import translation as _t_module

    class _Ctx:
        def __enter__(self):
            self._prev = _t_module.activate(lang)

        def __exit__(self, *exc):
            _t_module.deactivate_all()
            _t_module.activate(self._prev)
            return False

    return _Ctx()


class ModelNumberIntegrityTests(TestCase):
    """P0-B — no product may advertise another product's model code."""

    @classmethod
    def setUpTestData(cls):
        cls.seed_products = {
            p['slug']: p for p in _load_seed().get('products', [])
        }

    def _both_paths(self, slug):
        """Yield ``(source_label, product_dict)`` for DB and seed paths.

        Both are needed: production renders the seed object
        (``_DictProduct``), local dev renders the model. A fix applied to
        only one of them is invisible until deploy.
        """
        item = self.seed_products.get(slug)
        if item is not None:
            yield 'seed', _DictProduct(item)
        row = Product.objects.filter(slug=slug).first()
        if row is not None:
            yield 'db', row

    def test_model_number_prefix_matches_product_identity(self):
        offenders = []
        for slug in sorted(self.seed_products):
            if slug in MODEL_NUMBER_PREFIX_EXEMPT:
                continue
            item = self.seed_products[slug]
            model_number = (item.get('model_number') or '').strip()
            if not model_number:
                continue
            # The alphabetic head of the code, e.g. "RT590FL" from
            # "RT590FL-160W", "FL9M" from "FL9M-720W-XXK-S".
            head = re.match(r'[A-Za-z]+', model_number)
            if not head:
                continue
            token = head.group(0).upper()
            name = re.sub(r'[^A-Za-z0-9]', '', item.get('name', '')).upper()
            alt = re.sub(r'[^A-Za-z0-9]', '', slug).upper()
            if token in name or token in alt:
                continue
            offenders.append((slug, item.get('name'), model_number))
        self.assertEqual(
            offenders, [],
            'model_number belongs to a different product (P0-B regression): %r'
            % (offenders,),
        )

    def test_model_numbers_are_unique_across_products(self):
        """Two pages sharing a model code compete for the same query."""
        from collections import Counter

        codes = Counter(
            (p.get('model_number') or '').strip()
            for p in self.seed_products.values()
            if (p.get('model_number') or '').strip()
        )
        dupes = {code: n for code, n in codes.items() if n > 1}
        self.assertEqual(
            dupes, {},
            'duplicate model_number across products — they will fight over '
            'the same keyword: %r' % (dupes,),
        )

    def test_no_model_number_equals_the_removed_field_default(self):
        """``models.py`` used to default ``model_number`` to ``FL1M-80W``.

        Any product still carrying that exact code is either the real fl1m
        (whose code is the longer ``FL1M-80W-30K-S``) or inherited the
        default. Guards against the default creeping back in.
        """
        for slug, item in sorted(self.seed_products.items()):
            code = (item.get('model_number') or '').strip()
            if code == 'FL1M-80W' and slug != 'fl1m':
                self.fail(
                    'product %r carries model_number "FL1M-80W", which is the '
                    'old models.py field default and belongs to fl1m' % slug,
                )

    def test_model_field_has_no_foreign_business_default(self):
        """The field itself must not seed a business code on new objects.

        A ``default=`` carrying a real model number silently stamps it onto
        every newly created product in the admin — the exact mechanism that
        produced ``rt220ub``'s wrong code.
        """
        from django.db import models as django_models

        field = Product._meta.get_field('model_number')
        self.assertTrue(field.empty_strings_allowed or field.blank)
        default = field.default
        self.assertTrue(
            default is django_models.NOT_PROVIDED or default == '',
            'Product.model_number.default is %r — a business code in a field '
            'default propagates to every new product' % (default,),
        )


class WattageConsistencyTests(TestCase):
    """P0-C — the wattage must not contradict itself across five sources."""

    @classmethod
    def setUpTestData(cls):
        cls.seed_products = {
            p['slug']: p for p in _load_seed().get('products', [])
        }

    def _sources(self, item):
        """Map every place a wattage can hide to its numeric string."""
        specs = item.get('specs') or []
        spec_w = ''
        if isinstance(specs, list):
            for row in specs:
                if isinstance(row, dict) and row.get('label') == 'Power':
                    spec_w = _wattage(row.get('value'))
                    break
        energy = item.get('energy_data') or []
        energy_w = ''
        if isinstance(energy, list):
            for row in energy:
                if isinstance(row, dict) and row.get('label') == 'System Wattage':
                    energy_w = _wattage(row.get('value'))
                    break
        ordering = item.get('ordering_info') or []
        ordering_w = _wattage(ordering[1]) if len(ordering) > 1 else ''
        return {
            'power': _wattage(item.get('power')),
            'specs[Power]': spec_w,
            'energy_data[System Wattage]': energy_w,
            'ordering_info[1]': ordering_w,
            'model_number': _wattage(item.get('model_number')),
        }

    def test_no_product_has_contradictory_wattage(self):
        offenders = []
        for slug, item in sorted(self.seed_products.items()):
            sources = self._sources(item)
            distinct = sorted({v for v in sources.values() if v})
            if len(distinct) > 1:
                offenders.append((slug, sources))
        self.assertEqual(
            offenders, [],
            'wattage disagrees across sources (P0-C regression): %r' % (offenders,),
        )

    def test_power_field_populated_whenever_wattage_is_known(self):
        """An empty ``power`` silently drops the wattage from title+desc.

        ``build_seo_title`` only appends the power clause when
        ``power and power not in core``. Four products are legitimately
        wattage-free (accessories and the RGB/RGBW concept page); every
        other product must carry the value so the formula can use it.
        """
        missing = []
        for slug, item in sorted(self.seed_products.items()):
            sources = self._sources(item)
            known = {v for v in sources.values() if v}
            if not known:
                if slug not in NO_WATTAGE_EXPECTED:
                    missing.append((slug, 'no wattage anywhere, and not an '
                                         'approved wattage-free product'))
                continue
            if not sources['power']:
                missing.append((slug, 'power empty but wattage is %s'
                                     % sorted(known)))
        self.assertEqual(
            missing, [],
            'power field empty although a wattage is known (title/desc drop '
            'the wattage clause): %r' % (missing,),
        )

    def test_wattage_free_products_are_exactly_the_approved_four(self):
        """The exemption list is a product decision, so it is asserted.

        If a genuinely new accessory is added the list must be extended on
        purpose; if one of the four gains a wattage the entry must go.
        """
        actual = set()
        for slug, item in self.seed_products.items():
            if not any(self._sources(item).values()):
                actual.add(slug)
        self.assertEqual(
            actual, set(NO_WATTAGE_EXPECTED),
            'the set of products with no wattage changed — update '
            'NO_WATTAGE_EXPECTED deliberately',
        )

    def test_db_path_wattage_matches_seed_path(self):
        """DB and seed must agree, or local and production render differently."""
        drift = []
        for slug, item in sorted(self.seed_products.items()):
            row = Product.objects.filter(slug=slug).first()
            if row is None:
                continue
            seed_w = self._sources(item)
            db = {
                'power': _wattage(row.power),
                'specs[Power]': _wattage(next(
                    (r.get('value') for r in (row.specs or [])
                     if isinstance(r, dict) and r.get('label') == 'Power'), '')),
                'energy_data[System Wattage]': _wattage(next(
                    (r.get('value') for r in (row.energy_data or [])
                     if isinstance(r, dict) and r.get('label') == 'System Wattage'), '')),
                'ordering_info[1]': _wattage(
                    (row.ordering_info or [None, None])[1]),
            }
            for key, seed_val in seed_w.items():
                if seed_val and db.get(key) and seed_val != db[key]:
                    drift.append((slug, key, seed_val, db[key]))
        self.assertEqual(
            drift, [],
            'DB and seed wattage drifted (seed_sync would silently overwrite '
            'one side): %r' % (drift,),
        )


class BeamAngleImageIntegrityTests(TestCase):
    """P0-E — the photometric chart must belong to the product that shows it.

    Borrowing a chart from a sibling product is legitimate when both share
    one optical platform, and the business has confirmed every remaining
    case (2026-10-06): the M-series modules, the VSP towers, the RT410
    series/RGBW pair, RT590FL-S~RT390FL, RT500HB~RT400HB and
    RT820SL-T~RT600SL-T all use the same optics. These guards therefore do
    NOT forbid borrowing — they forbid the two things that were actually
    wrong:

    1. a chart path that resolves to nothing on disk (online 404), and
    2. a chart whose plotted degrees are not among the degrees the product
       actually offers (``rt220ub`` sold a 100° optic against a 120° chart
       — a correctness bug, since the buyer would specify the wrong beam).
    """

    @classmethod
    def setUpTestData(cls):
        cls.seed_products = {
            p['slug']: p for p in _load_seed().get('products', [])
        }
        cls.static_root = os.path.join(settings.BASE_DIR, 'static')

    @staticmethod
    def _degrees_from_chart_name(path):
        """Parse the degree tokens out of a chart file name.

        Two naming conventions are in the tree and both must work:

        * ``beamangle-3050120.webp`` — the digits are the offered angles run
          together (30 / 50 / 120). There is no separator, so the *set* of
          angles cannot be recovered; only a single-degree name is
          unambiguous.
        * ``beamangle-120d-1.webp`` — the ``120d`` form names exactly one
          angle, which is the case the P0-E bug lived in.

        Returns a set of angles, or an empty set when the name does not
        pin a single angle (in which case there is nothing to cross-check).
        """
        base = os.path.basename(str(path or ''))
        m = re.search(r'beamangle-(\d+)d', base)
        if m:
            return {m.group(1)}
        return set()

    @staticmethod
    def _offered_degrees(item):
        ordering = item.get('ordering_info') or []
        beam_col = ordering[4] if len(ordering) > 4 else ''
        return set(re.findall(r'(\d+)', str(beam_col)))

    def test_single_degree_chart_matches_the_offered_beam_angles(self):
        offenders = []
        for slug, item in sorted(self.seed_products.items()):
            path = item.get('beam_angle_image') or ''
            if not path:
                continue
            chart = self._degrees_from_chart_name(path)
            if not chart:
                continue  # multi-angle chart, nothing unambiguous to check
            offered = self._offered_degrees(item)
            if not offered:
                continue
            if not chart <= offered:
                offenders.append((slug, os.path.basename(path), sorted(offered)))
        self.assertEqual(
            offenders, [],
            'a single-degree beam chart plots an angle the product does not '
            'offer (P0-E regression): %r' % (offenders,),
        )

    def test_beam_angle_chart_exists_on_disk(self):
        """A path that resolves to nothing renders a broken image slot."""
        missing = []
        for slug, item in sorted(self.seed_products.items()):
            for field in ('image', 'banner_image', 'dimension_image',
                          'beam_angle_image', 'ordering_image', 'cert_image'):
                path = item.get(field) or ''
                if not path:
                    continue
                rel = str(path).replace('\\', '/')
                if not os.path.isfile(os.path.join(self.static_root, rel)):
                    missing.append((slug, field, path))
        self.assertEqual(
            missing, [],
            'image field points at a file that is not in static/ (online 404): '
            '%r' % (missing,),
        )

    def test_orphaned_beam_charts_are_not_left_behind(self):
        """The 120° chart must sit with the product that sells 120°.

        Regression lock for the P0-E fix: the file was moved out of
        ``rt220ub/`` (which sells 100°) into ``rt420fs-s/``. Asserting the
        move from both ends — rt220ub must not reference it, and the file
        must exist where rt420fs-s looks for it — catches a revert that
        only fixes one side.
        """
        rt220ub = self.seed_products.get('rt220ub') or {}
        self.assertEqual(
            (rt220ub.get('beam_angle_image') or ''), '',
            'rt220ub offers a 100° optic only; pointing it at the 120° chart '
            'is the P0-E bug',
        )
        rt420 = self.seed_products.get('rt420fs-s') or {}
        path = (rt420.get('beam_angle_image') or '').replace('\\', '/')
        self.assertTrue(
            path.endswith('rt420fs-s/beamangle-120d-1.webp'),
            'rt420fs-s must own the 120° chart, got %r' % path,
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.static_root, path)),
            'rt420fs-s beam chart missing on disk: %r' % path,
        )
        self.assertFalse(
            os.path.isfile(os.path.join(
                self.static_root, 'images/products/rt220ub/beamangle-120d-1.webp')),
            'the 120° chart is back in rt220ub/ — it belongs to rt420fs-s',
        )
