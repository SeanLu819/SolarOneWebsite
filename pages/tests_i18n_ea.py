"""E+A plumbing guard (2026-10-12).

E: 法律页 title/meta/og 字面量经 `{% trans %}` 路由到 gettext（见 templates/privacy.html,
templates/terms.html），并已用 MT 译出五语（用户 2026-10-12 明确指示牺牲「法律文本不机翻」换
非英语 SERP 标题；正文法律文本仍待 B5/C 专业/法务译文，不在本批）。

A: 35 个缺失 gettext 串中，16 个非法律 UI 串已补译文（MT 草稿，待母语复核），其余 19 个
cookie/GDPR/隐私合规串「不接受机翻」，继续留在 KNOWN_UNTRANSLATED（已编译进 .mo 但 msgstr 为空）。

本文件守卫三条事实：
  ① 16 个 UI 串在运行时真实翻译（gettext 查 .mo，与线上同路径），不只是存在于目录里；
  ② 合规串在五语下仍回退英文（绝不能悄悄被翻译，也不能被遗漏成空串）；
  ③ 法律页 6 个元数据串在运行时真实翻译，且 /fr/privacy/ 与 /fr/terms/ 渲染出的 <title> 非英文。
既有的 pages/tests.I18nCatalogGuardTests 已守住「目录里有没有条目」，这里补「运行时是否真生效」。
"""
from django.test import TestCase, SimpleTestCase
from django.conf import settings
from django.utils import translation
from django.utils.html import escapejs
from django.utils.translation import gettext
import gettext as gettext_module
import html
import re

# 16 个已译 UI 串（A 段非法律部分）。
TRANSLATED_UI = [
    'Application',
    'Change language',
    'Dimming (option)',
    'Filter / Categories',
    'Filter by Application',
    'Finish (option)',
    'Input Voltage',
    'LED Driver Location',
    'Main menu',
    'Sorry, we could not save your message. Please try again.',
    'Swipe to view all columns',
    'Theme',
    'Too many messages submitted recently. Please wait a few minutes before trying again.',
    'View image %(forloop.counter)s',
    'We could not deliver your message right now. Please try again later or email us directly using the address on this site.',
    'Your message has been sent successfully!',
]

# 19 个合规串（cookie/GDPR/隐私）—— 必须回退英文，禁止被翻译。
DEFERRED_COMPLIANCE = [
    'Accept All',
    'Analytics cookies:',
    'Cookie Usage',
    'Data We Collect',
    'Essential cookies:',
    'Help us understand how visitors interact with our website',
    'Last updated:',
    'Marketing cookies:',
    'Reject',
    'Required for basic site functionality',
    'Types of cookies we use:',
    'Under GDPR (EU) and similar regulations, you have the right to access, correct, or delete your personal data. Contact us at',
    'Used to deliver relevant advertisements',
    'We collect minimal data necessary for website functionality and analytics, including: device type, browser type, pages visited, and referring source. We do not sell your personal data to third parties.',
    "We use cookies to enhance your browsing experience and analyze site traffic. By clicking 'Accept', you consent to our use of cookies.",
    'We use cookies to enhance your browsing experience and analyze site traffic. Cookies are small text files stored on your device that help us understand how you use our website.',
    'You can accept or reject non-essential cookies at any time. Essential cookies cannot be disabled as they are necessary for the website to function.',
    'Your Rights',
    'for any privacy-related requests.',
]

# E 段：法律页 6 个唯一 msgid（title 与 og_title 共用同一条），用户指示 MT 译出。
LEGAL_METADATA = [
    'Privacy Policy \u2014 SolarOne LED Lighting',
    'SolarOne privacy policy: what data we collect through our contact form '
    'and analytics, how we use cookies, and your rights under GDPR and CCPA.',
    'How SolarOne collects, uses and protects your personal data when you '
    'visit our website or contact us.',
    'Terms of Service \u2014 SolarOne LED Lighting',
    'SolarOne terms of service: website use, intellectual property, product '
    'information disclaimer, and limitations of liability.',
    'The terms governing your use of the SolarOne website and the limitations '
    'that apply to product information shown.',
]

