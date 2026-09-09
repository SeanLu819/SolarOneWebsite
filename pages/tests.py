from pathlib import Path
from types import SimpleNamespace
import unittest

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from pages.admin import ProjectAdmin
from pages.views import _product_image_url, _get_project_detail_from_json, _enrich_project
from django.utils.translation import activate


# 修改后
class ProductImagePathResolutionTests(SimpleTestCase):
    def test_static_fallback_finds_file_in_slug_subdirectory(self):
        """DB stores old flat path, but assets now live in slug/ subdirectory.
        The resolver should find the real file even though DB path differs."""
        product = SimpleNamespace(
            slug='fl4m',
            image=SimpleNamespace(name='products/fl4m-01.webp'),
        )
        url = _product_image_url(product, 'image')
        self.assertIn('/static/images/products/fl4m/fl4m-01.webp', url)  # ← 实际位置

    def test_static_fallback_prefers_db_relative_canonical_path(self):
        product = SimpleNamespace(
            slug='rt590fl-s',
            banner_image=SimpleNamespace(name='products/vsp/vsp-bar-1.webp'),
        )

        url = _product_image_url(product, 'banner_image')

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
