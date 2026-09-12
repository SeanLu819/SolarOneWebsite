import re
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from pages.admin import ProjectAdmin
from pages.views import _product_image_url, _get_project_detail_from_json, _enrich_project
from django.utils.translation import activate


# In production the static storage is content-hashed (Manifest storage), so
# resolved URLs look like /static/.../name.<12-hex>.webp; locally they are
# un-hashed. These tests care about *path* resolution (slug subdirectory
# fallback), so strip any content hash first to stay storage-agnostic.
_HASH_RE = re.compile(r'\.[0-9a-f]{12}(\.[A-Za-z0-9]+)$')


def _strip_static_hash(url: str) -> str:
    return _HASH_RE.sub(r'\1', url)


class ProductImagePathResolutionTests(SimpleTestCase):
    def test_static_fallback_finds_file_in_slug_subdirectory(self):
        """DB stores old flat path, but assets now live in slug/ subdirectory.
        The resolver should find the real file even though DB path differs."""
        product = SimpleNamespace(
            slug='fl4m',
            image=SimpleNamespace(name='products/fl4m-01.webp'),
        )
        url = _strip_static_hash(_product_image_url(product, 'image'))
        self.assertIn('/static/images/products/fl4m/fl4m-01.webp', url)  # ← 实际位置

    def test_static_fallback_prefers_db_relative_canonical_path(self):
        product = SimpleNamespace(
            slug='rt590fl-s',
            banner_image=SimpleNamespace(name='products/vsp/vsp-bar-1.webp'),
        )

        url = _strip_static_hash(_product_image_url(product, 'banner_image'))

        self.assertIn('/static/images/products/vsp/vsp-bar-1.webp', url)


class ProjectAdminOrderingTests(SimpleTestCase):
    def test_project_admin_images_section_comes_before_content(self):
        fieldset_names = [name for name, _ in ProjectAdmin.fieldsets]

        self.assertEqual(ProjectAdmin.change_form_template, 'admin/pages/project/change_form.html')
        self.assertLess(fieldset_names.index('Images'), fieldset_names.index('Content'))


class FootballFieldProjectImageTests(TestCase):
    """Verify football-field-led-retrofit project: cover + gallery paths resolve to valid static URLs."""

    def test_cover_and_gallery_resolve(self):
        activate('en')
        slug = 'football-field-led-retrofit'
        project = _get_project_detail_from_json(slug, 'en')
        self.assertIsNotNone(project, f'Project {slug} not found in seed data')
        _enrich_project(project, 'en')

        self.assertTrue(project.image_url, 'Cover image URL should not be empty')
        self.assertTrue(project.image_url.startswith('/static/'),
                        f'Cover should resolve to /static/ URL, got: {project.image_url}')

        self.assertGreaterEqual(len(project.gallery), 3,
                                f'Expected at least 3 gallery images, got {len(project.gallery)}')
        for i, g in enumerate(project.gallery):
            self.assertTrue(g['src'].startswith('/static/'),
                            f'Gallery [{i}] URL should start with /static/: {g["src"]}')
            self.assertIn('football-field-led-retrofit', g['src'],
                          f'Gallery [{i}] URL should contain slug: {g["src"]}')
        print(f'  OK cover={project.image_url}')
        for g in project.gallery:
            print(f'  OK gal={g["src"]}')


class SecurityHeadersTests(SimpleTestCase):
    """Security response headers & cookie flags (#5, #6, #22, #7)."""

    def test_nosniff_and_referrer_policy_on_every_response(self):
        resp = self.client.get('/definitely-not-a-real-page/')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('Referrer-Policy'),
                         'strict-origin-when-cross-origin')

    def test_ssl_redirect_and_hsts_match_environment(self):
        if settings.IS_VERCEL:
            self.assertTrue(settings.SECURE_SSL_REDIRECT)
            self.assertGreaterEqual(settings.SECURE_HSTS_SECONDS, 31536000)
            resp = self.client.get('/definitely-not-a-real-page/', secure=True)
            self.assertIn('Strict-Transport-Security', resp.headers)
        else:
            # Local http://127.0.0.1 must not force HTTPS/HSTS.
            self.assertFalse(settings.SECURE_SSL_REDIRECT)
            self.assertEqual(settings.SECURE_HSTS_SECONDS, 0)

    def test_cookie_samesite_defaults(self):
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_csrf_cookie_stays_js_readable(self):
        # auto_translate.js reads the csrftoken cookie → HttpOnly must stay False.
        self.assertFalse(getattr(settings, 'CSRF_COOKIE_HTTPONLY', False))


@unittest.skipUnless(settings.IS_VERCEL,
                     'HTTPS-only cookies are enforced only on Vercel')
class VercelSecureCookieTests(SimpleTestCase):
    def test_secure_cookie_flags_enabled(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)

    def test_plain_http_request_redirects_to_https(self):
        resp = self.client.get('/definitely-not-a-real-page/', secure=False)
        self.assertIn(resp.status_code, (301, 302))
        self.assertTrue(resp.headers.get('Location', '').startswith('https://'))


class TextFilterSafetyTests(SimpleTestCase):
    """#9/#10 — template filters must escape untrusted text (XSS)."""

    def test_nl2para_escapes_inline_html(self):
        from pages.templatetags.text_filters import nl2para
        out = nl2para('Hello <script>alert(1)</script>\n\nWorld')
        self.assertNotIn('<script>', out)
        self.assertIn('&lt;script&gt;', out)
        self.assertIn('<p>Hello', out)
        self.assertIn('<p>World</p>', out)

    def test_nl2para_paragraph_and_break_structure(self):
        from pages.templatetags.text_filters import nl2para
        out = nl2para('A\nB\n\nC')
        self.assertIn('<p>A<br>B</p>', out)
        self.assertIn('<p>C</p>', out)

    def test_linebreaktospaces_escapes_raw_input(self):
        from pages.templatetags.text_filters import linebreaktospaces
        out = linebreaktospaces('<script>x</script>')
        self.assertNotIn('<script>', out)
        self.assertIn('&lt;script&gt;', out)

    def test_linebreaktospaces_strips_br_from_safe_html(self):
        from django.utils.safestring import mark_safe
        from pages.templatetags.text_filters import linebreaktospaces
        out = linebreaktospaces(mark_safe('<p>A<br>B</p>'))
        self.assertIn('<p>A B</p>', out)