NON_SOURCE_LANGS = ('fr', 'es', 'de', 'ru', 'ar')


def _catalog(lang):
    path = __import__('os').path.join(
        settings.BASE_DIR, 'locale', lang, 'LC_MESSAGES', 'django.mo')
    with open(path, 'rb') as fh:
        return gettext_module.GNUTranslations(fh)._catalog


class EaI18nUiTranslatedTests(SimpleTestCase):
    """16 个 UI 串在五语下必须真实翻译（gettext 查 .mo，与线上同路径）。"""

    def test_ui_strings_translated(self):
        for msgid in TRANSLATED_UI:
            for lang in NON_SOURCE_LANGS:
                catalog = _catalog(lang)
                # 译文可能恰好等于原文（如 fr 'Application'），所以只验证：
                # ① 目录里有该条目；② 其 msgstr 非空（真的被翻译/显式填写，不是遗漏成空串）。
                self.assertIn(
                    msgid, catalog,
                    f'{msgid!r} 在 {lang} 的 .mo 里没有条目（未编译或漏译）')
                self.assertTrue(
                    catalog[msgid].strip(),
                    f'{msgid!r} 在 {lang} 的译文为空串')

    def test_ui_strings_resolve_at_runtime(self):
        # 运行时 gettext 必须命中编译后的 .mo（与线上同路径），不能只停在目录里。
        for msgid in TRANSLATED_UI:
            for lang in NON_SOURCE_LANGS:
                catalog = _catalog(lang)
                with translation.override(lang):
                    self.assertEqual(
                        gettext(msgid), catalog.get(msgid, ''),
                        f'{msgid!r} 在 {lang} 运行时 gettext 未命中编译后的 .mo')


class EaI18nComplianceFallbackTests(SimpleTestCase):
    """19 个合规串在五语下必须回退英文（不能翻译、也不能被遗漏成空串）。"""

    def test_compliance_strings_fallback_to_english(self):
        for msgid in DEFERRED_COMPLIANCE:
            for lang in NON_SOURCE_LANGS:
                with translation.override(lang):
                    self.assertEqual(
                        gettext(msgid), msgid,
                        f'合规串 {msgid!r} 在 {lang} 不应被翻译（应回退英文），却得到 {gettext(msgid)!r}')


class EaI18nLegalMetadataTranslatedTests(SimpleTestCase):
    """E 段：法律页 6 个元数据串在五语下必须真实翻译（用户指示牺牲「不机翻」换 SERP 标题）。"""

    def test_legal_metadata_translated(self):
        for msgid in LEGAL_METADATA:
            for lang in NON_SOURCE_LANGS:
                catalog = _catalog(lang)
                self.assertIn(
                    msgid, catalog,
                    f'{msgid!r} 在 {lang} 的 .mo 里没有条目（未编译或漏译）')
                self.assertTrue(
                    catalog[msgid].strip(),
                    f'{msgid!r} 在 {lang} 的译文为空串')
                # 译文必须真的非英文（防止「等于原文」的假绿）。
                self.assertNotEqual(
                    catalog[msgid], msgid,
                    f'{msgid!r} 在 {lang} 译文等于原文（未真正翻译）')

    def test_legal_metadata_resolve_at_runtime(self):
        for msgid in LEGAL_METADATA:
            for lang in NON_SOURCE_LANGS:
                catalog = _catalog(lang)
                with translation.override(lang):
                    self.assertEqual(
                        gettext(msgid), catalog.get(msgid, ''),
                        f'{msgid!r} 在 {lang} 运行时 gettext 未命中编译后的 .mo')


