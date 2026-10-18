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
from django.test.utils import override_settings
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext
import gettext as gettext_module
import html

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