class SiteConfigCssValidationTests(SimpleTestCase):
    """#11 — CSS-typed SiteConfig fields must reject injection payloads."""

    def _assert_invalid(self, **fields):
        from django.core.exceptions import ValidationError
        from pages.models import SiteConfig
        cfg = SiteConfig(**fields)
        with self.assertRaises(ValidationError):
            cfg.full_clean()

    def test_accent_color_rejects_css_escape(self):
        self._assert_invalid(accent_color='#0088FF; } body { background: red')

    def test_accent_color_accepts_valid_hex_and_rgb(self):
        from pages.models import SiteConfig
        SiteConfig(accent_color='#FF6B00').full_clean()
        SiteConfig(accent_color='rgb(0, 136, 255)').full_clean()

    def test_font_size_rejects_injection(self):
        self._assert_invalid(font_size_base='16px; } * { display: none')

    def test_font_size_accepts_valid_units(self):
        from pages.models import SiteConfig
        for value in ('16px', '1.25rem', '1.05em', '50%'):
            SiteConfig(font_size_base=value).full_clean()

    def test_font_family_rejects_injection(self):
        self._assert_invalid(font_family_body="'} body{background:url(x)} '")

    def test_font_family_accepts_existing_production_value(self):
        from pages.models import SiteConfig
        SiteConfig(
            font_family_body="'Inter', 'Helvetica Neue', Arial, sans-serif"
        ).full_clean()