class EaI18nRenderTests(TestCase):
    """集成层：/fr/projects/ 实际渲染时，侧栏滤镜标签应显示法文，cookie 合规条仍英文。"""

    def test_fr_projects_filter_labels_translated(self):
        resp = self.client.get('/fr/projects/')
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8')
        self.assertIn('Filtrer / Catégories', body)
        self.assertIn('Filtrer par application', body)
        # 英文原文不应再出现（证明翻译生效，而非回退）。
        self.assertNotIn('Filter / Categories', body)
        self.assertNotIn('Filter by Application', body)
        # cookie 合规条（base.html 横幅）在 /fr/ 下仍是英文（按「法律文本不机翻」保留）。
        self.assertIn(
            'We use cookies to enhance your browsing experience and analyze site '
            'traffic. By clicking', body)

    def test_fr_legal_pages_title_translated(self):
        # 法律页非英语 SERP 标题实证：<title>/og_title 必须法文，原文整串不得出现。
        resp = self.client.get('/fr/privacy/')
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8')
        self.assertIn('Politique de confidentialit', body)
        self.assertNotIn('Privacy Policy \u2014 SolarOne LED Lighting', body)

        resp = self.client.get('/fr/terms/')
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8')
        self.assertIn('Conditions d\'utilisation', body)
        self.assertNotIn('Terms of Service \u2014 SolarOne LED Lighting', body)


# B 段残留：4 个 SiteConfig 活字段（about_title / about_text_1 / about_text_2 /
# footer_description）经是曾路由到 _t()，五语条目在 i18n_overrides.json。
# 恒等消息键取自 seed_data.json 的英文原值，不能手抄（_t() 查不到会静默回退）。
SIteCONFIG_FIELDS = [
    'about_title',
    'about_text_1',
    'about_text_2',
    'footer_description',
]

# 每个字段的「非英语必出现子串」——取自 i18n_overrides.json 的译文，
# 用作渲染实证与 _t() 源级实证的样本。
SITECONFIG_EXPECT = {
    'about_title': {
        'fr': 'Reconnu dans le monde', 'de': 'Weltweit aus gutem Grund',
        'es': 'Confiable en todo el mundo', 'ru': 'Доверие во всём мире',
        'ar': 'موثوق به في جميع أنحاء العالم'},
    'about_text_1': {
        'fr': 'Depuis 2007', 'de': 'Seit 2007', 'es': 'Desde 2007',
        'ru': 'С 2007 года', 'ar': 'منذ عام 2007'},
    'about_text_2': {
        'fr': 'La mission de SolarOne', 'de': 'Die Mission von SolarOne',
        'es': 'La misión de SolarOne', 'ru': 'Миссия SolarOne',
        'ar': 'مهمة SolarOne'},
    'footer_description': {
        'fr': 'Systèmes d\'éclairage LED professionnels',
        'de': 'Professionelle LED-Beleuchtungssysteme',
        'es': 'Sistemas de iluminación LED profesionales',
        'ru': 'Профессиональные светодиодные системы',
        'ar': 'أنظمة إضاءة LED احترافية'},
}


def _seed_siteconfig():
    import json
    path = __import__('os').path.join(settings.BASE_DIR, 'seed_data.json')
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)['siteconfig']


class BResidualSiteConfigTranslatedTests(SimpleTestCase):
    """B 段残留：4 个活字段在五语下必须真实翻译（_t 查 _SIDEBAR_I18N，含 overrides）。"""

    def test_fields_translate_at_source_level(self):
        from pages.views.i18n import _t
        cfg = _seed_siteconfig()
        for field in SIteCONFIG_FIELDS:
            val = cfg[field]
            for lang in NON_SOURCE_LANGS:
                translated = _t(val, lang)
                # SITECONFIG_EXPECT 是「译文里必出现的特征子串」，用 assertIn 断言；
                # 不能与整段译文做 assertEqual（长文本标点/空格微差会假红）。
                self.assertIn(
                    SITECONFIG_EXPECT[field][lang], translated,
                    f'{field} 在 {lang} 未命中 _SIDEBAR_I18N（键不匹配或条目缺失）')
                self.assertNotEqual(
                    translated, val,
                    f'{field} 在 {lang} 未真正翻译，回退了英文原文')
            # 英文必须逐字回退原值。
            self.assertEqual(_t(val, 'en'), val)

    def test_field_keys_match_seed(self):
        # 直接锁死「override 消息键 == seed 英文原值」（防手抄漂移）。
        from pages.views.i18n import _SIDEBAR_I18N
        cfg = _seed_siteconfig()
        for field in SIteCONFIG_FIELDS:
            self.assertIn(
                cfg[field], _SIDEBAR_I18N,
                f'{field} 的英文原值不在 _SIDEBAR_I18N 里（_t 会静默回退英文）')