class CanonicalOriginTests(TestCase):
    """#17 — SEO URLs must use the fixed CANONICAL_ORIGIN, never the Host."""

    def test_sitemap_uses_fixed_origin(self):
        resp = self.client.get('/sitemap.xml', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('https://www.solaronelighting.com', content)
        self.assertNotIn('evil.vercel.app', content)

    def test_robots_txt_uses_fixed_origin(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn(
            'Sitemap: https://www.solaronelighting.com/sitemap.xml', content)
        self.assertNotIn('evil.vercel.app', content)

    def test_home_canonical_and_jsonld_use_fixed_origin(self):
        resp = self.client.get('/', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('evil.vercel.app', content)
        self.assertIn('https://www.solaronelighting.com', content)


class SitemapMultilingualTests(TestCase):
    """P1 — the sitemap must expose all 6 languages via xhtml:link alternates."""

    def test_sitemap_declares_xhtml_namespace_and_alternates(self):
        content = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('xmlns:xhtml="http://www.w3.org/1999/xhtml"', content)
        for code in ('en', 'fr', 'es', 'de', 'ru', 'ar'):
            self.assertIn(f'hreflang="{code}"', content)
        self.assertIn('hreflang="x-default"', content)

    def test_sitemap_loc_entries_are_language_neutral_even_when_prefixed(self):
        """Requesting /fr/sitemap.xml must not double-prefix the <loc> URLs."""
        root_locs = re.findall(r'<loc>(.*?)</loc>',
                               self.client.get('/sitemap.xml').content.decode())
        prefixed = self.client.get('/fr/sitemap.xml')
        self.assertEqual(prefixed.status_code, 200)
        prefixed_text = prefixed.content.decode()
        prefixed_locs = re.findall(r'<loc>(.*?)</loc>', prefixed_text)
        self.assertEqual(root_locs, prefixed_locs)
        self.assertNotIn('/fr/fr/', prefixed_text)

    def test_sitemap_alternates_point_at_every_language(self):
        content = self.client.get('/sitemap.xml').content.decode()
        for code, suffix in (('fr', '/fr/'), ('ar', '/ar/'), ('ru', '/ru/')):
            self.assertIn(
                f'hreflang="{code}" href="https://www.solaronelighting.com{suffix}"',
                content,
            )


class AboveTheFoldImageTests(SimpleTestCase):
    """P1 — first-screen (LCP) images must be eager and high priority.

    Guards against regressions where a hero/banner image gets re-tagged
    `loading="lazy"`, which delays Largest Contentful Paint.
    """

    def _read(self, name):
        return (Path(settings.BASE_DIR) / 'templates' / name).read_text(encoding='utf-8')

    def _assert_lcp(self, tag):
        self.assertNotIn('loading="lazy"', tag)
        self.assertIn('fetchpriority="high"', tag)
        self.assertIn('decoding="async"', tag)

    def test_product_detail_hero_is_lcp(self):
        tags = re.findall(r'<img[^>]*series-hero-bg[^>]*>',
                          self._read('product_detail.html'))
        self.assertEqual(len(tags), 1)
        self._assert_lcp(tags[0])

    def test_product_series_hero_is_lcp(self):
        tags = re.findall(r'<img[^>]*series-hero-bg[^>]*>',
                          self._read('product_series.html'))
        self.assertEqual(len(tags), 1)
        self._assert_lcp(tags[0])

    def test_home_hero_first_slide_is_lcp(self):
        tags = re.findall(r'<img[^>]*class="hero-slide active"[^>]*>',
                          self._read('home.html'))
        self.assertEqual(len(tags), 1)
        self._assert_lcp(tags[0])

    def test_products_page_banner_not_lazy(self):
        """Both theme variants are eager; only the default (dark) one is high
        priority, so the light asset never competes with the LCP candidate."""
        tags = re.findall(r'<img[^>]*products-banner-img[^>]*>',
                          self._read('products.html'))
        self.assertEqual(len(tags), 2)
        dark = [t for t in tags if 'products-banner-dark' in t]
        light = [t for t in tags if 'products-banner-light' in t]
        self.assertEqual(len(dark), 1)
        self.assertEqual(len(light), 1)
        for tag in tags:
            self.assertNotIn('loading="lazy"', tag)
        self.assertIn('fetchpriority="high"', dark[0])
        self.assertNotIn('fetchpriority', light[0])


class VisitorIpHashTests(TestCase):
    """#16 — visitor IPs are stored hashed, never as plaintext (GDPR)."""

    def test_stored_ip_is_hashed_not_plaintext(self):
        self.client.get('/', HTTP_X_FORWARDED_FOR='203.0.113.50',
                        HTTP_USER_AGENT='Mozilla/5.0 (test-suite)')
        from pages.models import Visitor
        row = Visitor.objects.order_by('-id').first()
        self.assertIsNotNone(row)
        self.assertNotIn('203.0.113.50', row.ip_address)
        self.assertRegex(row.ip_address, r'^[0-9a-f]{64}$')

    def test_unique_visit_counting_still_works(self):
        ua = 'Mozilla/5.0 (unique-test)'
        self.client.get('/', HTTP_X_FORWARDED_FOR='198.51.100.9',
                        HTTP_USER_AGENT=ua)
        self.client.get('/', HTTP_X_FORWARDED_FOR='198.51.100.9',
                        HTTP_USER_AGENT=ua)
        from pages.models import Visitor
        rows = list(Visitor.objects.order_by('id'))
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].is_unique)
        self.assertFalse(rows[1].is_unique)


class ContactFormSecurityTests(TestCase):
    """#13/#15 — rate-limit fail-closed + honeypot spam trap."""

    def test_rate_limit_fails_closed_when_cache_broken(self):
        from unittest.mock import patch
        from django.test import RequestFactory
        from pages.views.views_contact import _is_rate_limited
        req = RequestFactory().post('/contact/')
        # RequestFactory requests lack a session (SessionMiddleware not applied)
        req.session = SimpleNamespace(session_key=None)
        with patch('pages.views.views_contact.cache.get',
                   side_effect=Exception('cache down')):
            self.assertTrue(_is_rate_limited(req),
                            'cache failure must DENY the request (fail closed)')

    def test_honeypot_silently_drops_bot_submissions(self):
        resp = self.client.post(reverse('contact'), {
            'name': 'Spam Bot',
            'email': 'bot@spam.example',
            'message': 'buy cheap stuff',
            'company_website': 'http://spam.example',
        })
        self.assertEqual(resp.status_code, 200)
        from pages.models import ContactMessage
        self.assertFalse(
            ContactMessage.objects.filter(email='bot@spam.example').exists(),
            'honeypot-filled submissions must NOT be saved')

    def test_normal_submission_still_saved(self):
        resp = self.client.post(reverse('contact'), {
            'name': 'Real Person',
            'email': 'real@customer.example',
            'message': 'Please quote the FL4M series.',
        })
        self.assertEqual(resp.status_code, 200)
        from pages.models import ContactMessage
        self.assertTrue(
            ContactMessage.objects.filter(email='real@customer.example').exists(),
            'normal submissions (no honeypot) must still be saved')

class ResponsiveNavTests(TestCase):
    """阶段一 F1' — 导航单一数据源 + 移动端功能不丢失（渲染 DOM 契约，§6.2/§8.5）。

    断言的是"渲染出的 DOM"而非 CSS 字符串，因此能捕获：
    1) 汉堡/nav-links/面板结构的回归；
    2) 桌面与移动面板导航不同步（双份数据源）；
    3) 多行 `{# #}` 未闭合注释泄漏到 HTML（Django 的 silent 行为）。
    """

    def _home(self):
        resp = self.client.get('/', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_hamburger_present_with_aria(self):
        html = self._home()
        self.assertIn('id="hamburgerBtn"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn('aria-controls="mobilePanel"', html)

    def test_nav_links_is_ul(self):
        # 外部工具会向 base.html 全部元素注入 data-page-node-id 等属性，
        # 故用正则匹配标签而非精确串（精确串会因多出的属性失配，v1.1.4）

        html = self._home()
        self.assertRegex(html, r'<ul\s+class="nav-links"[\s>]')

    def test_legacy_duplicate_ids_removed(self):
        # 改为多实例 class 绑定后，旧的单例 id 必须移除（否则出现重复 id）
        html = self._home()
        self.assertNotIn('id="themeToggle"', html)
        self.assertNotIn('id="langSwitchBtn"', html)
        self.assertNotIn('id="langSwitchMenu"', html)

    def test_no_unclosed_django_comment_leaks(self):
        # `{# ... #}` 是单行注释；跨行未闭合时 Django 不报错、原文进 HTML
        html = self._home()
        self.assertNotIn('{#', html)

    def test_mobile_panel_has_full_navigation(self):
        # 移动端不丢任何入口：5 项主链接 + Contact + 主题 + 语言
        html = self._home()
        panel = html.split('id="mobilePanel"')[1]
        for slug in ('home', 'products', 'projects', 'news', 'about', 'contact'):
            self.assertIn(f'data-nav="{slug}"', panel)
        self.assertIn('theme-toggle', panel)
        self.assertIn('lang-switch-option', panel)

    def test_desktop_and_panel_share_single_source(self):
        # 桌面 .nav-links 与移动面板必须来自同一份 include，顺序与集合完全一致
        import re
        html = self._home()
        desktop = html.split('class="nav-links"')[1].split('</ul>')[0]
        panel = html.split('class="mobile-panel-links"')[1].split('</ul>')[0]
        self.assertEqual(
            re.findall(r'data-nav="(\w+)"', desktop),
            re.findall(r'data-nav="(\w+)"', panel),
        )
class ResponsivePhase1Tests(TestCase):
    """阶段一其余项（N-1/N-5/N-8/N-9/N-10/F4'/F5'）— v1.1.5。

    按 §6.8.3 策略，iOS/OS 级行为不模拟，改为断言"防御性 CSS/HTML 是否存在"
    （比真机更可回归）；F4' 为渲染 DOM 契约断言。CSS/HTML 直接读源码文件
    （L1 针对源码状态；部署产物由 collectstatic 在发布时生成）。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = Path(settings.BASE_DIR, 'static', 'css', 'base.css').read_text(encoding='utf-8')
        cls.base_html = Path(settings.BASE_DIR, 'templates', 'base.html').read_text(encoding='utf-8')

    def _get(self, url):
        resp = self.client.get(url, HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200, f'{url} must render')
        return resp.content.decode()

    # ---- N-1: 输入框 font-size >= 16px（iOS 聚焦自动放大且不回弹） ----
    def test_n1_form_inputs_16px(self):
        # contact.html 表单控件用内联样式（非 .form-group 结构）——
        # 内联 font-size:0.9rem(<16px) 会让 iOS 聚焦自动放大且不回弹。
        # 断言渲染 DOM（L2 首跑发现纯 CSS 规则断言抓不到该问题，v1.1.6）。
        # 仅限 <form id="contactForm"> 片段：页内联系信息文本（地址/电话等
        # span/a）用 0.9rem 属正常展示排版，与 N-1 无关。
        html = self._get('/contact/')
        form = html.split('id="contactForm"', 1)[1].split('</form>', 1)[0]
        self.assertNotIn('font-size: 0.9rem', form)
        self.assertIn('font-size: 16px', form)
        # 通用兜底：base.css 中 .form-group 的 16px 覆盖规则仍在
        self.assertRegex(
            self.css,
            r'\.form-group input,\s*\.form-group textarea\s*\{\s*font-size:\s*16px',
        )

    # ---- N-10: 全局长词换行保护 ----
    def test_n10_body_overflow_wrap_anywhere(self):
        self.assertRegex(self.css, r'body\s*\{[^}]*overflow-wrap:\s*anywhere')

    # ---- N-8: reduced-motion 下关闭平滑滚动（CSS + JS 两侧） ----
    def test_n8_reduced_motion_disables_smooth_scroll(self):
        self.assertRegex(
            self.css,
            r'@media \(prefers-reduced-motion: reduce\)\s*\{\s*html\s*\{\s*scroll-behavior:\s*auto',
        )
        self.assertIn("matchMedia('(prefers-reduced-motion: reduce)')", self.base_html)

    # ---- N-9: 移动端触摸目标 >=44px（伪元素扩大命中区，视觉尺寸不变） ----
    def test_n9_touch_target_hit_areas(self):
        self.assertRegex(self.css, r'\.theme-toggle::after\s*\{[^}]*inset:\s*-4px')
        self.assertRegex(self.css, r'\.lang-switch-btn::after\s*\{[^}]*inset:\s*-9px')

    # ---- N-5: Google Fonts 异步加载 + noscript 兜底 ----
    def test_n5_fonts_async_with_noscript_fallback(self):
        html = self._get('/')
        self.assertIn('media="print"', html)
        self.assertIn("this.media='all'", html)
        self.assertRegex(
            html,
            r'<noscript><link href="https://fonts\.googleapis\.com/[^"]*" rel="stylesheet"',
        )

    # ---- F5': 移动端字号 min(max()) 收口 + -admin 间接层（桌面零改动） ----
    def test_f5_mobile_typography_clamp(self):
        self.assertRegex(
            self.css,
            r'--fs-hero-title:\s*min\(var\(--fs-hero-title-admin\),\s*max\(30px, calc\(1rem \+ 4vw\)\)\)',
        )
        self.assertRegex(
            self.css,
            r'--fs-section-title:\s*min\(var\(--fs-section-title-admin\),\s*max\(22px, calc\(0\.85rem \+ 2\.4vw\)\)\)',
        )
        html = self._get('/')
        self.assertIn('--fs-hero-title-admin:', html)
        self.assertIn('--fs-section-title-admin:', html)

    # ---- F4': 侧栏 checkbox hack —— input/label/aside 同级且按序（~ 选择器前提） ----
    def test_f4_sidebar_toggle_dom_contract(self):
        for url in ('/products/', '/projects/', '/news/'):
            html = self._get(url)
            self.assertIn('class="sidebar-toggle-input"', html, url)
            self.assertIn('for="sidebarToggle"', html, url)
            self.assertRegex(
                html,
                r'<input type="checkbox" id="sidebarToggle"[^>]*>'
                r'\s*<label for="sidebarToggle"[^>]*>[^<]*</label>'
                r'\s*<aside class="sidebar-nav"',
                url,
            )

    def test_f4_sidebar_toggle_css_rules(self):
        self.assertIn(
            '.sidebar-toggle-input:not(:checked) ~ .sidebar-nav { display: none; }',
            self.css,
        )
        self.assertRegex(self.css, r'\.sidebar-toggle-label\s*\{[^}]*display:\s*flex')


class ResponsiveDeviceFixesTests(TestCase):
    """真机反馈修复（N-22 / N-24）的防回归断言。

    N-22（RTL 抽屉方向）与 N-24（reduced-motion 不得停轮播）都发生在
    渲染层之外——前者是纯 CSS 方向，后者是 JS 分支——Django Test Client
    拿不到计算结果，所以按 §6.8.3 的策略断言「防御性写法是否存在」。
    这比真机更强：真机只能证明这次没坏，断言保证永远不会坏。
    """

    def _home_html(self):
        resp = self.client.get('/', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = Path(settings.BASE_DIR, 'static/css/base.css').read_text(
            encoding='utf-8')

    def test_rtl_drawer_slides_from_left(self):
        # N-22: 阿拉伯语下抽屉必须从左侧滑出，否则与阅读方向相反
        self.assertIn('[dir="rtl"] .mobile-panel:not(.open)', self.css)
        self.assertIn('transform: translateX(-100%)', self.css)

    def test_carousel_not_gated_by_reduced_motion(self):
        # N-24: reduced-motion 只能去掉淡入淡出，不能停掉轮播，
        # 否则开了「减弱动态效果」的用户永远看不到第 2..n 张图
        html = self._home_html()
        self.assertNotIn(".matches) return;", html)
        self.assertIn('setInterval(next, interval);', html)
        # 淡入淡出仍需在 reduced-motion 下关闭
        self.assertIn('.hero-slide { transition: none; }', self.css)


class ResponsiveBlowoutAndHeroTests(TestCase):
    """N-25（grid blowout）/ N-26（hero 竖版 <picture>）防回归。

    N-25 的失效模式很隐蔽：模板内联 <style> 里的 `1fr !important` 加载在
    base.css 之后，会反杀 N-21 的 minmax(0, 1fr)，让修复静默失效——
    manage.py check / test 全绿，只有真实渲染才看得见。产品详情页因此在
    390px 视口被撑到 921px，手机端只能看到约 42% 的页面。
    这里同时断言「根本解存在」与「反杀写法不存在」。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = Path(settings.BASE_DIR, 'static/css/base.css').read_text(
            encoding='utf-8')
        cls.templates = {
            p.name: p.read_text(encoding='utf-8')
            for p in Path(settings.BASE_DIR, 'templates').glob('*.html')
        }

    def test_grid_items_have_min_width_zero(self):
        # N-25 根本解：grid item 的 min-width:auto 是 blowout 的传导路径，
        # 归零后无论轨道写成 1fr 还是 minmax(0,1fr) 都不会撑破页面
        self.assertIn('.sidebar-layout > *', self.css)
        self.assertIn('min-width: 0;', self.css)

    def test_no_bare_1fr_sidebar_override(self):
        for name, src in self.templates.items():
            self.assertNotIn(
                'grid-template-columns: 1fr !important', src,
                f"{name} 仍在使用 `1fr !important`，会反杀 N-21/N-25 并重新"
                f"触发 grid blowout（应改为 minmax(0, 1fr) !important）")

    def test_sidebar_uses_minmax_zero(self):
        for name in ('product_detail.html', 'product_series.html',
                     'project_detail.html', 'news.html'):
            self.assertIn('grid-template-columns: minmax(0, 1fr) !important',
                          self.templates[name])

    def test_energy_table_wraps_on_mobile(self):
        # th 的 nowrap 是 energy 表被撑到 899px 的原因：
        # 桌面保留 nowrap（排版需要），窄屏必须放开让它自然换行
        src = self.templates['product_detail.html']
        self.assertIn('white-space: nowrap', src)
        self.assertIn('white-space: normal', src)

    def test_hero_uses_picture_with_portrait_source(self):
        src = self.templates['home.html']
        self.assertIn('<picture>', src)
        self.assertIn('media="(max-width: 767px)"', src)
        for i in (1, 2, 3):
            self.assertIn(f'images/hero-main-{i}-portrait.webp', src)

    def test_hero_portrait_files_exist(self):
        # <picture> 的 source 一旦 media 匹配就不会回退到 img，
        # 文件缺失 = 手机端 hero 直接白屏，比裁切严重得多
        for i in (1, 2, 3):
            p = Path(settings.BASE_DIR, 'static/images',
                     f'hero-main-{i}-portrait.webp')
            self.assertTrue(p.exists(), f"缺少竖版 hero 图：{p.name}")

    def test_hero_portrait_is_actually_portrait(self):
        try:
            from PIL import Image
        except ImportError:  # pragma: no cover
            self.skipTest("PIL 未安装")
        for i in (1, 2, 3):
            p = Path(settings.BASE_DIR, 'static/images',
                     f'hero-main-{i}-portrait.webp')
            with Image.open(p) as im:
                w, h = im.size
            self.assertGreater(h, w, f"{p.name} 不是竖版：{w}x{h}")
            self.assertLess(abs(w / h - 0.75), 0.03,
                            f"{p.name} 比例偏离 3:4 过多：{w}x{h}")

    def test_picture_does_not_break_slider_layout(self):
        # picture 是 inline 元素，会在 track 内留下空行盒
        self.assertIn(
            '.hero-carousel-track > picture { display: contents; }', self.css)


class ResponsiveIOSSafeAreaTests(TestCase):
    """N-27（移动端底部按钮被系统 UI 遮住）防回归，v1.1.12 改判方向。

    早期 v1.1.11 的判断把问题归到 iOS Home Indicator（错的）：
      → 加 viewport-fit=cover、靠 env() 让出 34px。
    真机复核（iPhone 14 + 安卓百度 App）揭示真实情况：
      → iOS Safari/Chrome **自己就会避让 Home Indicator**，按钮正常显示。
      → **安卓**百度 App 内嵌 WebView、微信内置、部分 Chrome
        env(safe-area-inset-bottom) **几乎都返回 0 或直接不支持**，
        底部 Theme/Lang 按钮贴底被完全遮住。
    因此正确解是：删掉 viewport-fit=cover（破坏桌面布局、对 iOS 也没用），
    改用 max() 兜底：env() 支持则取 env+48，不支持则固定 80px。
    80px ≈ 安卓底部导航条(50) + 手势条(24)，任一设备都不会被遮。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = Path(settings.BASE_DIR, 'static/css/base.css').read_text(
            encoding='utf-8')

    def _get_html(self):
        resp = self.client.get('/', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_viewport_meta_no_cover(self):
        # N-27 改判后：viewport-fit=cover **不应**存在——
        # 它会让桌面浏览器误判可视区、还会让 iOS 把 Home Indicator 区域
        # 暴露到 layout 区内从而把按钮往下推
        html = self._get_html()
        self.assertNotIn('viewport-fit=cover', html)
        self.assertIn('width=device-width', html)

    def test_panel_actions_uses_max_fallback(self):
        # 关键：.panel-actions 必须用 max() 兜底，
        # 让 env() 返回 0 的安卓 WebView 也能避开底部 UI
        import re
        block = re.search(
            r'\.panel-actions\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(block, '.panel-actions 块不存在')
        body = block.group(0)
        self.assertIn('padding-bottom', body)
        self.assertIn('max(', body,
            '必须用 max() 兜底——单纯 env() 在安卓上返回 0 会让按钮被遮')
        self.assertIn('env(safe-area-inset-bottom', body)

    def test_panel_actions_fallback_at_least_72(self):
        # 兜底值必须 ≥ 72px（约 安卓导航 50 + 手势 24 - 2 的安全余量）
        # 72/64/48/32 都不允许——任何缩水都会被这条抓到
        import re
        block = re.search(
            r'\.panel-actions\s*\{[^}]*\}', self.css, re.DOTALL)
        body = block.group(0)
        # 抽出 max() 里的第一个参数（兜底值）
        m = re.search(r'max\(\s*(\d+)px', body)
        self.assertIsNotNone(m, 'max() 的第一个参数必须是 px 数字')
        v = int(m.group(1))
        self.assertGreaterEqual(v, 72,
            f'兜底值 {v}px 太小，安卓底部 UI 仍可能遮住按钮')

    def test_mobile_panel_width_shrunk(self):
        # 抽屉从 260px → 240px → 160px（v1.1.11→13→14）
        # 用户反馈"宽度还是太宽" + "按钮上下排列后宽度再减"
        # 250/200/180/170 都不允许——任何回退都会被这条抓到
        self.assertIn('width: 160px;', self.css)
        self.assertNotIn('width: 170px;', self.css)
        self.assertNotIn('width: 180px;', self.css)
        self.assertNotIn('width: 200px;', self.css)
        self.assertNotIn('width: 240px;', self.css)
        self.assertNotIn('width: 260px;', self.css)
        self.assertNotIn('width: 280px;', self.css)
        self.assertNotIn('width: 300px;', self.css)

    def test_panel_actions_vertical_layout(self):
        # v1.1.14: Theme/Lang 按钮竖向排列
        import re
        block = re.search(
            r'\.panel-actions\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(block)
        body = block.group(0)
        self.assertIn('flex-direction: column', body,
            'panel-actions 必须竖向排列（用户反馈按钮太大）')
        # 按钮 width:100% 铺满
        self.assertIn('width: 100%', self.css)

    def test_panel_buttons_same_alignment(self):
        # v1.1.15: 用户要求"按钮宽度一致，与上方菜单文字左对齐"
        # 关键：lang-switch 外层 div 不能有 padding（会双重缩进），
        # 两个按钮都要 padding:0 14px + height:36px + justify-content:flex-start
        # → "EN" / "Theme" 起点 = 14px，与 panel padding 14 一致
        import re
        # Theme 按钮
        theme = re.search(
            r'\.panel-actions\s+\.theme-toggle\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(theme, '.panel-actions .theme-toggle 块缺失')
        t = theme.group(0)
        self.assertIn('width: 100%', t)
        self.assertIn('height: 36px', t)
        self.assertIn('padding: 0 14px', t,
            'Theme 按钮必须 padding:0 14px，文字起点 14px 与菜单对齐')
        self.assertIn('justify-content: flex-start', t)
        # Lang 按钮外层
        lang_wrap = re.search(
            r'\.panel-actions\s+\.lang-switch\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(lang_wrap, '.panel-actions .lang-switch 块缺失')
        w = lang_wrap.group(0)
        self.assertIn('width: 100%', w)
        self.assertNotIn('padding: 0 14px', w,
            '外层 lang-switch 不能有 padding（会双重缩进，文字起点变 24px）')
        # Lang 按钮内层 button
        lang_btn = re.search(
            r'\.panel-actions\s+\.lang-switch-btn\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(lang_btn, '.panel-actions .lang-switch-btn 块缺失')
        lb = lang_btn.group(0)
        self.assertIn('width: 100%', lb)
        self.assertIn('height: 36px', lb,
            'Lang 按钮必须 height:36px 与 Theme 一致')
        self.assertIn('padding: 0 14px', lb,
            'Lang 按钮必须 padding:0 14px，文字起点与 Theme 一致')

    def test_admin_font_injection_uses_safe(self):
        # v1.1.14: admin 的 font_family_body 必须用 |safe 强制不转义，
        # 否则 Django 会把 'Inter' 里的单引号转成 &#x27; 实体，
        # 整个站点 fallback 到 system-ui → Times New Roman，
        # iOS 与安卓的字体观感就会"看起来不一样"。
        # （这是用户报告"安卓字体更好"的真正根因，不是设备差异。）
        from pathlib import Path
        import re
        base = Path(settings.BASE_DIR, 'templates', 'base.html').read_text(
            encoding='utf-8')
        block = re.search(
            r'<style>\s*/\* === Dynamic typography.*?</style>', base, re.DOTALL)
        self.assertIsNotNone(block, 'admin 注入 :root 块缺失')
        body = block.group(0)
        self.assertIn('font_family_body|safe', body,
            'admin font_family_body 必须用 |safe 否则单引号被 Django 转义')
        self.assertIn('font_family_heading|safe', body,
            'admin font_family_heading 必须用 |safe')

    def test_font_stack_has_chinese_fallback(self):
        # v1.1.14: 字体栈必须显式包含中文 fallback，
        # 否则 iOS 自动 fallback 到 SF Pro + PingFang SC 两套字体，
        # baseline 不对齐导致中英文混排"参差"（用户反馈"安卓字体更好"）
        # ——安卓 Roboto + Noto Sans CJK 设计上保持中英文字宽统一
        self.assertIn('--ff-body:', self.css)
        self.assertIn('PingFang SC', self.css,
            'iOS 必须显式声明 PingFang SC，否则中英文 baseline 错位')
        self.assertIn('Noto Sans CJK', self.css,
            '安卓/海外必须声明 Noto Sans CJK 兜底')
        self.assertIn('Microsoft YaHei', self.css,
            'Windows 必须声明微软雅黑兜底')
        # 还要有 -apple-system 才能让 iOS 显式识别 SF Pro
        self.assertIn('-apple-system', self.css)


class ResponsivePhase2Tests(TestCase):
    """阶段二（F7-F11 + N-4/N-6/N-11/N-16）防回归断言，v1.1.17。

    §15.2 实施清单的静态防御（§6.8.3 策略）：
      - N-11: 平板 hero min-height 必须 100svh + 100vh 成对
      - N-6:  Cookie 横幅 padding-bottom 用 max()+env() 兜底（N-27 改判后不用 viewport-fit）
      - F10:  .project-card-title 移动端允许换行
      - F11:  .reveal 初始隐藏必须带 html.js 前缀 + base.html 有 classList.add('js') 注入
      - F7:   断点收敛——源码中不得再出现 @media (max-width: 900px) / min-width: 1024px
      - F8:   detail-grid 折单列断点提升到 1024；detail-specs 移动端 1 列
      - F9:   products-banner 不再用 aspect-ratio:1920/442
      - N-4:  hero 桌面 <img> 有 1280w 档 srcset 且 1280 文件存在
      - N-16: .scroll-hint 全局样式在 base.css
    """

    def setUp(self):
        self.css = Path(settings.BASE_DIR, 'static/css/base.css').read_text(
            encoding='utf-8')
        self.base_html = Path(settings.BASE_DIR, 'templates/base.html').read_text(
            encoding='utf-8')

    # ---- N-11: 平板 hero svh ----
    def test_hero_tablet_uses_svh_with_vh_fallback(self):
        self.assertIn('min-height: 100vh; min-height: 100svh;', self.css,
            '平板 hero 必须 100svh（动态视口）+ 100vh 降级成对')

    # ---- N-6: Cookie 横幅 safe-area ----
    def test_cookie_banner_uses_env_fallback(self):
        import re
        self.assertRegex(self.base_html,
            r'padding-bottom:\s*max\(\s*20px,\s*calc\(\s*env\(safe-area-inset-bottom,\s*0px\)\s*\+\s*8px\)\s*\)',
            'Cookie 横幅 padding-bottom 必须 max()+env() 兜底（N-27 改判后的正确方向）')

    # ---- F10: 卡片标题换行 ----
    def test_project_card_title_wraps_on_mobile(self):
        import re
        block = re.search(
            r'@media \(max-width: 767px\) \{\s*\.project-card-title\s*\{[^}]*\}',
            self.css, re.DOTALL)
        self.assertIsNotNone(block, '767px 块内 .project-card-title 覆盖缺失')
        body = block.group(0)
        self.assertIn('white-space: normal', body,
            '移动端必须允许换行，否则长项目名被截成…（P1-8）')

    # ---- F11: reveal 渐进增强 ----
    def test_reveal_gated_by_html_js_class(self):
        # 前缀必须存在：无 JS 时 .reveal 不受 opacity:0 影响 → 内容可见
        self.assertRegex(self.css,
            r'html\.js \.reveal\s*\{[^}]*opacity:\s*0',
            '.reveal 初始隐藏必须带 html.js 前缀')
        self.assertIn("document.documentElement.classList.add('js')",
            self.base_html,
            'base.html 必须在 <head> 注入 html.js 类（渲染阻塞前）')

    def test_reveal_hidden_rule_has_no_bare_selector(self):
        # 裸 .reveal { opacity:0 } 会重新导致无 JS 白屏 —— 必须一律带 html.js 前缀。
        # 先把带前缀的替换掉再找裸规则，避免误报。
        import re
        # 替换串不能含 ".reveal"，否则 findall 会把替换后的文本再匹配回来
        stripped = re.sub(r'html\.js \.reveal', 'REVEAL_GATED', self.css)
        bare = re.findall(r'(?<![\w-])\.reveal\s*\{[^}]*opacity:\s*0', stripped)
        self.assertEqual(bare, [], f'发现裸 .reveal{{opacity:0}}: {bare}')

    # ---- F7: 断点收敛 ----
    def test_no_legacy_900px_breakpoint_in_source(self):
        import re
        paths = [Path(settings.BASE_DIR, 'static/css/base.css')]
        paths += Path(settings.BASE_DIR, 'templates').rglob('*.html')
        for path in paths:
            text = path.read_text(encoding='utf-8')
            hits = re.findall(r'@media\s*\(\s*max-width:\s*900px\s*\)', text)
            self.assertEqual(hits, [], f'{path}: 遗留 900px 断点 → {hits}')

    def test_breakpoints_use_canonical_values(self):
        """N-31 防回归：断点只允许白名单值（黑名单改白名单）。

        教训（v1.1.19）：原先只禁 900px，结果漏掉 8 处 `max-width:768px`——
        它与平板档 `min-width:768px` 在 768px 点上重叠，而 L1 全绿没暴露。
        「收敛/统一」类改造的断言必须枚举**所有**可能旧值与边界值，
        因此这里改用白名单：任何不在允许集合内的断点值一律失败。

        允许集合（F7 三档 + 两个有意例外）：
          max-width ∈ {767, 1024, 1199}
            - 767  手机档上界（F7）
            - 1024 F8 detail-grid 折单列的有意例外（≥1200 才双列）
            - 1199 平板档封闭区间上界 `@media (min-width:768px) and (max-width:1199px)`
          min-width ∈ {768, 1200}
        """
        import re
        allowed = {
            'max-width': {'767px', '1024px', '1199px'},
            'min-width': {'768px', '1200px'},
        }
        paths = [Path(settings.BASE_DIR, 'static/css/base.css')]
        paths += sorted(Path(settings.BASE_DIR, 'templates').rglob('*.html'))
        media_cond = re.compile(r'@media([^{]*)\{')
        width_val = re.compile(r'(max|min)-width:\s*(\d+px)')
        for path in paths:
            text = path.read_text(encoding='utf-8')
            for cond in media_cond.findall(text):
                for kind, value in width_val.findall(cond):
                    key = f'{kind}-width'
                    self.assertIn(
                        value, allowed[key],
                        f'{path}: 非标准断点 `@media{cond.strip()}` → '
                        f'{key}:{value}（允许 {sorted(allowed[key])}）')

    def test_no_legacy_1024px_grid_in_css(self):
        self.assertNotIn('@media (min-width: 1024px)', self.css)
        self.assertIn('@media (min-width: 1200px)', self.css)

    # ---- F8: 详情页折单列提前 ----
    def test_detail_grid_collapses_at_1024(self):
        pd = Path(settings.BASE_DIR,
                  'templates/product_detail.html').read_text(encoding='utf-8')
        ps = Path(settings.BASE_DIR,
                  'templates/product_series.html').read_text(encoding='utf-8')
        for name, text in [('product_detail', pd), ('product_series', ps)]:
            self.assertRegex(text,
                r'@media \(max-width: 1024px\)\s*\{[^}]*detail-grid\s*\{[^}]*grid-template-columns:\s*1fr',
                f'{name}.html: detail-grid 折单列必须提升到 1024px 断点')

    def test_detail_specs_two_columns_on_mobile(self):
        """F8 修正（2026-09-10 真机复核发现）：detail-specs 移动端恢复 2 列。

        原 F8 当初因 1.35rem 字号过大把 mobile 改 1 列（1xN 堆叠），
        用户反馈 4 项参数在 390px 视口按 2x2 更紧凑、6 项 2x3 最多 3 行。
        防御性双向断言：必须有 2 列，且不得退回 1 列。
        """
        pd = Path(settings.BASE_DIR,
                  'templates/product_detail.html').read_text(encoding='utf-8')
        import re
        # 767px 块内 .detail-specs 之前可能还有内层块（如 .sidebar-layout），需允许一层嵌套
        block = re.search(
            r'@media \(max-width: 767px\) \{(?:[^{}]|\{[^{}]*\})*\.detail-specs\s*\{[^}]*\}',
            pd, re.DOTALL)
        self.assertIsNotNone(block, '767px 块内 .detail-specs 覆盖缺失')
        matched = block.group(0)
        self.assertIn('repeat(2, 1fr)', matched,
                      'detail-specs 移动端必须 2 列（用户偏好 2x3 紧凑布局）')
        # 抓 1 列回归：先把 repeat(2, 1fr) 摘除，再检查裸 1fr
        stripped = matched.replace('repeat(2, 1fr)', '')
        self.assertNotIn('grid-template-columns: 1fr', stripped,
                         'detail-specs 不得退回 1 列布局（F8-修正规则）')

    # ---- F9: banner 自适应 ----
    def test_products_banner_no_hard_aspect_ratio(self):
        products = Path(settings.BASE_DIR,
                        'templates/products.html').read_text(encoding='utf-8')
        self.assertNotIn('aspect-ratio: 1920 / 442', products)
        self.assertIn('min-height: 120px', products)
        import re
        self.assertRegex(products,
            r'@media \(max-width: 767px\)\s*\{[^}]*products-banner\s*\{[^}]*min-height',
            '移动端 products-banner 必须有 min-height 收口')

    # ---- N-4: hero 桌面分档 ----
    def test_hero_img_has_1280_srcset(self):
        home = Path(settings.BASE_DIR,
                    'templates/home.html').read_text(encoding='utf-8')
        for i in (1, 2, 3):
            f = Path(settings.BASE_DIR, 'static/images',
                     f'hero-main-{i}-1280.webp')
            self.assertTrue(f.is_file(),
                            f'hero-main-{i}-1280.webp 不存在（N-4 桌面分档）')
            self.assertIn(f'hero-main-{i}-1280.webp', home,
                          f'home.html 第 {i} 张 hero 缺 1280w srcset 档')
        # sizes 与 F7 三档一致
        self.assertIn('sizes="(min-width: 1200px) 1920px, 1280px"', home)

    # ---- N-16: 滑动提示全局化 ----
    def test_scroll_hint_global_in_base_css(self):
        import re
        block = re.search(r'\.scroll-hint\s*\{[^}]*\}', self.css, re.DOTALL)
        self.assertIsNotNone(block, 'base.css 必须有全局 .scroll-hint')
        body = block.group(0)
        self.assertIn('text-transform: uppercase', body)
        # product_detail 只允许保留「显形」规则（display:block，≤767px），
        # 不得再内联「样式」定义（font-family/margin 等）→ 防止两处漂移
        pd = Path(settings.BASE_DIR,
                  'templates/product_detail.html').read_text(encoding='utf-8')
        hint = re.search(r'\.scroll-hint\s*\{[^}]*\}', pd, re.DOTALL)
        if hint is not None:
            self.assertNotIn('font-family', hint.group(0),
                'product_detail.html 只应保留 display 显形规则，样式定义已全局化到 base.css')
            self.assertIn('display: block', hint.group(0))


class StaticIndexBuildTests(unittest.TestCase):
    """构建期静态索引生成器（pages/static_index.py）—— 供 Vercel 函数包瘦身使用。

    背景：static/ 与 staticfiles/ 被 vercel.json 的 excludeFiles 排除出 Python
    函数包（~118MB 的图片/PDF 改由边缘 CDN 服务），运行时磁盘上不再有这两个目录，
    图片路径解析改由构建期生成的索引兜底。
    """

    def test_build_index_groups_files_by_directory(self):
        from pages.static_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'images', 'products', 'demo').mkdir(parents=True)
            Path(tmp, 'images', 'products', 'demo', 'demo-01.webp').write_bytes(b'x')
            Path(tmp, 'images', 'products', 'demo', 'demo-02.webp').write_bytes(b'x')
            Path(tmp, 'css').mkdir()
            Path(tmp, 'css', 'base.css').write_text('body{}', encoding='utf-8')
            Path(tmp, '.DS_Store').write_bytes(b'junk')

            index = build_index(tmp)
            self.assertEqual(index['dirs']['images/products/demo'],
                             ['demo-01.webp', 'demo-02.webp'])
            self.assertEqual(index['dirs']['css'], ['base.css'])
            self.assertNotIn('.DS_Store', index['dirs'].get('', []),
                             '系统垃圾文件不应进入索引')

    def test_build_index_missing_root_returns_empty(self):
        from pages.static_index import build_index
        self.assertEqual(build_index(str(Path(tempfile.gettempdir(), 'no-such-dir-xyz'))),
                         {'dirs': {}})

    def test_rendered_module_is_valid_python(self):
        from pages.static_index import render_module
        src = render_module({'dirs': {'images/products/demo': ['a.webp']}})
        ns = {}
        exec(compile(src, '<static_index_data>', 'exec'), ns)
        self.assertEqual(ns['STATIC_INDEX']['dirs']['images/products/demo'], ['a.webp'])


class StaticIndexFallbackTests(SimpleTestCase):
    """static/ 不在磁盘上时（Vercel 函数包），图片解析必须仍然可用。"""

    FAKE_INDEX = {'dirs': {
        'images/products/demo': ['demo-01.webp', 'demo-bar-1.webp'],
        'images/projects/demo': ['cover.webp', 'gallery-01.webp'],
        'files': ['brochure.pdf'],
    }}

    def setUp(self):
        from pages.views import utils
        self.utils = utils
        self._saved = (utils._static_file_set, utils._static_index)
        utils._static_file_set = None
        utils._static_index = self.FAKE_INDEX
        utils._dir_listing_cache.clear()
        utils._PRODUCT_DIR_IMAGE_CACHE.clear()
        self._missing = str(Path(tempfile.gettempdir(), 'solarone-no-static-xyz'))
        self._override = override_settings(STATICFILES_DIRS=[], STATIC_ROOT=self._missing)
        self._override.enable()
        self.addCleanup(self._restore)

    def _restore(self):
        self._override.disable()
        self.utils._static_file_set, self.utils._static_index = self._saved
        self.utils._dir_listing_cache.clear()
        self.utils._PRODUCT_DIR_IMAGE_CACHE.clear()

    def test_find_static_uses_index_when_disk_is_absent(self):
        self.assertFalse(Path(self._missing).is_dir())
        self.assertTrue(self.utils._find_static('images/products/demo/demo-01.webp'))
        self.assertTrue(self.utils._find_static('files/brochure.pdf'))
        self.assertFalse(self.utils._find_static('images/products/demo/nope.webp'))

    def test_list_static_dir_uses_index(self):
        self.assertEqual(self.utils._list_static_dir('images/projects/demo'),
                         {'cover.webp', 'gallery-01.webp'})

    def test_product_image_url_resolves_without_disk(self):
        product = SimpleNamespace(
            slug='demo',
            image=SimpleNamespace(name='products/demo-01.webp'),
        )
        url = _strip_static_hash(self.utils._product_image_url(product, 'image'))
        self.assertIn('/static/images/products/demo/demo-01.webp', url)

    def test_product_dir_images_prefers_non_banner_card_image(self):
        # DB 里存的是 banner 图 → 卡片位应改用同目录非 banner 图（索引提供目录列表）
        product = SimpleNamespace(
            slug='demo',
            image=SimpleNamespace(name='products/demo-bar-1.webp'),
        )
        url = _strip_static_hash(self.utils._product_image_url(product, 'image'))
        self.assertIn('/static/images/products/demo/demo-01.webp', url)
        self.assertNotIn('demo-bar-1.webp', url)


class GeneratedStaticIndexCoverageTests(SimpleTestCase):
    """若构建期索引存在（build.sh / CI 会生成），必须覆盖 static/ 下全部资源。

    防止索引过期或 collectstatic 范围变化后，线上出现「图片解析不到」的静默回归。
    """

    def _load(self):
        try:
            from pages.static_index_data import STATIC_INDEX
        except Exception:
            self.skipTest('pages/static_index_data.py 未生成（本地/CI 未跑构建步骤）')
        return STATIC_INDEX

    def test_index_covers_every_committed_static_file(self):
        index = self._load()
        indexed = set()
        for rel_dir, names in (index.get('dirs') or {}).items():
            prefix = (rel_dir + '/') if rel_dir else ''
            indexed.update(prefix + n for n in names)

        static_dir = Path(settings.BASE_DIR, 'static')
        missing = []
        for path in static_dir.rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(static_dir).as_posix()
            if rel.startswith('admin/'):
                continue
            if rel not in indexed:
                missing.append(rel)
        self.assertEqual(missing, [], f'索引遗漏了 {len(missing)} 个 static/ 文件')