class BResidualRenderTests(TestCase):
    """集成层：/fr/about/ 正文与全站页脚渲染法文，且英文原串不泄漏。"""

    def test_fr_about_page_translated(self):
        resp = self.client.get('/fr/about/')
        self.assertEqual(resp.status_code, 200)
        # 渲染层会 HTML 转义（' -> &#x27;），断言前先 unescape 才能与正文逐字比对。
        body = html.unescape(resp.content.decode('utf-8'))
        for field in SIteCONFIG_FIELDS:
            self.assertIn(
                SITECONFIG_EXPECT[field]['fr'], body,
                f'/fr/about/ 未渲染 {field} 的法文译文')
        cfg = _seed_siteconfig()
        for field in SIteCONFIG_FIELDS:
            self.assertNotIn(
                cfg[field], body,
                f'/fr/about/ 泄漏了 {field} 的英文原串')

    def test_fr_home_footer_translated(self):
        resp = self.client.get('/fr/')
        self.assertEqual(resp.status_code, 200)
        body = html.unescape(resp.content.decode('utf-8'))
        self.assertIn(SITECONFIG_EXPECT['footer_description']['fr'], body)
        self.assertNotIn(_seed_siteconfig()['footer_description'], body)

    def test_cross_locale_not_bleeding(self):
        # 先取 /fr/ 再取 /de/：LocMemCache 存的是 pickle 副本，不应当串味。
        fr = html.unescape(self.client.get('/fr/').content.decode('utf-8'))
        de = html.unescape(self.client.get('/de/').content.decode('utf-8'))
        self.assertIn(SITECONFIG_EXPECT['footer_description']['fr'], fr)
        self.assertIn(SITECONFIG_EXPECT['footer_description']['de'], de)
        self.assertNotIn(SITECONFIG_EXPECT['footer_description']['de'], fr)
        self.assertNotIn(SITECONFIG_EXPECT['footer_description']['fr'], de)


class SportsLandingI18nTests(TestCase):
    """Q1 sports-landing pages (football / tennis) translate at runtime.

    Their copy flows through two channels and both must resolve in the five
    non-English locales:

      * page copy (accent / h1 / intro / product_* / selection_* / venue_* /
        faq_heading and the FAQ Q&A) is gettext ``_()`` — checked here against
        the *compiled* ``.mo``, the same table the live site reads, so a
        forgotten compilemessages cannot hide behind a present ``.po``;
      * page_title / page_description route through the sidebar ``_t()``.

    These are subscript ``_()`` calls (``_(cfg['h1'])``), which
    ``I18nCatalogGuardTests``' literal-argument extractor cannot see — so this
    runtime guard is what stops a new string from silently serving English
    under a ``/fr/`` URL. Selection-row cells are intentionally out of scope:
    they carry order codes / model numbers (``FL6M, 480 W``) that must stay
    literal in every locale.
    """
    NON_SOURCE_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    def _prose(self):
        from pages.views.views_projects import SPORT_LANDING_PAGES
        items = []
        for sport, cfg in SPORT_LANDING_PAGES.items():
            for key in ('accent', 'h1', 'intro', 'product_heading',
                        'product_lead', 'selection_lead', 'selection_note',
                        'venue_heading', 'venue_lead', 'faq_heading'):
                items.append((sport, key, cfg[key]))
            for i, faq in enumerate(cfg['faq']):
                items.append((sport, 'faq%d.q' % i, faq['question']))
                items.append((sport, 'faq%d.a' % i, faq['answer']))
        return items

    def test_page_copy_resolves_translated_at_runtime(self):
        for sport, key, msgid in self._prose():
            for lang in self.NON_SOURCE_LANGS:
                with translation.override(lang):
                    got = gettext(msgid)
                self.assertTrue(
                    got and got.strip(),
                    '%s.%s resolved to an empty string in %s' % (sport, key, lang))
                self.assertNotEqual(
                    got, msgid,
                    '%s.%s fell back to English in %s (missing .mo entry?)'
                    % (sport, key, lang))

    def test_meta_title_and_description_resolve_via_sidebar_t(self):
        from pages.views.i18n import _t
        from pages.views.views_projects import SPORT_LANDING_PAGES
        for sport in ('football', 'tennis'):
            cfg = SPORT_LANDING_PAGES[sport]
            for field in ('title', 'description'):
                en = cfg[field]
                for lang in self.NON_SOURCE_LANGS:
                    self.assertNotEqual(
                        _t(en, lang), en,
                        '%s.%s fell back to English in %s (not in _SIDEBAR_I18N?)'
                        % (sport, field, lang))

    def test_fr_football_page_renders_translated(self):
        resp = self.client.get('/fr/projects/football/')
        self.assertEqual(resp.status_code, 200)
        body = html.unescape(resp.content.decode('utf-8'))
        # <title> is the French meta title, not the English one.
        self.assertIn("Projets d'\u00e9clairage de stades de football", body)
        self.assertNotIn('Football Stadium Lighting Projects | SolarOne', body)
        # A translated product lead and a translated FAQ question appear; the
        # English originals are gone.
        self.assertIn('Choisissez selon le niveau de jeu', body)
        self.assertIn('Combien de projecteurs un terrain de football', body)
        self.assertNotIn('How many floodlights does a football pitch need?', body)

    def test_ar_tennis_page_renders_translated(self):
        # RTL, non-latin: the Arabic meta title serves, the English one is gone.
        resp = self.client.get('/ar/projects/tennis/')
        self.assertEqual(resp.status_code, 200)
        body = html.unescape(resp.content.decode('utf-8'))
        self.assertIn('\u0645\u0634\u0627\u0631\u064a\u0639 \u0625\u0636\u0627\u0621\u0629 '
                      '\u0645\u0644\u0627\u0639\u0628 \u0627\u0644\u062a\u0646\u0633', body)
        self.assertNotIn('Tennis Court Lighting Projects | SolarOne', body)
        self.assertNotIn('What lux level do tennis courts need?', body)


class AboutPercentStringI18nTests(TestCase):
    """运行时守卫：含 `%` 的模板串必须真的译出（2026-10-18 `%%` bug 类）。

    Django 的 `{% trans %}` 在查目录前会把字面 `%` 翻倍成 `%%`
    （django/template/base.py Variable.resolve：``msgid = value.replace("%", "%%")``），
    与 templatize/makemessages 的提取形式一致。若 `.po` msgid 写成单 `%`，
    目录里「有条目、守卫也过」，但运行时永远查不到 → 五语全部静默显示英文。

    about.html 的两段 99% 文案就是这样坏了很久：译文五语齐全却从未生效。
    静态侧已由 I18nCatalogGuardTests（`_catalog_has` 精确匹配）把守；这里补
    「渲染出来真的是译文」的运行时证据。
    """

    # (lang, 第一段译文的探针)
    PROBES = (
        ('fr', 'Flux lumineux sup\u00e9rieur'),
        ('es', 'Mayor rendimiento luminoso'),
        ('de', 'H\u00f6herer Lichtoutput'),
        ('ru', '\u0411\u043e\u043b\u0435\u0435 \u0432\u044b\u0441\u043e\u043a\u0438\u0439 '
               '\u0441\u0432\u0435\u0442\u043e\u0432\u043e\u0439 \u043f\u043e\u0442\u043e\u043a'),
        ('ar', '\u0645\u062e\u0631\u062c\u0627\u062a \u0625\u0636\u0627\u0621\u0629 '
               '\u0623\u0639\u0644\u0649'),
    )
    ENGLISH_ORIGINALS = (
        'Higher light output at farther distances',
        'Proprietary glass achieves 99%',
    )

    def test_percent_paragraphs_render_translated_in_all_five_languages(self):
        for lang, probe in self.PROBES:
            resp = self.client.get('/%s/about/' % lang)
            self.assertEqual(resp.status_code, 200, lang)
            body = html.unescape(resp.content.decode('utf-8'))
            self.assertIn(
                probe, body,
                '%s: about.html 99%% 段落回退英文 —— .po msgid 必须是翻倍形式' % lang)
            for original in self.ENGLISH_ORIGINALS:
                self.assertNotIn(
                    original, body,
                    '%s: about.html 仍渲染英文原文 %r' % (lang, original))


class ProductsPageLabelI18nTests(TestCase):
    """运行时守卫：productspagecards 标签与 FAQ 标题必须真的译出。

    /products/ 索引页和三个 sports landing hero 会用卡片 title/subtitle
    **覆盖**产品已译的 ``name_t``。这些标签是我们撰写的页面文案、不是产品
    数据，不过 gettext 就会让 /fr/ /de/ … 页面成为全站唯一还把平台名显示成
    英文的地方。"Product FAQ" / "Frequently Asked Questions" 标题同理：曾
    是模板里裸的英文字面量，压根没进 trans 管道。2026-10-18 两处都已修，
    这里钉住渲染结果。
    """

    def test_fr_products_index_shows_translated_card_titles(self):
        resp = self.client.get('/fr/products/')
        self.assertEqual(resp.status_code, 200)
        body = html.unescape(resp.content.decode('utf-8'))
        for probe in ('S\u00e9rie M', 'S\u00e9rie RT410', 'S\u00e9rie VSP',
                      'Projecteurs', 'Haute Baie', '\u00c9clairage de rue'):
            self.assertIn(probe, body,
                          'fr /products/ 卡片标题未翻译（gettext 路由失效？）')
        # 卡片标签若回落英文，页面上会留下裸的 >M Series< 形式的 h3
        for raw in ('>M Series<', '>RT410 Series<', '>VSP series<',
                    '>FLOOD LIGHTING<', '>HIGHBAY<', '>Street Lighting<'):
            self.assertNotIn(raw, body, 'fr /products/ 仍渲染英文卡片标题 %r' % raw)

    def test_de_products_index_shows_translated_card_titles(self):
        body = html.unescape(
            self.client.get('/de/products/').content.decode('utf-8'))
        for probe in ('M-Serie', 'RT410-Serie', 'Flutlicht',
                      'Stra\u00dfenbeleuchtung'):
            self.assertIn(probe, body, 'de /products/ 卡片标题未翻译')
        self.assertNotIn('>M Series<', body)
        self.assertNotIn('>FLOOD LIGHTING<', body)

    def test_landing_heroes_use_translated_card_titles(self):
        # stadium / football / tennis 的 hero 卡同样走卡片标题覆盖
        for path in ('/fr/stadium-lighting/', '/fr/projects/football/',
                     '/fr/projects/tennis/'):
            body = html.unescape(
                self.client.get(path).content.decode('utf-8'))
            self.assertNotIn('>M Series<', body,
                             '%s hero 仍渲染英文卡片标题' % path)

    def test_faq_heading_renders_translated_not_literal(self):
        # 只看 h2 可见文本：CSS 注释里允许出现 "Product FAQ" 字样。
        for path, expected in (
            ('/fr/products/m-series/', 'FAQ produit'),
            ('/de/products/m-series/', 'Produkt-FAQ'),
        ):
            body = self.client.get(path).content.decode('utf-8')
            m = re.search(r'<h2 class="detail-faq-title">([^<]+)</h2>', body)
            self.assertIsNotNone(m, '%s 缺 FAQ 标题' % path)
            self.assertEqual(
                m.group(1), expected,
                '%s FAQ 标题未走 gettext（仍是硬编码英文字面量？）' % path)
        # 英文原串不得作为可见文本出现（注释里允许）
        body = self.client.get('/fr/products/m-series/').content.decode('utf-8')
        m = re.search(r'<h2 class="detail-faq-title">([^<]+)</h2>', body)
        self.assertNotEqual(m.group(1), 'Product FAQ')


class ProjectTitleI18nTests(TestCase):
    """运行时守卫：项目 title 五语覆盖 + 无 MT 报错串残留（2026-10-18）。

    三类失效模式，各有事故史：

    ① 16 个项目的 translations 块只有 description/location/results、title
       整块缺失 —— title 是 H1 / og:title / JSON-LD headline / 面包屑最可见
       的字段，缺译即这些位置整块回退英文。断言「每个项目的五语 title 均
       非空」，数据从 _load_seed()（生产同路径：优先构建产物
       pages/seed_data.py）派生，不写死项目数量。
    ② beijing-capital-international-airport 的 es/de/ru/ar 四语 title/
       description/location/results 曾被 MT API 速率限制写成
       `[Error: Server Error: ...]` 报错串 —— translate() 只判「非空」，
       报错串因此赢过英文回退，线上 H1 直接渲染报错串。断言任何 section
       的任何翻译字段都不得包含 `[Error:`。
    ③ 渲染层：/fr 与 /ar 项目详情页的 H1 / og:title / JSON-LD headline
       必须等于该语 title_t（期望值同样从 seed 派生），英文标题不得出现在
       H1（<title> 走英文 SEO 公式是刻意设计，不在此断言范围）。
    """

    NON_SOURCE_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    def _seed(self):
        from pages.views.utils import _load_seed
        return _load_seed()

    def test_every_project_title_translated_in_all_five_languages(self):
        seed = self._seed()
        for project in seed['projects']:
            tr = project.get('translations') or {}
            for lang in self.NON_SOURCE_LANGS:
                title = ((tr.get(lang) or {}).get('title') or '').strip()
                self.assertTrue(
                    title,
                    '%s 缺 %s title 译文 —— H1/og:title/JSON-LD 将回退英文'
                    % (project['slug'], lang))

    def test_no_translation_field_contains_mt_error_string(self):
        seed = self._seed()
        for section in ('projects', 'products', 'news'):
            for item in seed[section]:
                tr = item.get('translations') or {}
                for lang, block in tr.items():
                    for field, value in (block or {}).items():
                        if isinstance(value, str) and '[Error' in value:
                            self.fail(
                                '%s %s.%s.%s 残留 MT 报错串：%r'
                                % (section, item.get('slug'), lang, field,
                                   value[:60]))

    def test_localized_project_pages_render_translated_title(self):
        seed = self._seed()
        by_slug = {p['slug']: p for p in seed['projects']}
        for slug, lang in (('perryville-high-school', 'fr'),
                           ('beijing-capital-international-airport', 'ar')):
            project = by_slug[slug]
            expected = project['translations'][lang]['title']
            resp = self.client.get('/%s/projects/%s/' % (lang, slug))
            self.assertEqual(resp.status_code, 200, '%s %s' % (lang, slug))
            body = html.unescape(resp.content.decode('utf-8'))
            m = re.search(r'<h1 class="section-title"[^>]*>([^<]+)</h1>', body)
            self.assertIsNotNone(m, '%s %s 缺 H1' % (lang, slug))
            self.assertEqual(m.group(1), expected,
                             '%s %s H1 不是该语 title_t' % (lang, slug))
            self.assertNotIn(m.group(1), project['title'],
                             '%s %s 探针自证失败：译文等于英文原文' % (lang, slug))
            og = re.search(r'<meta property="og:title" content="([^"]*)"', body)
            self.assertIsNotNone(og, '%s %s 缺 og:title' % (lang, slug))
            self.assertIn(expected, og.group(1),
                          '%s %s og:title 不是该语 title_t' % (lang, slug))
            # headline 走 escapejs（连字符 -> ﻿ 是 Django 防 `-->`
            # 序列的刻意转义），断言必须用同一函数派生期望值。
            self.assertIn('"headline": "%s"' % escapejs(expected), body,
                          '%s %s JSON-LD headline 不是该语 title_t'
                          % (lang, slug))
