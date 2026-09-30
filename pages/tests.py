import ast
import gettext
import inspect
import json
import re
import shutil
import sys
import tempfile
import types
from html import unescape as html_unescape
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from django.conf import settings
from django.contrib import admin as dj_admin
from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, TestCase, RequestFactory, override_settings
from django.urls import reverse

from pages.admin import ProjectAdmin
from pages.admin.mixins import CacheClearMixin
from pages.admin.news import NewsArticleAdmin
from pages.admin.product import ProductAdmin
from pages.admin.products_page import ProductsPageCardAdmin
from pages.admin.siteconfig import SiteConfigAdmin
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

    def test_gallery_legacy_path_prefers_slug_dir_over_stale_static_root_copy(self):
        """2026-09-26 故障回归：DB 里的 legacy 图集路径 products/gallery/x.webp
        被规范化成 images/products/gallery/x.webp 并因 staticfiles/（STATIC_ROOT，
        本地 dev 不对外服务）里还留着旧拷贝而在候选排序里抢先命中 → 浏览器
        404。slug 目录里明明有同名文件时必须优先命中 slug 目录。"""
        from pages.views.utils import _dict_product_image_url

        legacy = 'products/gallery/rt410fl-s-01.webp'
        expected = '/static/images/products/rt410-series/rt410fl-s-01.webp'

        # DB 分支（ProductImage.image FieldFile 形状）
        product = SimpleNamespace(
            slug='rt410-series',
            image=SimpleNamespace(name=legacy),
        )
        self.assertIn(expected, _strip_static_hash(_product_image_url(product, 'image')))

        # seed/dict 分支（plain str 路径形状）
        self.assertIn(expected, _strip_static_hash(_dict_product_image_url(legacy, 'rt410-series')))


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


@override_settings(
    IS_VERCEL=True,
    SECURE_SSL_REDIRECT=True,
    SECURE_HSTS_SECONDS=31536000,
    SESSION_COOKIE_SECURE=True,
    CSRF_COOKIE_SECURE=True,
)
class VercelSecureCookieTests(SimpleTestCase):
    """HTTPS-only cookies / HSTS are enforced on Vercel.

    Previously skipped locally via ``@unittest.skipUnless(settings.IS_VERCEL)``;
    now we force the production flag set with ``override_settings`` so the
    assertions also run in the local / CI test run (D2 / v1.5.9). The secure
    cookie booleans are overridden explicitly because they are derived from
    ``IS_VERCEL`` at settings-import time and do not recompute on override.
    """

    def test_secure_cookie_flags_enabled(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)

    def test_plain_http_request_redirects_to_https(self):
        resp = self.client.get('/definitely-not-a-real-page/', secure=False)
        self.assertIn(resp.status_code, (301, 302))
        self.assertTrue(resp.headers.get('Location', '').startswith('https://'))


class ContentSecurityPolicyHeaderTests(SimpleTestCase):
    """E1 (v1.5.9): every response must carry a Content-Security-Policy header.

    v1.6.2: script-src must use a per-request nonce and drop 'unsafe-inline'.
    """

    # The home page renders ``get_common_context()`` which reads ``SiteConfig``
    # from the DB; allow DB access for this otherwise-DB-free test (D2 / v1.5.9).
    databases = {'default'}

    def test_home_page_has_csp_header(self):
        resp = self.client.get('/')
        self.assertIn('Content-Security-Policy', resp.headers)

    def test_csp_policy_is_configurable(self):
        self.assertTrue(getattr(settings, 'CONTENT_SECURITY_POLICY', ''))

    def test_script_src_uses_nonce_and_drops_unsafe_inline(self):
        resp = self.client.get('/')
        csp = resp.headers['Content-Security-Policy']
        self.assertIn("'nonce-", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        # nonce is 22 chars (secrets.token_urlsafe(16)) — assert a real value
        m = re.search(r"'nonce-([^']+)'", csp)
        self.assertIsNotNone(m)
        self.assertGreater(len(m.group(1)), 8)

    def test_inline_script_tags_carry_matching_nonce(self):
        resp = self.client.get('/')
        csp = resp.headers['Content-Security-Policy']
        nonce = re.search(r"'nonce-([^']+)'", csp).group(1)
        content = resp.content.decode('utf-8')
        # Collect every inline <script> (no external src) open tag.
        inline = [t for t in re.findall(r'<script\b[^>]*>', content) if 'src=' not in t]
        self.assertGreater(len(inline), 0, 'no inline <script> tags found to verify')
        # Every inline <script> must carry the matching nonce attribute.
        for tag in inline:
            self.assertIn("nonce=\"%s\"" % nonce, tag,
                          "inline script missing matching nonce: %s" % tag)


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
        resp = self.client.get('/sitemap.xml', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('https://www.solaronelighting.com', content)
        self.assertNotIn('evil.vercel.app', content)

    def test_robots_txt_uses_fixed_origin(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn(
            'Sitemap: https://www.solaronelighting.com/sitemap.xml', content)
        self.assertNotIn('evil.vercel.app', content)

    def test_home_canonical_and_jsonld_use_fixed_origin(self):
        resp = self.client.get('/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('evil.vercel.app', content)
        self.assertIn('https://www.solaronelighting.com', content)

    def test_disallowed_host_rejected(self):
        # #4 (v1.6.1): a host outside ALLOWED_HOSTS (e.g. a spoofed *.vercel.app)
        # must be rejected with 400, never served with a leaked canonical URL.
        resp = self.client.get('/', HTTP_HOST='evil.vercel.app')
        self.assertEqual(resp.status_code, 400)


class AnalyticsRenderingTests(TestCase):
    """M2 (P1c) — GA4 snippet + GSC meta render only when configured."""

    def _home(self):
        return self.client.get('/').content.decode()

    def test_no_analytics_when_unset(self):
        content = self._home()
        self.assertNotIn('googletagmanager.com/gtag/js', content)
        self.assertNotIn('google-site-verification', content)

    @override_settings(GA4_MEASUREMENT_ID='G-TEST12345')
    def test_ga4_snippet_renders_with_id(self):
        content = self._home()
        self.assertIn('googletagmanager.com/gtag/js?id=G-TEST12345', content)
        self.assertIn("gtag('config', 'G-TEST12345')", content)
        # the inline config script must carry the CSP nonce
        self.assertIn('nonce=', content)

    @override_settings(GSC_VERIFICATION_CODE='abc123verify')
    def test_gsc_verification_meta_renders(self):
        content = self._home()
        self.assertIn('name="google-site-verification" content="abc123verify"', content)


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


class ProductSeriesRedirectTests(TestCase):
    """P1b — /products/series/<slug>/ must 301 to /products/<slug>/."""

    def test_series_url_redirects_to_product_detail(self):
        resp = self.client.get('/products/series/fl1m/')
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], '/products/fl1m/')

    def test_series_url_redirect_preserves_language_prefix(self):
        # A French request must keep the /fr/ prefix on the redirect target,
        # because the view runs inside i18n_patterns. Django's redirect() returns
        # a host-relative Location, so the prefix shows up as /fr/products/...
        resp = self.client.get('/fr/products/series/fl1m/')
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], '/fr/products/fl1m/')


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


class TemplateCommentHygieneTests(TestCase):
    """`{# #}` 只注释**单行** —— 跨行写法会把注释原样输出成可见文本。

    事故（v1.5.2 引入，v1.5.6 发现）：products.html 的 LCP banner 注释写了 3 行，
    Django lexer 不报错，注释原文进入渲染结果——落进 `.products-banner` 成为**流内**
    inline 文本（其余子元素全是 absolute），后果有二：
      1. 泄漏可读文本（屏幕阅读器会念，且图片加载失败时直接可见）；
      2. 把容器撑到 179.2px（390px 视口），掩盖了「高度只由 CSS 决定」的真实契约，
         让 F9 的 min-height 地板看起来「没问题」。
    双向断言：静态扫模板 + 渲染结果不得含 `{#`。
    """

    def test_no_multiline_hash_comment_in_templates(self):
        for path in sorted(Path(settings.BASE_DIR, 'templates').rglob('*.html')):
            text = path.read_text(encoding='utf-8')
            for m in re.finditer(r'\{#', text):
                end = text.find('#}', m.start())
                self.assertNotEqual(
                    end, -1, f'{path.name}: 未闭合的 `{{#`（off={m.start()}）')
                seg = text[m.start():end]
                line = text[:m.start()].count('\n') + 1
                self.assertNotIn(
                    '\n', seg,
                    f'{path.name}:{line} 跨行 `{{# #}}` 会原样输出为可见文本，'
                    f'请改用 `{{% comment %}}...{{% endcomment %}}`')

    def test_rendered_pages_leak_no_template_comment(self):
        for url in ('/', '/products/', '/about/', '/contact/', '/projects/'):
            html = self.client.get(url).content.decode('utf-8')
            self.assertNotIn('{#', html, f'{url} 渲染结果里出现模板注释原文')

    def test_no_external_editor_injected_attributes(self):
        # 外部可视化编辑器会向模板元素注入 data-page-node-id 等噪声属性，
        # 仅膨胀 HTML、无运行时用途（v1.5.8 已将 base.html 的 150 处全清）。
        # 双向断言：① 所有模板源码不含该属性；② 渲染结果也不含。
        tpl_dir = Path(settings.BASE_DIR, 'templates')
        for path in sorted(tpl_dir.rglob('*.html')):
            text = path.read_text(encoding='utf-8')
            self.assertEqual(
                text.count('data-page-node-id'), 0,
                f'{path.name} 仍存在 data-page-node-id（外部编辑器回填？）')
        for url in ('/', '/products/', '/about/', '/contact/', '/projects/'):
            html = self.client.get(url).content.decode('utf-8')
            self.assertNotIn(
                'data-page-node-id', html,
                f'{url} 渲染结果含 data-page-node-id')


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

    def test_runtime_notify_failure_shows_honest_error(self):
        # On Vercel (IS_RUNTIME), a saved-but-undelivered submission (notify set
        # but SMTP send fails) must surface an HONEST error to the visitor — not
        # a fake "success" that hides the lost lead (incident 2026-09-13).
        from unittest.mock import patch
        with override_settings(IS_RUNTIME=True, CONTACT_NOTIFY_EMAIL='sales@solarone.com'), \
                patch('django.core.mail.send_mail', side_effect=Exception('SMTP down')):
            resp = self.client.post(reverse('contact'), {
                'name': 'Real Person',
                'email': 'real@customer.example',
                'message': 'Please quote the FL4M series.',
            })
        self.assertEqual(resp.status_code, 200)
        from pages.models import ContactMessage
        self.assertTrue(
            ContactMessage.objects.filter(email='real@customer.example').exists(),
            'submission must still be saved to the DB')
        content = resp.content.decode()
        self.assertIn('could not deliver', content,
                      'visitor must see an honest failure, never a fake success')


class ContactPersistenceCheckTests(TestCase):
    """Production guard: contact submissions must have a durable delivery channel.

    On Vercel the default DB is the ephemeral /tmp SQLite (lost on redeploy). The
    only durable channel is email (CONTACT_NOTIFY_EMAIL + SMTP). If neither is
    configured, check_contact_persistence must warn so the loss is caught in CI
    / `manage.py check`, not discovered via silent data loss (incident 2026-09-13).
    """

    def _run(self, *, vercel, db_url, notify, smtp_user='', smtp_pass=''):
        from pages.checks import check_contact_persistence
        with mock.patch.dict('os.environ', {'DATABASE_URL': db_url}), \
                override_settings(IS_VERCEL=vercel, CONTACT_NOTIFY_EMAIL=notify,
                                  EMAIL_HOST_USER=smtp_user, EMAIL_HOST_PASSWORD=smtp_pass):
            return check_contact_persistence(None)

    def test_vercel_ephemeral_db_without_email_warns(self):
        errors = self._run(vercel=True, db_url='sqlite:////tmp/db.sqlite3', notify='')
        self.assertEqual(len(errors), 1, 'must warn when Vercel + /tmp DB + no notify email')
        self.assertEqual(errors[0].id, 'pages.W001')

    def test_vercel_ephemeral_db_notify_without_smtp_warns(self):
        # Half-config: notify set but no SMTP creds => locmem swallows the mail
        # and the lead is still lost on redeploy. This used to be missed.
        errors = self._run(vercel=True, db_url='sqlite:////tmp/db.sqlite3',
                           notify='sales@solarone.com', smtp_user='', smtp_pass='')
        self.assertEqual(len(errors), 1,
                         'notify WITHOUT smtp creds must still warn (half-config)')
        self.assertEqual(errors[0].id, 'pages.W001')

    def test_vercel_ephemeral_db_notify_with_smtp_ok(self):
        errors = self._run(vercel=True, db_url='sqlite:////tmp/db.sqlite3',
                           notify='sales@solarone.com', smtp_user='u', smtp_pass='p')
        self.assertEqual(errors, [], 'notify + smtp creds => durable channel exists')

    def test_vercel_persistent_db_without_email_ok(self):
        errors = self._run(vercel=True, db_url='postgres://u:p@neon/db', notify='')
        self.assertEqual(errors, [], 'persistent DB => durable even without email')

    def test_local_dev_not_flagged(self):
        errors = self._run(vercel=False, db_url='', notify='')
        self.assertEqual(errors, [], 'non-Vercel must never warn')


class RuntimeSchemaBootstrapTests(TestCase):
    """Cold-start guard: on Vercel ephemeral /tmp SQLite, ``api.index`` must
    create all tables at runtime. build.sh skips migrate in the stateless seed
    path, so a fresh serverless instance boots with an EMPTY /tmp SQLite and
    ``ContactMessage.objects.create()`` raises OperationalError "no such table"
    -> the visitor sees "Sorry, we could not save your message" (prod
    incident 2026-09-26).

    This test simulates that cold-start empty-DB scenario with a throwaway
    SQLite file, calls the encapsulated ``_ensure_runtime_schema()`` function,
    and asserts (a) the ``pages_contactmessage`` table now exists and (b) a
    contact submission can be written. No network, no real Vercel environment.
    """

    def test_ensure_runtime_schema_creates_contact_table(self):
        # Lazy import so the heavy WSGI bootstrap only runs for this test path.
        import os
        from api.index import _ensure_runtime_schema
        from django.db import connections
        from django.test.utils import override_settings

        # 1) Simulate a FRESH, EMPTY serverless instance DB (cold start).
        tmp_dir = tempfile.mkdtemp(prefix='solarone-coldstart-')
        tmp_db = os.path.join(tmp_dir, 'db.sqlite3')
        self.assertFalse(
            os.path.exists(tmp_db),
            'cold-start DB must not exist yet (no tables)')

        new_databases = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': tmp_db,
            }
        }
        try:
            with override_settings(
                IS_VERCEL=True,
                DATABASE_URL=f'sqlite:///{tmp_db}',
                DATABASES=new_databases,
            ):
                # override_settings(DATABASES=...) closes the cached connection
                # so the next access reopens against the empty temp DB.
                connections.close_all()
                ok = _ensure_runtime_schema()
                self.assertTrue(
                    ok, 'runtime schema bootstrap must succeed on empty DB')

                # 2) The contact table must now physically exist in the cold DB.
                with connections['default'].cursor() as cur:
                    cur.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='pages_contactmessage'")
                    self.assertIsNotNone(
                        cur.fetchone(),
                        'pages_contactmessage table must exist after bootstrap')

                # 3) A contact submission write must succeed (the prod failure
                #    path) and be queryable back.
                from pages.models import ContactMessage
                msg = ContactMessage.objects.create(
                    name='Real Person',
                    email='real@customer.example',
                    message='Please quote the FL4M series.',
                )
                self.assertEqual(msg.email, 'real@customer.example')
                self.assertEqual(
                    ContactMessage.objects.filter(
                        email='real@customer.example').count(), 1)
        finally:
            # Clean up the temp DB so it is never left behind in CI.
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_ensure_runtime_schema_failure_path_returns_false(self):
        """Negative: if migrate blows up, the bootstrap must return False and
        must NEVER raise (the app must keep booting)."""
        import api.index

        # call_command is imported *locally* inside _ensure_runtime_schema's
        # try block, so we patch the real module attribute it binds to.
        with mock.patch(
            'django.core.management.call_command',
            side_effect=RuntimeError('simulated migrate failure'),
        ):
            # Must not raise out of this call.
            ok = api.index._ensure_runtime_schema()

        self.assertFalse(
            ok, 'bootstrap must return False when migrate raises')

    def test_guard_skips_managed_db_no_migrate(self):
        """Negative: the production trigger (api/index.py L49-51) must NOT run
        migrate against a managed DB (Neon/Supabase/Postgres). It only fires
        when IS_VERCEL is truthy AND DATABASE_URL contains '/tmp/'.

        We mirror the exact guard expression against the module's IS_VERCEL
        attribute and the live DATABASE_URL env, so a future change to the
        guard condition is caught here. (A behavioral reload of the WSGI
        module is avoided — it re-runs the full bootstrap and is unsafe in a
        unit test.)
        """
        import os

        import api.index

        # Control: a genuine /tmp URL MUST trigger (proves the gate is real).
        with mock.patch.object(api.index, 'IS_VERCEL', True), \
                mock.patch.dict('os.environ',
                                {'DATABASE_URL': 'sqlite:////tmp/db.sqlite3'}):
            self.assertTrue(
                api.index.IS_VERCEL and
                '/tmp/' in os.environ.get('DATABASE_URL', ''),
                'control: /tmp URL must trigger the guard')

        # Managed postgres (no /tmp) must NOT trigger.
        with mock.patch.object(api.index, 'IS_VERCEL', True), \
                mock.patch.dict('os.environ',
                                {'DATABASE_URL': 'postgres://u:p@neon.tech/db'}):
            self.assertFalse(
                api.index.IS_VERCEL and
                '/tmp/' in os.environ.get('DATABASE_URL', ''),
                'managed postgres URL must NOT trigger runtime migrate')

        # neon://-style URL must NOT trigger either.
        with mock.patch.object(api.index, 'IS_VERCEL', True), \
                mock.patch.dict('os.environ',
                                {'DATABASE_URL': 'neon://user:pass@ep-xxx/db'}):
            self.assertFalse(
                api.index.IS_VERCEL and
                '/tmp/' in os.environ.get('DATABASE_URL', ''),
                'neon:// URL must NOT trigger runtime migrate')


class ResponsiveNavTests(TestCase):
    """阶段一 F1' — 导航单一数据源 + 移动端功能不丢失（渲染 DOM 契约，§6.2/§8.5）。

    断言的是"渲染出的 DOM"而非 CSS 字符串，因此能捕获：
    1) 汉堡/nav-links/面板结构的回归；
    2) 桌面与移动面板导航不同步（双份数据源）；
    3) 多行 `{# #}` 未闭合注释泄漏到 HTML（Django 的 silent 行为）。
    """

    def _home(self):
        resp = self.client.get('/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_hamburger_present_with_aria(self):
        html = self._home()
        self.assertIn('id="hamburgerBtn"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn('aria-controls="mobilePanel"', html)

    def test_nav_links_is_ul(self):
        # 用正则匹配标签而非精确串：即便未来模板标签内多出属性（如外部编辑器
        # 回填 data-page-node-id，已在 v1.5.8 清空但保留正则以防复发），精确串也会失配。

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
        resp = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, f'{url} must render')
        return resp.content.decode()

    # ---- N-1: 输入框 font-size >= 16px（iOS 聚焦自动放大且不回弹） ----
    def test_n1_form_inputs_16px(self):
        # Contact 控件已统一使用语义 class；16px 由 base.css 集中提供。
        # 渲染 DOM 与样式源都必须保留该行为契约。
        html = self._get('/contact/')
        form = html.split('id="contactForm"', 1)[1].split('</form>', 1)[0]
        self.assertNotIn('font-size: 0.9rem', form)
        self.assertIn('class="contact-form-control', form)
        self.assertRegex(
            self.css,
            r'\.contact-form-control\s*\{[^}]*font-size:\s*16px',
            'Contact 表单控件必须保持 iOS 防自动放大的 16px 字号',
        )
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

    # ---- N-5 / #2 (v1.6.1): self-hosted fonts, no third-party request ----
    def test_n5_fonts_self_hosted_no_third_party(self):
        html = self._get('/')
        # Self-hosted font CSS is linked from our own origin (static/css/fonts.css).
        self.assertIn("static/css/fonts.css", html)
        # No third-party Google Fonts request may remain (#2, v1.6.1):
        # fonts are committed under static/fonts/ and served by the Vercel CDN.
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("fonts.gstatic.com", html)

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
        # /news/ 不在此列：v1.6.3 新闻页改版为顶部 chips + 卡片网格，
        # 不再使用 sidebar 抽屉（chips 契约归 NewsChipsAndCopyTests 管）。
        for url in ('/products/', '/projects/'):
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
        resp = self.client.get('/', HTTP_HOST='localhost')
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

    2026-09-17（Ponytail B6）：模板中 `.sidebar-layout` 的 4 份重复副本已合并
    进 base.css，断言语义随之从「模板里含该声明」改为「base.css 在 767px 断点
    提供该声明」+「模板不得再声明」——后者反而更强（新增了禁止重复声明的守卫）。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = Path(settings.BASE_DIR, 'static/css/base.css').read_text(
            encoding='utf-8')
        # rglob, not glob: after the DRY consolidation most markup lives in
        # templates/includes/, and a non-recursive scan cannot see overrides
        # placed there (found by independent QA as a blind spot).
        root = Path(settings.BASE_DIR, 'templates')
        cls.templates = {
            str(p.relative_to(root)).replace('\\', '/'): p.read_text(
                encoding='utf-8')
            for p in root.rglob('*.html')
        }

    def test_grid_items_have_min_width_zero(self):
        # N-25 根本解：grid item 的 min-width:auto 是 blowout 的传导路径，
        # 归零后无论轨道写成 1fr 还是 minmax(0,1fr) 都不会撑破页面
        self.assertIn('.sidebar-layout > *', self.css)
        self.assertIn('min-width: 0;', self.css)

    # `1fr` and `minmax(auto, 1fr)` are the same thing — the N-21 anti-pattern.
    # Whitespace-tolerant, and deliberately not anchored to a selector, so it
    # cannot be walked around by rewriting the selector list.
    _BARE_TRACK_RE = re.compile(
        r'grid-template-columns\s*:\s*'
        r'(?:1fr|minmax\(\s*auto\s*,\s*1fr\s*\))\s*!important')

    # Innermost CSS rules only: neither group can contain a brace, so an
    # enclosing @media block is stepped over and `.a, .b { … }` is captured as
    # one (selector, body) pair — which is what makes the comma/compound case
    # detectable at all.
    _CSS_RULE_RE = re.compile(r'([^{}]*?)\{([^{}]*)\}', re.S)

    def test_no_bare_1fr_sidebar_override(self):
        """Templates must not reintroduce the `1fr !important` anti-pattern.

        `1fr` desugars to `minmax(auto, 1fr)`, whose min track is the content's
        min-content width — the engine behind the N-25 grid blowout. Matched
        structurally so that `minmax(auto, 1fr)` and any selector shape are
        both caught (independent QA showed a literal-substring check missed
        `.sidebar-layout, .decoy { grid-template-columns: minmax(auto, 1fr) !important }`).
        """
        for name, src in self.templates.items():
            hit = self._BARE_TRACK_RE.search(src)
            self.assertIsNone(
                hit,
                f'{name} 使用了 `{hit.group(0) if hit else ""}`：`1fr` 等价于 '
                f'minmax(auto, 1fr)，会反杀 N-21/N-25 并重新触发 grid blowout')

    def test_sidebar_uses_minmax_zero(self):
        """N-25 root fix must exist in base.css — its single source of truth.

        Each sidebar template used to carry its own copy of
        `.sidebar-layout { grid-template-columns: minmax(0, 1fr) !important }`.
        Those copies were consolidated into base.css (Ponytail B6), so asserting
        them in the templates would now forbid the consolidation while proving
        less. What matters is that the declaration exists *inside the mobile
        breakpoint* — a declaration parked at the wrong breakpoint is just as
        broken as a missing one.
        """
        blocks = re.findall(r'@media\s*\(max-width:\s*767px\)\s*\{(.*?)\n  \}',
                            self.css, re.S)
        self.assertTrue(blocks, 'base.css 缺少 max-width:767px 断点块')
        self.assertTrue(
            any('.sidebar-layout' in b and
                'grid-template-columns: minmax(0, 1fr) !important' in b
                for b in blocks),
            'base.css 的 767px 断点块里没有 .sidebar-layout 的 minmax(0,1fr) '
            '修复（N-25）')

    def test_sidebar_templates_do_not_redeclare_grid_template(self):
        """No template may declare grid-template-columns for .sidebar-layout.

        A template-level declaration loads *after* base.css, so re-adding one
        silently defeats N-21/N-25 again — the exact failure mode this suite
        exists to catch.

        Deliberately structural rather than a substring / anchored-regex check:
        independent QA demonstrated that `.sidebar-layout, .decoy { … }` (comma
        selector) and an override inside `templates/includes/` both slipped past
        the first version of this guard while it reported green.
        """
        offenders = []
        for name, src in self.templates.items():
            for selector, body in self._CSS_RULE_RE.findall(src):
                if '.sidebar-layout' in selector and 'grid-template-columns' in body:
                    offenders.append(
                        (name, ' '.join(selector.split())))
        self.assertEqual(
            offenders, [],
            '模板重新声明了 .sidebar-layout 的 grid-template-columns，会覆盖 '
            f'base.css 的 N-25 修复（应只保留 base.css 一处）：{offenders}')

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
        resp = self.client.get('/', HTTP_HOST='localhost')
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
            r'<style[^>]*>\s*/\* === Dynamic typography.*?</style>', base, re.DOTALL)
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
      - F9:   products-banner 必须 aspect-ratio:1920/442 与 min-height 地板并存
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

        允许集合（F7 三档 + 三个有意例外）：
          max-width ∈ {767, 1024, 1199}
            - 767  手机档上界（F7）
            - 1024 F8 detail-grid 折单列的有意例外（≥1200 才双列）
            - 1024 亦是导航平板/桌面分界：≤1024 走汉堡抽屉，≥1025 显示内联链接
            - 1199 平板档封闭区间上界 `@media (min-width:768px) and (max-width:1199px)`
          min-width ∈ {768, 1025, 1200}
            - 1025 导航抽屉的桌面侧阈值（与 max-width:1024 配对，避免 1024px 点重叠）
        """
        import re
        allowed = {
            'max-width': {'767px', '1024px', '1199px'},
            'min-width': {'768px', '1025px', '1200px'},
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
        self.assertRegex(pd,
            r'@media \(max-width: 1024px\)\s*\{[^}]*detail-grid\s*\{[^}]*grid-template-columns:\s*1fr',
            'product_detail.html: detail-grid 折单列必须提升到 1024px 断点')

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
    def test_products_banner_aspect_ratio_and_floor(self):
        """F9 修正（v1.5.6 线上复核发现）：aspect-ratio 与 min-height 必须**并存**。

        原断言（v1.4.2）是「必须没有 aspect-ratio」——方向写反了：
        banner 的 img/overlay/content 全是绝对定位，容器高度完全由 CSS 决定，
        删掉 aspect-ratio 后高度塌到地板 120px，1920×442 的图被 object-fit:cover
        上下各裁约 22%（用户反馈「banner 高度变小、图上下被截断」）。
        正确形态：aspect-ratio 提供首选高度，min-height 只做窄屏地板。
        双向断言：必须有比值，也必须有地板。
        """
        products = Path(settings.BASE_DIR,
                        'templates/products.html').read_text(encoding='utf-8')
        block = re.search(r'\.products-banner\s*\{[^}]*\}', products)
        self.assertIsNotNone(block, 'products.html 缺 .products-banner 规则块')
        body = block.group(0)
        self.assertIn('aspect-ratio: 1920 / 442', body,
                      'F9-修正：必须保留 aspect-ratio 首选高度，否则 1920×442 被上下裁切')
        self.assertIn('min-height: 120px', body,
                      '窄屏地板 min-height 仍需保留（P1-7 超窄屏文字空间）')
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
                         {'dirs': {}, 'hashed': {}})

    def test_build_index_collects_hashed_names_from_manifest(self):
        """staticfiles.json 的 paths 必须被带进生成物（生产存储靠它出哈希 URL）。"""
        from pages.static_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'css').mkdir()
            Path(tmp, 'css', 'base.css').write_text('body{}', encoding='utf-8')
            Path(tmp, 'css', 'base.280e03822c88.css').write_text('body{}', encoding='utf-8')
            Path(tmp, 'staticfiles.json').write_text(json.dumps({
                'paths': {'css/base.css': 'css/base.280e03822c88.css'},
                'version': '1.1',
                'hash': 'deadbeef',
            }), encoding='utf-8')

            index = build_index(tmp)
            self.assertEqual(index['hashed'], {'css/base.css': 'css/base.280e03822c88.css'})

    def test_read_hashed_files_tolerates_garbage(self):
        from pages.static_index import read_hashed_files

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_hashed_files(tmp), {}, '没有清单时应返回空字典')

            Path(tmp, 'staticfiles.json').write_text('{not json', encoding='utf-8')
            self.assertEqual(read_hashed_files(tmp), {}, '清单损坏不应抛异常')

            Path(tmp, 'staticfiles.json').write_text(
                json.dumps({'paths': {'a.css': 'a.1.css', 'bad': 3}}), encoding='utf-8')
            self.assertEqual(read_hashed_files(tmp), {'a.css': 'a.1.css'},
                             '非字符串条目应被丢弃')

    def test_rendered_module_is_valid_python(self):
        from pages.static_index import render_module
        src = render_module({'dirs': {'images/products/demo': ['a.webp']},
                             'hashed': {'a.webp': 'a.0123456789ab.webp'}})
        ns = {}
        exec(compile(src, '<static_index_data>', 'exec'), ns)
        self.assertEqual(ns['STATIC_INDEX']['dirs']['images/products/demo'], ['a.webp'])
        self.assertEqual(ns['HASHED_FILES'], {'a.webp': 'a.0123456789ab.webp'})


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


class WhiteNoiseLocalDevTests(SimpleTestCase):
    """本地 WhiteNoise 行为守卫。

    回归背景（2026-09-23）：后台新建 RT410-RGBW 并上传图片后，admin 列表
    图标与前端产品图全部 404 —— 非 autorefresh 的 WhiteNoise 只服务**进程
    启动时**的文件快照（`self.files` dict），运行中新增的 static/ 文件必须
    重启才能访问。
    """

    def test_autorefresh_on_locally_off_on_vercel(self):
        self.assertEqual(
            settings.WHITENOISE_AUTOREFRESH, not settings.IS_VERCEL,
            '本地必须 autorefresh（后台上传的新图片立即可访问，不需重启）；'
            'Vercel 必须关闭（构建期 collectstatic，进程无启动期概念）')


class GeneratedStaticIndexCoverageTests(SimpleTestCase):
    """本地/CI 直接基于 static/ 重建索引并校验覆盖，不再依赖构建期产物。

    防止 static/ 下新增资源后索引（pages/static_index_data.py）过期或 collectstatic
    范围变化，导致线上出现「图片解析不到」的静默回归。v1.5.9（D2）起改为在 setUp
    临时基于真实 static/ 树构建索引，使该守护在本地/CI 也能运行、零 skip。
    """

    # build_index() 与扫描都依赖磁盘上的 static/，无需数据库。
    _SKIP_NAMES = {'.DS_Store', 'Thumbs.db'}

    def setUp(self):
        from pages.static_index import build_index
        static_dir = Path(settings.BASE_DIR, 'static')
        self._index = build_index(str(static_dir))

    def test_index_covers_every_committed_static_file(self):
        index = self._index
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
            # 与 build_index() 的过滤规则保持一致（忽略系统垃圾文件与隐藏文件）。
            name = rel.rsplit('/', 1)[-1]
            if name.startswith('.') or name in self._SKIP_NAMES:
                continue
            if rel not in indexed:
                missing.append(rel)
        self.assertEqual(missing, [], f'索引遗漏了 {len(missing)} 个 static/ 文件')


# ---------------------------------------------------------------------------
# 生产静态存储（pages/storage.py）回归守卫
# ---------------------------------------------------------------------------
# 事故（v1.5.4，2026-09-12）：vercel.json 把 staticfiles/ 排除出函数包以压到
# 225 MB 以内，但 CompressedManifestStaticFilesStorage 运行时必须能读到
# 「原名 → 哈希名」映射。清单不在磁盘上时，{% static %} 会抛
#   ValueError: The file 'css/base.css' could not be found with <...>
# 而 base.html 每个页面都要它 —— 于是**全站 500**。
#
# 修法：① 构建期把 paths 写进包内 Python 模块 pages/static_index_data.py；
#       ② 存储层任何情况下都不抛异常，退回未哈希 URL（v1.5.2 之前的行为）。
# 下面这组测试正是那次事故的最小复现与防回归。
_WHITENOISE_MANIFEST_BACKEND = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
_BUNDLED_BACKEND = 'pages.storage.BundledManifestStaticFilesStorage'

_MISSING_ROOT = str(Path(tempfile.gettempdir(), 'solarone-static-root-absent'))


class BundledStaticManifestTests(TestCase):
    def setUp(self):
        from pages import storage as storage_mod
        self.storage_mod = storage_mod
        self._saved_cache = storage_mod._bundled_cache
        storage_mod._bundled_cache = None
        self.addCleanup(setattr, storage_mod, '_bundled_cache', self._saved_cache)

    def _inject(self, hashed_files):
        mod = types.ModuleType('pages.static_index_data')
        mod.STATIC_INDEX = {'dirs': {}}
        mod.HASHED_FILES = hashed_files
        self._saved_module = sys.modules.get('pages.static_index_data')
        sys.modules['pages.static_index_data'] = mod
        self.storage_mod._bundled_cache = None
        self.addCleanup(self._restore_module)

    def _restore_module(self):
        if self._saved_module is not None:
            sys.modules['pages.static_index_data'] = self._saved_module
        else:
            sys.modules.pop('pages.static_index_data', None)

    def _url(self, name, root=_MISSING_ROOT):
        from django.contrib.staticfiles.storage import staticfiles_storage
        with override_settings(
            STATIC_ROOT=root,
            STATICFILES_DIRS=[],
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': _BUNDLED_BACKEND},
            },
        ):
            return staticfiles_storage.url(name)

    def test_bundled_manifest_provides_hashed_urls(self):
        self._inject({'css/base.css': 'css/base.280e03822c88.css'})
        self.assertEqual(self._url('css/base.css'),
                         '/static/css/base.280e03822c88.css')

    def test_unknown_name_falls_back_instead_of_raising(self):
        """磁盘上没有 static/、清单里也没有这个名字 —— 必须返回未哈希 URL。"""
        self._inject({'css/base.css': 'css/base.280e03822c88.css'})
        self.assertEqual(self._url('images/definitely-missing.webp'),
                         '/static/images/definitely-missing.webp')

    def test_no_manifest_at_all_still_serves_unhashed_urls(self):
        self.storage_mod._bundled_cache = {}
        self.assertEqual(self._url('css/base.css'), '/static/css/base.css')

    def test_corrupt_manifest_file_does_not_raise(self):
        """清单文件存在但版本/格式非法：Django 原生实现会抛 ValueError。"""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'staticfiles.json').write_text('{"version": "9.9"}',
                                                     encoding='utf-8')
            self.storage_mod._bundled_cache = {}
            self.assertEqual(self._url('css/base.css', root=tmp), '/static/css/base.css')

    def test_old_backend_raises_in_the_same_situation(self):
        """反向断言：记录事故的失败模式，证明这个子类不是多余的。"""
        from django.contrib.staticfiles.storage import staticfiles_storage
        with override_settings(
            STATIC_ROOT=_MISSING_ROOT,
            STATICFILES_DIRS=[],
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': _WHITENOISE_MANIFEST_BACKEND},
            },
        ):
            with self.assertRaises(ValueError):
                staticfiles_storage.url('css/base.css')

    def test_home_page_renders_when_static_trees_are_absent(self):
        """端到端：函数包里没有 static/、没有 staticfiles/ —— 首页仍必须 200。"""
        self.storage_mod._bundled_cache = {}
        with override_settings(
            STATIC_ROOT=_MISSING_ROOT,
            STATICFILES_DIRS=[],
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': _BUNDLED_BACKEND},
            },
        ):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_hashed_stylesheet_when_manifest_is_bundled(self):
        self._inject({'css/base.css': 'css/base.280e03822c88.css'})
        with override_settings(
            STATIC_ROOT=_MISSING_ROOT,
            STATICFILES_DIRS=[],
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': _BUNDLED_BACKEND},
            },
        ):
            html = self.client.get('/').content.decode('utf-8')
        self.assertIn('/static/css/base.280e03822c88.css', html,
                      '包内清单可用时必须出哈希 URL（immutable 缓存的前提）')


# ---------------------------------------------------------------------------
# vercel.json 配置守卫（离线校验）
# ---------------------------------------------------------------------------
# 背景（v1.5.3 → v1.5.4）：functions.excludeFiles 曾被写成**数组**，Vercel 在
# **构建开始前**（15s）就以
# 「A Configuration error — Vercel couldn't load a valid project configuration」
# 拒绝部署 —— 与函数包体积无关，纯粹是 schema 校验失败。
#
# 官方 schema（https://openapi.vercel.sh/vercel.json）规定 functions 每个条目的
# excludeFiles / includeFiles 均为 {type: "string", maxLength: 256}，且该
# patternProperties 节点是 additionalProperties: false —— 数组直接判非法。
# 排除多个目录只能靠**花括号展开的单条 glob**（构建器 normalizeGlobs 不会按逗号拆分，
# 但它下游的 npm `glob` / minimatch 支持 `{a,b}`）。
#
# 以下断言全部离线（不联网），目的是让 CI 拦住同类配置错误。
_FUNCTION_OPTIONS = frozenset({
    'excludeFiles', 'includeFiles', 'maxDuration', 'maxConcurrency', 'memory',
    'runtime', 'regions', 'functionFailoverRegions', 'supportsCancellation',
    'experimentalTriggers',
})
_TOP_LEVEL_KEYS = frozenset({
    '$schema', 'alias', 'build', 'buildCommand', 'builds', 'bulkRedirectsPath',
    'bunVersion', 'cleanUrls', 'crons', 'devCommand', 'env',
    'experimentalAtproto', 'experimentalBYOC', 'experimentalEnvironmentVariables',
    'experimentalServiceGroups', 'experimentalServices', 'experimentalServicesV2',
    'fluid', 'framework', 'functionFailoverRegions', 'functions', 'git', 'github',
    'headers', 'ignoreCommand', 'images', 'installCommand', 'name',
    'outputDirectory', 'passiveRegions', 'proxy', 'redirects', 'regions',
    'relatedProjects', 'rewrites', 'routes', 'schedules', 'scope', 'services',
    'trailingSlash', 'version', 'wildcard',
})
_STRING_OPTION_MAXLEN = 256


def _expand_braces(pattern):
    """把 ``{a,b}/**`` 展开为 ``['a/**', 'b/**']``；不含花括号时原样返回。"""
    match = re.search(r'\{([^{}]*)\}', pattern)
    if not match:
        return [pattern]
    expanded = []
    for alt in match.group(1).split(','):
        expanded.extend(
            _expand_braces(pattern[:match.start()] + alt + pattern[match.end():])
        )
    return expanded


class VercelConfigTests(SimpleTestCase):
    """vercel.json 必须符合官方 schema —— 违规会让 Vercel 在构建前直接拒绝部署。"""

    def _cfg(self):
        path = Path(settings.BASE_DIR, 'vercel.json')
        if not path.is_file():
            self.skipTest('vercel.json 不存在')
        return json.loads(path.read_text(encoding='utf-8'))

    def test_top_level_keys_are_known(self):
        unknown = set(self._cfg()) - _TOP_LEVEL_KEYS
        self.assertEqual(
            unknown, set(),
            f'vercel.json 顶层出现 schema 不认识的键（会被直接拒绝）: {sorted(unknown)}',
        )

    def test_function_options_match_schema_types(self):
        for pattern, options in (self._cfg().get('functions') or {}).items():
            self.assertLessEqual(len(pattern), _STRING_OPTION_MAXLEN,
                                 'functions 的键超过 schema maxLength')
            self.assertIsInstance(options, dict)
            unknown = set(options) - _FUNCTION_OPTIONS
            self.assertEqual(
                unknown, set(),
                f'functions["{pattern}"] 含非法选项（additionalProperties:false）: {sorted(unknown)}',
            )
            for key in ('excludeFiles', 'includeFiles'):
                if key not in options:
                    continue
                value = options[key]
                self.assertIsInstance(
                    value, str,
                    f'functions["{pattern}"].{key} 必须是 string（schema: type=string）；'
                    f'写成 {type(value).__name__} 会让 Vercel 报 Configuration error',
                )
                self.assertLessEqual(
                    len(value), _STRING_OPTION_MAXLEN,
                    f'functions["{pattern}"].{key} 超过 schema 的 maxLength={_STRING_OPTION_MAXLEN}',
                )

    def test_heavy_static_trees_excluded(self):
        """体积修复的核心不变量：static/ 与 staticfiles/ 不进函数包。

        清单**不再**依赖 includeFiles：哈希映射改由包内 Python 模块提供，少一个
        会和 excludeFiles 抢文件的机制（v1.5.4 全站 500 的根源）。见
        BundledStaticManifestTests。
        """
        functions = self._cfg().get('functions') or {}
        if not functions:
            self.skipTest('vercel.json 未配置 functions')
        options = next(iter(functions.values()))

        excluded = _expand_braces(options.get('excludeFiles') or '')
        self.assertIn('static/**', excluded, '源码 static/ 未排除 → 函数包会超 225 MB')
        self.assertIn('staticfiles/**', excluded,
                      'collectstatic 产物 staticfiles/ 未排除 → 函数包会超 225 MB')

    def test_brace_glob_expansion_helper(self):
        self.assertEqual(_expand_braces('a/**'), ['a/**'])
        self.assertEqual(_expand_braces('{a,b}/**'), ['a/**', 'b/**'])
        self.assertEqual(
            _expand_braces('{static,staticfiles,media}/**'),
            ['static/**', 'staticfiles/**', 'media/**'],
        )


# ---------------------------------------------------------------------------
# Production statelessness (A1 / B3 / B4 / B7, v1.6.0)
# ---------------------------------------------------------------------------
# Decision (2026-09-14): the committed seed_data.json is the single source of
# truth for content. In production (IS_VERCEL=True) no request reads content
# from the database; the DB is only a local admin preview. These guards prove
# the prod code paths never touch the DB for content.

class StatelessProductionTests(TestCase):
    """Production must be fully stateless — content from seed JSON, never the DB."""

    # ---- A1 + B7: products/projects loaders skip the DB on Vercel ----
    @override_settings(IS_VERCEL=True)
    def test_prod_loaders_skip_db(self):
        from pages.views import data_loaders

        with mock.patch('pages.models.Product.objects') as prod_mock:
            result = data_loaders._get_products_from_db('en')
            self.assertIsInstance(result, list, 'products loader must return a list')
            self.assertFalse(
                prod_mock.called,
                'products loader must NOT query the DB on Vercel (A1/B7)',
            )

        with mock.patch('pages.models.Project.objects') as proj_mock:
            result = data_loaders._get_projects_from_db('en')
            self.assertIsInstance(result, list, 'projects loader must return a list')
            self.assertFalse(
                proj_mock.called,
                'projects loader must NOT query the DB on Vercel (A1/B7)',
            )

    # ---- A1.1 + B4: get_common_context never writes to the DB ----
    def test_get_common_context_no_db_write(self):
        from pages.views.common import get_common_context
        from django.core.cache import cache
        from pages.models import SiteConfig

        # Variant A — local dev (IS_VERCEL=False): when the SiteConfig singleton is
        # missing, the OLD code called SiteConfig.objects.create() on a GET (a hidden
        # write). It must now fall back to seed defaults instead (B4).
        SiteConfig.objects.all().delete()
        cache.clear()
        with override_settings(IS_VERCEL=False):
            with mock.patch('pages.models.SiteConfig.objects.create') as create_mock:
                context = get_common_context()
                config = context['config']
                self.assertFalse(
                    create_mock.called,
                    'get_common_context must NOT auto-create a SiteConfig row (B4)',
                )
                self.assertTrue(
                    getattr(config, 'hero_bg_url', ''),
                    'seed-fallback config must still resolve hero_bg_url',
                )

        # Variant B — production (IS_VERCEL=True): the DB must not be queried at all.
        cache.clear()
        with override_settings(IS_VERCEL=True):
            with mock.patch('pages.models.SiteConfig.objects') as cfg_mock:
                get_common_context()
                self.assertFalse(
                    cfg_mock.called,
                    'get_common_context must NOT query the DB on Vercel (A1.1)',
                )

    # ---- B3: news view falls back to the seed JSON in production ----
    @override_settings(IS_VERCEL=True)
    def test_news_seed_fallback(self):
        from pages.views import views_other

        seed = {'news': [{
            'slug': 'x',
            'title': 'SeedNewsTitleXYZ',
            'summary': 's',
            'content': 'c',
            'image': 'images/news/x.webp',
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
        }]}
        # Patch the module news() actually reads from (get_news -> data_loaders._load_seed),
        # not views_other (which only sitemap_xml uses). A unique title proves the
        # seeded article is really rendered (and exercises _normalize_news_article ->
        # _static_url, catching the missing import that crashed on the first real news).
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            resp = self.client.get(reverse('news'))

        self.assertEqual(resp.status_code, 200)
        self.assertIn('SeedNewsTitleXYZ', resp.content.decode('utf-8'))

    # ---- P1: /products/ must not touch the DB in production, and must still
    #      render the curated card subset instead of every product ----
    @override_settings(IS_VERCEL=True)
    def test_products_page_prod_no_db_and_shows_curated_subset(self):
        import pages.cards as cards_mod

        with mock.patch.object(cards_mod.ProductsPageCard, 'objects') as ppc_mock:
            resp = self.client.get(reverse('products'))
            self.assertFalse(
                ppc_mock.filter.called,
                'products view must NOT query ProductsPageCard on Vercel (P1)',
            )

        self.assertEqual(resp.status_code, 200)
        # v1.8.2: the title text is wrapped in <bdi> for RTL bidi isolation, so
        # the inner markup must be stripped instead of matching plain text.
        # (Asserting on the *expected behaviour* — which titles render, in what
        # order — not on the exact markup, which legitimately changes.)
        rendered = [
            re.sub(r'<[^>]+>', '', m.group(1)).strip()
            for m in re.finditer(
                r'<h3[^>]*class="[^"]*product-card-title[^"]*"[^>]*>(.*?)</h3>',
                resp.content.decode('utf-8'), re.S)
        ]

        from pages.views.utils import _load_seed
        seed = _load_seed()
        active_cards = [c for c in seed.get('productspagecards', [])
                        if c.get('is_active', True)]
        active_cards.sort(key=lambda c: c.get('order', 0) or 0)
        expected = [c['title'] for c in active_cards if c.get('title')]

        self.assertEqual(
            rendered, expected,
            'production must render the curated cards in seed order',
        )
        # The `all_card_slugs` safety net is DB-backed, so on Vercel the seed
        # fallback is the only thing preventing every product from being shown.
        self.assertLess(
            len(rendered), len(seed.get('products', [])),
            'production must show the curated subset, never every product',
        )

    @override_settings(IS_VERCEL=True)
    def test_products_page_prod_issues_zero_queries(self):
        """The real contract: on Vercel /products/ touches the DB zero times.

        The test above only proves ProductsPageCard is never queried; this one
        pins the whole "production is stateless" promise (v1.6.0) for the page.

        VisitorTrackingMiddleware is registered only when `not IS_VERCEL`
        (settings.py:182-184) and `override_settings` cannot re-evaluate
        MIDDLEWARE, so it is stripped here to model the production stack —
        otherwise the assertion would trip over 4 analytics queries that never
        exist on Vercel.
        """
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        mw = [m for m in settings.MIDDLEWARE if 'VisitorTracking' not in m]
        with self.settings(MIDDLEWARE=mw):
            with CaptureQueriesContext(connection) as ctx:
                resp = self.client.get(reverse('products'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [q['sql'] for q in ctx.captured_queries], [],
            'production /products/ must not query the DB at all',
        )


class I18nCatalogGuardTests(SimpleTestCase):
    """可译字符串必须存在于编译后的 gettext 目录里，否则静默回退成英文。

    背景（2026-09-17 核查）：`locale/` 最后一次同步是 2026-08-08（c88154a），
    此后五周模板持续增长却无人再跑 makemessages。核查时模板侧共 201 个可译
    字符串，其中 **31 个在 locale/<lang>/LC_MESSAGES/django.mo 里没有条目**，
    另有 4 条 Python 字符串同样缺失 —— 它们在 fr/es/de/ru/ar 全部回退为英文。
    受损最重的是合规相关的地方：
      * Cookie 同意条（base.html，2026-08-15 由 7765865 引入，从未翻译）——
        一个 GDPR「知情同意」界面，在五个本地化站点上以英文呈现；
      * about.html 的 cookie / 隐私政策章节；
      * 移动端抽屉标签（Main menu / Theme / Change language）与产品规格表头；
      * 联系表单给访客的 4 条提示（成功 / 限流 / 降级 / 保存失败）。

    提取方式刻意复用 Django 自己的机制，避免与 makemessages 漂移：
      * 模板 → django.utils.translation.template.templatize()。它内部走
        template.Lexer 分词 + 官方 inline_re/block_re，正是 makemessages 投喂
        xgettext 的那份产物；自己写正则会在转义引号（`"L\\" × W\\""`）等
        边角上与官方行为分叉。
      * Python → ast。ast 会自动折叠隐式拼接的相邻字面量（`_('a' 'b')` 视为
        'ab'），而正则既漏掉这个折叠，又会把 `__import__('sys')` 误判成
        `_('sys')`。

    比对目标是 .mo 而非 .po —— .mo 才是运行时真正查表的东西，因此
    「.po 已补但忘了 compilemessages」同样会被这条守卫抓住。

    KNOWN_UNTRANSLATED 是冻结的存量欠账清单：**只许缩小**。翻译落地后请立即
    删除对应条目（test_allowlist_entries_are_still_untranslated 会盯着这件事）；
    任何不在清单里、又不在目录里的字符串都会让测试变红。
    """

    # 存量欠账（截至 2026-09-17）。新增条目 = 又漏了一次翻译同步，不要这么做。
    KNOWN_UNTRANSLATED = frozenset({
        'Accept All',
        'Analytics cookies:',
        'Application',
        'Change language',
        'Cookie Usage',
        'Data We Collect',
        'Dimming (option)',
        'Essential cookies:',
        'Filter / Categories',
        'Filter by Application',
        'Finish (option)',
        'Help us understand how visitors interact with our website',
        'Input Voltage',
        'LED Driver Location',
        'Last updated:',
        'Main menu',
        'Marketing cookies:',
        'Reject',
        'Required for basic site functionality',
        'Sorry, we could not save your message. Please try again.',
        'Swipe to view all columns',
        'Theme',
        'Too many messages submitted recently. Please wait a few minutes '
        'before trying again.',
        'Types of cookies we use:',
        'Under GDPR (EU) and similar regulations, you have the right to '
        'access, correct, or delete your personal data. Contact us at',
        'Used to deliver relevant advertisements',
        'View image %(forloop.counter)s',
        'We collect minimal data necessary for website functionality and '
        'analytics, including: device type, browser type, pages visited, and '
        'referring source. We do not sell your personal data to third parties.',
        'We could not deliver your message right now. Please try again later '
        'or email us directly using the address on this site.',
        "We use cookies to enhance your browsing experience and analyze site "
        "traffic. By clicking 'Accept', you consent to our use of cookies.",
        'We use cookies to enhance your browsing experience and analyze site '
        'traffic. Cookies are small text files stored on your device that help '
        'us understand how you use our website.',
        'You can accept or reject non-essential cookies at any time. Essential '
        'cookies cannot be disabled as they are necessary for the website to '
        'function.',
        'Your Rights',
        'Your message has been sent successfully!',
        'for any privacy-related requests.',
    })

    # en 是源语言：msgid 本身就是英文，查不到自然回退英文，不构成缺陷。
    NON_SOURCE_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    # templatize 的产物形如 gettext(u'...') 或 pgettext(u'ctx', u'...')
    _CALL_RE = re.compile(
        r"(?:gettext|pgettext)\(u((?:'(?:[^'\\]|\\.)*')|(?:\"(?:[^\"\\]|\\.)*\"))"
        r"(?:\s*,\s*u((?:'(?:[^'\\]|\\.)*')|(?:\"(?:[^\"\\]|\\.)*\")))?\)"
    )
    _PY_FUNCS = frozenset(
        {'_', 'gettext', 'gettext_lazy', 'ugettext', 'ugettext_lazy'})

    @staticmethod
    def _catalog(lang):
        path = Path(settings.BASE_DIR, 'locale', lang, 'LC_MESSAGES', 'django.mo')
        with path.open('rb') as fh:
            return gettext.GNUTranslations(fh)._catalog

    @staticmethod
    def _catalog_has(catalog, msgid):
        # templatize 会把 `%` 翻倍（免得 xgettext 把字面 % 当格式符），
        # 所以两种写法都算命中。
        return msgid in catalog or msgid.replace('%%', '%') in catalog

    @classmethod
    def _template_strings(cls):
        from django.utils.translation.template import templatize
        found = set()
        for path in sorted(Path(settings.BASE_DIR, 'templates').rglob('*.html')):
            rendered = templatize(path.read_text(encoding='utf-8'), origin=str(path))
            for match in cls._CALL_RE.finditer(rendered):
                literal = match.group(2) if match.group(2) is not None else match.group(1)
                found.add(ast.literal_eval(literal))
        return found

    @classmethod
    def _python_strings(cls):
        found = set()
        for path in sorted(Path(settings.BASE_DIR, 'pages').rglob('*.py')):
            if path.name.startswith('test'):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)
                if name not in cls._PY_FUNCS:
                    continue
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.add(arg.value)
        return found

    def _offenders(self, strings):
        """返回 {lang: [未翻译字符串]}，已排除已知欠账。"""
        offenders = {}
        for lang in self.NON_SOURCE_LANGS:
            catalog = self._catalog(lang)
            missing = sorted(
                s for s in strings
                if not self._catalog_has(catalog, s)
                and s not in self.KNOWN_UNTRANSLATED
            )
            if missing:
                offenders[lang] = missing
        return offenders

    # --- 反空洞自检：守卫本身必须真的在工作 --------------------------------
    def test_extractor_actually_extracts(self):
        """防止守卫退化成恒真（提取器返回空集合时，下文两个契约会假绿）。"""
        template_strings = self._template_strings()
        self.assertGreater(
            len(template_strings), 150,
            f'模板提取器只抓到 {len(template_strings)} 个字符串，守卫已失效')
        self.assertIn('Products', template_strings)

        from django.utils.translation.template import templatize
        # 单引号包裹 + 内含双引号：官方 inline_re 能正确切出 msgid。
        # （反例：写成 {% trans "L\" × W\" × H\"" %} 时 templatize 会切出 'L\\'，
        #  在 .po 里留下一个永不命中的垃圾 msgid —— v1.6.2 已修正模板写法。）
        match = self._CALL_RE.search(templatize("""{% trans 'L" × W" × H"' %}"""))
        self.assertIsNotNone(match, '官方提取路径抓不到单引号包裹的 trans')
        self.assertEqual(ast.literal_eval(match.group(1)), 'L" × W" × H"')

        self.assertGreater(
            len(self._python_strings()), 3,
            'Python 提取器只抓到极少数字符串，守卫可能已失效')

    def test_allowlist_only_shrinks(self):
        """清单只许缩小：某条目已翻译却还留在 KNOWN_UNTRANSLATED 就失败了。"""
        stale = set()
        for lang in self.NON_SOURCE_LANGS:
            catalog = self._catalog(lang)
            for msgid in self.KNOWN_UNTRANSLATED:
                if self._catalog_has(catalog, msgid):
                    stale.add(msgid)
        self.assertEqual(
            stale, set(),
            f'这些条目已经有翻译了，请从 KNOWN_UNTRANSLATED 删除：{sorted(stale)}')

    # --- 契约 ---------------------------------------------------------------
    def test_all_template_strings_are_translated(self):
        offenders = self._offenders(self._template_strings())
        self.assertEqual(
            offenders, {},
            '新增的模板可译字符串缺少 gettext 条目（会静默显示英文）：'
            f'{offenders}')

    def test_all_python_strings_are_translated(self):
        offenders = self._offenders(self._python_strings())
        self.assertEqual(
            offenders, {},
            '新增的 Python 可译字符串缺少 gettext 条目（会静默显示英文）：'
            f'{offenders}')


class DataDrivenTranslationTests(SimpleTestCase):
    """第二条翻译路径：`pages/views/i18n.py` 的 `_SIDEBAR_I18N` 硬编码字典。

    本站有两条互不相干的翻译机制：
      ① gettext 目录（locale/*.mo）—— 由 I18nCatalogGuardTests 守卫；
      ② `_SIDEBAR_I18N` 字典 + `_t(label, lang)` —— 侧栏分类/系列/场馆类型/规格
         标签与 SiteConfig 文案走这条。`_t()` 在字典里查不到时**静默回退英文
         原文**（`entry.get(lang, label)`），既不报错也不写日志。

    2026-09-17 首次为路径 ② 建守卫时扫出 6 处**现存**漏译，且已运行时确认
    （/de/、/fr/、/ar/ 的 /projects/ 页面上，同一页里 'Fußballplatz' 已本地化，
    而下面这些仍是英文）：
      * `Karting Track` / `Fencing` / `Aquatics Centre` / `City Expressway` /
        `Airports` —— `_get_projects_sidebar` 一直在请求，字典里却没有条目
        （注意字典里存的是 `Airports and Ports`，与请求的 `Airports` 键名对不上）；
      * `Featured Projects` —— seed_data.json 的 `siteconfig.projects_title` 经
        `common.py` 的 `_t(config.projects_title, lang)` 下发，字典里没有条目。
    六条均已补录，本守卫防止同类问题再发生。

    为什么不复用 I18nCatalogGuardTests 的 templatize 提取：路径 ② 里的标签多以
    **变量**形式下发（`product_detail.html:176` 的 `{% trans item.label %}`、
    `enrich.py` 的 `_t(card_label, lang)`、`common.py` 的
    `_t(config.hero_title, lang)`），而 templatize() 会把非字面量参数整段 mask 掉
    —— 静态扫描一律看不见。所以本守卫改为直接扫「谁会被传给 _t()」这个全集：
      a. 各模块中 `_t('字面量', lang)` 的首参；
      b. `_PRODUCT_CARD_LABELS` / `_PRODUCT_CAT_TO_SIDEBAR_LABEL` 的取值
         （它们经 enrich.py 以变量形式喂给 `_t`）；
      c. `_t(config.<字段>, lang)` 的字段在 seed_data.json['siteconfig'] 里的英文取值。
    再要求每条都在 `_SIDEBAR_I18N` 有条目，且 fr/es/de/ru/ar 五语齐备且非空。

    静态提取有个固有弱点：**首参既非字面量、又不来自上面两个映射字典时看不见**
    （例如新引入第三张 dict 后 `_t(other_dict['label'], lang)`）。独立验证者用
    `_t(_QA_EXTRA['label'], lang)` 实测确认过这个洞。因此再加两层把口子堵死：
      * `test_labels_actually_routed_through_t_are_covered` —— **运行时**抽查：用
        spy 替换 `i18n._t` 后真实执行 `_get_products_sidebar` /
        `_get_projects_sidebar`，记录**所有实际流经 `_t()` 的标签**再校验。这条
        路径不依赖静态分析，所以未来换成任何数据来源都会被抓住。
      * `test_card_labels_actually_routed_through_t_are_covered` —— 同上，但针对
        `enrich.py` 的产品卡 `card_label`。它对 `_t` 拿的是**独立引用**，patch
        `i18n` 模块拦不到，必须 patch `pages.views.enrich._t`；用 seed_data 的
        真实产品驱动 `_enrich_product`（= 生产无状态路径）。**这一条是必需的**：
        实测过「把 `card_label` 的数据源换成第三张 dict」这个突变，只靠调用点
        清单会漏（调用点数量没变），只有运行时 spy 抓得到。
      * `test_siteconfig_labels_actually_routed_through_t_are_covered` —— 同上，但
        针对 `common.py` 的 6 处 `_t(config.<字段>, lang)`，patch
        `pages.views.common._t` 并真跑 `get_common_context()`。
      * `test_config_fields_passed_to_t_are_pinned` —— **字段集必须逐字固定**。
        独立验证者实测：把 `_t(config.hero_title, lang)` 改成
        `_t(_HERO_COPY['title'], lang)` 时，静态规则 (c) 是按 `config.<字段>`
        这个 **name** 认人的，换掉后该字段**从待译集合里悄悄消失** —— 是
        "覆盖变少"，不是"变红"；调用点清单数量 6→6 也不变。所以必须把字段集
        钉死：少一个、多一个、换成别的来源，都要显式改这张表。
      * `test_non_literal_t_call_sites_are_inventoried` —— 非字面量调用点数量清单，
        兜底 `common.py` / `enrich.py` 这类「独立引用」模块。
    四层合起来，机制 ② 的覆盖是闭合的。
    """

    ALL_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    # `_t(config.<字段>, lang)` 里被翻译的 SiteConfig 字段集，逐字固定。
    # 少一个、多一个、或改成非 config 来源，本条测试都会红 —— 因为那意味着
    # 静态规则 (c) 的覆盖范围**悄悄变了**（历史上这正好是"原地换数据源"的漏洞）。
    KNOWN_CONFIG_FIELDS = {
        'pages/views/common.py': (
            'hero_subtitle', 'hero_title',
            'meta_description', 'meta_title',
            'products_subtitle', 'products_title',
            'projects_subtitle', 'projects_title',
        ),
    }

    # 非字面量 `_t()` 调用点的已知清单（相对 BASE_DIR 的路径 → 调用点数量）。
    # 这些调用点因 `from .i18n import _t` 拿着独立引用，运行时 spy 抓不到，所以
    # 用数量清单兜底：新增一个变量型调用点就必须同步登记，否则测试变红。
    # 主体（26 处字面量 + 侧栏构建函数）由运行时 spy 覆盖，不进这张表。
    KNOWN_DYNAMIC_SITES = {
        'pages/views/common.py': 8,   # _t(config.hero_title / …_subtitle / meta_title / meta_description 等 8 个字段)
        'pages/views/enrich.py': 1,   # _t(card_label) —— 取自两个映射字典
        # _t(cat, lang) x2（news 视图的 chips 数据 + 卡片分类徽章）+ x2（
        # news_detail 视图的详情页分类标签 + related 卡片徽章）。取值只有
        # NewsArticle.NEWS_CATEGORIES 的 3 个 choice，现已在 _SIDEBAR_I18N 里
        # 补齐 fr/es/de/ru/ar 五语；将来新增分类必须同步补字典，否则该语种静默
        # 回退英文。
        'pages/views/views_other.py': 4,
    }

    # 边界说明：SiteConfig 里**未经** common.py 传给 _t() 的字段不在覆盖范围内
    # （联系邮箱、电话、社交链接等本就无需翻译）。若将来 common.py 新增
    # `_t(config.x, lang)`，字段会自动进入 (c) 而被覆盖。

    @staticmethod
    def _t_call_first_args(*, attribute_on=None):
        """扫 pages/**.py 里所有 _t(...) 调用，返回 (字符串字面量集合, 属性名集合)。"""
        literals, attributes = set(), set()
        for path in sorted(Path(settings.BASE_DIR, 'pages').rglob('*.py')):
            if path.name.startswith('test'):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)
                if name != '_t':
                    continue
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literals.add(arg.value)
                elif isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name):
                    if attribute_on is None or arg.value.id == attribute_on:
                        attributes.add(arg.attr)
        return literals, attributes

    def _required_labels(self):
        from pages.views.i18n import (
            _PRODUCT_CARD_LABELS, _PRODUCT_CAT_TO_SIDEBAR_LABEL)

        literals, _ = self._t_call_first_args()
        labels = set(literals)
        labels |= set(_PRODUCT_CARD_LABELS.values())
        labels |= set(_PRODUCT_CAT_TO_SIDEBAR_LABEL.values())

        # (c) SiteConfig 字段的英文取值：取自数据源 seed_data.json，与运行时一致。
        _, config_fields = self._t_call_first_args(attribute_on='config')
        seed = json.loads(
            Path(settings.BASE_DIR, 'seed_data.json').read_text(encoding='utf-8'))
        siteconfig = seed['siteconfig']
        for field in sorted(config_fields):
            value = siteconfig.get(field)
            if isinstance(value, str) and value.strip():
                labels.add(value)

        return {label for label in labels if label.strip()}

    # --- 反空洞自检 ---------------------------------------------------------
    def test_extractor_actually_extracts(self):
        """提取器返回空集合时下面的契约会假绿，先把这条钉死。"""
        literals, config_fields = self._t_call_first_args(attribute_on='config')
        self.assertGreater(
            len(literals), 20,
            f'只扫到 {len(literals)} 个字面量 _t() 调用，提取器可能已失效')
        self.assertIn('Outdoor Sports', literals)
        self.assertGreaterEqual(
            len(config_fields), 5,
            f'_t(config.<字段>) 只扫到 {sorted(config_fields)}，提取器可能已失效')
        labels = self._required_labels()
        self.assertGreater(len(labels), 25, f'待译标签只有 {len(labels)} 条，可疑')

    # --- 契约 ---------------------------------------------------------------
    def test_every_required_label_has_all_five_languages(self):
        from pages.views.i18n import _SIDEBAR_I18N
        offenders = {}
        for label in sorted(self._required_labels()):
            entry = _SIDEBAR_I18N.get(label)
            if entry is None:
                offenders[label] = '字典里没有条目（_t 会静默回退英文）'
                continue
            missing = [lang for lang in self.ALL_LANGS if not entry.get(lang, '').strip()]
            if missing:
                offenders[label] = f'缺语言 {missing}'
        self.assertEqual(
            offenders, {},
            '这些经 _t() 下发的标签没有完整五语翻译，会在页面上显示英文：'
            f'{offenders}')

    def test_dictionary_values_are_non_empty(self):
        from pages.views.i18n import _SIDEBAR_I18N
        offenders = {
            label: [lang for lang, text in entry.items() if not str(text).strip()]
            for label, entry in _SIDEBAR_I18N.items()
            if any(not str(text).strip() for text in entry.values())
        }
        self.assertEqual(offenders, {}, f'_SIDEBAR_I18N 存在空译文：{offenders}')

    # --- 运行时抽查：不依赖静态分析，闭合「变量来源不明」的洞 -----------------
    def _offending_labels(self, labels):
        """返回 {label: 原因} —— 缺条目或缺语言的标签。"""
        from pages.views.i18n import _SIDEBAR_I18N
        offenders = {}
        for label in sorted(set(labels)):
            entry = _SIDEBAR_I18N.get(label)
            if entry is None:
                offenders[label] = '字典里没有条目（_t 会静默回退英文）'
                continue
            missing = [lang for lang in self.ALL_LANGS if not entry.get(lang, '').strip()]
            if missing:
                offenders[label] = f'缺语言 {missing}'
        return offenders

    def _labels_routed_through_t(self):
        """真实执行侧栏构建函数，记录所有实际流经 `_t()` 的标签。

        构建函数引用的是 `i18n` 的模块级 `_t`，故 patch 模块全局即可拦到它们。
        """
        import pages.views.i18n as i18n_mod
        real_t = i18n_mod._t
        seen = []

        def spy(label, lang='en'):
            seen.append(label)
            return real_t(label, lang)

        with mock.patch.object(i18n_mod, '_t', spy):
            i18n_mod._get_products_sidebar('en')
            i18n_mod._get_projects_sidebar('en')

        return [s for s in seen if isinstance(s, str) and s.strip()]

    def test_labels_actually_routed_through_t_are_covered(self):
        """不管标签从哪来，只要真的流经 `_t()`，就必须有完整五语条目。

        这条是静态提取的兜底：改用第三张 dict、f-string、或任何新数据源喂给
        `_t()`，都会在这里被抓住（静态清单看不见，运行时不看不见）。
        """
        labels = self._labels_routed_through_t()
        self.assertGreater(
            len(labels), 15,
            f'侧栏构建函数只流经 {len(labels)} 个标签，spy 可能已失效')
        offenders = self._offending_labels(labels)
        self.assertEqual(
            offenders, {},
            f'这些侧栏标签真实流经 _t() 但没有完整五语翻译：{offenders}')

    def test_card_labels_actually_routed_through_t_are_covered(self):
        """产品卡分类标签：跑一遍生产无状态路径，记录流经 `_t()` 的标签。

        `enrich.py` 是 `from .i18n import _t`（拿的是**独立引用**），所以 patch
        `i18n` 模块全局**拦不到**它，必须 patch `pages.views.enrich._t`。
        用 seed_data 的真实产品驱动 `_enrich_product`（生产 IS_VERCEL 下走的
        就是这条路径），于是 `card_label` 的数据源无论以后换成什么，只要真的
        流经 `_t()` 就会在这里现形 —— 这正是调用点清单（数量不变即通过）堵不住
        的那个洞。
        """
        from pages.views import enrich as enrich_mod
        from pages.views.utils import _DictProduct, _load_seed

        seed = _load_seed()
        products = seed.get('products', [])
        self.assertGreater(len(products), 0, 'seed_data 里没有产品，这条测试无意义')

        real_t = enrich_mod._t
        seen = []

        def spy(label, lang='en'):
            seen.append(label)
            return real_t(label, lang)

        with mock.patch.object(enrich_mod, '_t', spy):
            for item in products:
                enrich_mod._enrich_product(_DictProduct(item), 'en')

        seen = [s for s in seen if isinstance(s, str) and s.strip()]
        self.assertGreater(len(seen), 0, 'spy 没抓到任何标签，patch 目标可能已失效')
        offenders = self._offending_labels(seen)
        self.assertEqual(
            offenders, {},
            f'这些产品卡标签真实流经 _t() 但没有完整五语翻译：{offenders}')

    def test_siteconfig_labels_actually_routed_through_t_are_covered(self):
        """SiteConfig 文案：patch `pages.views.common._t`，真跑 `get_common_context()`。

        `common.py` 同样是 `from .i18n import _t`（独立引用），必须 patch 它自己的
        模块全局。用 `override_settings(IS_VERCEL=True)` 走**生产无状态分支**
        （`_build_siteconfig_from_seed()`），这样既不碰 DB 也不依赖测试库状态。
        """
        import pages.views.common as common_mod
        from django.core.cache import cache

        cache.delete('site_config')
        real_t = common_mod._t
        seen = []

        def spy(label, lang='en'):
            seen.append(label)
            return real_t(label, lang)

        with override_settings(IS_VERCEL=True):
            with mock.patch.object(common_mod, '_t', spy):
                common_mod.get_common_context()

        seen = [s for s in seen if isinstance(s, str) and s.strip()]
        self.assertGreater(len(seen), 0, 'spy 没抓到任何标签，patch 目标可能已失效')
        offenders = self._offending_labels(seen)
        self.assertEqual(
            offenders, {},
            f'这些 SiteConfig 文案真实流经 _t() 但没有完整五语翻译：{offenders}')

    def test_config_fields_passed_to_t_are_pinned(self):
        """`_t(config.<字段>, lang)` 的字段集必须与 KNOWN_CONFIG_FIELDS 逐字一致。

        这是「原地换数据源」漏洞的正解：静态规则 (c) 按 `config` 这个 name 认字段，
        改成 `_t(third_dict['title'], lang)` 后该字段**静默从待译集合消失**（覆盖
        变少而非变红），调用点清单数量又不变。把字段集钉死后，任何增减或换源都
        必须显式改表 —— 想改就得先想清楚英文回退的后果。
        """
        base = Path(settings.BASE_DIR)
        fields = {}
        for path in sorted((base / 'pages').rglob('*.py')):
            if path.name.startswith('test'):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            found = []
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == '_t' and node.args):
                    continue
                arg0 = node.args[0]
                if (isinstance(arg0, ast.Attribute)
                        and isinstance(arg0.value, ast.Name)
                        and arg0.value.id == 'config'):
                    found.append(arg0.attr)
            if found:
                rel = str(path.relative_to(base)).replace('\\', '/')
                fields[rel] = tuple(sorted(found))
        self.assertEqual(
            fields, self.KNOWN_CONFIG_FIELDS,
            '被 _t() 翻译的 SiteConfig 字段集变了。这通常意味着静态规则 (c) 的'
            '覆盖范围悄悄改变了 —— 若某个字段不再经 _t() 下发，它在 fr/es/de/ru/ar '
            '就会静默回退英文。确认无误后同步更新 KNOWN_CONFIG_FIELDS。')

    def test_non_literal_t_call_sites_are_inventoried(self):
        """非字面量 `_t()` 调用点必须与 KNOWN_DYNAMIC_SITES 一致。

        运行时 spy 只覆盖侧栏构建函数；`common.py` / `enrich.py` 拿着 `_t` 的
        独立引用，patch 不到。所以用调用点数量清单堵口：新加一个变量型
        `_t()` 调用点（例如 `_t(third_dict['label'], lang)`）会让本条变红，逼
        作者改用已覆盖的映射源，或显式登记进清单并说明取值来源。
        """
        base = Path(settings.BASE_DIR)
        counts = {}
        for path in sorted((base / 'pages').rglob('*.py')):
            if path.name.startswith('test'):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == '_t' and node.args
                        and not isinstance(node.args[0], ast.Constant)):
                    rel = str(path.relative_to(base)).replace('\\', '/')
                    counts[rel] = counts.get(rel, 0) + 1
        self.assertEqual(
            counts, self.KNOWN_DYNAMIC_SITES,
            '非字面量 _t() 调用点的清单对不上。新增的调用点要么改用 '
            '_PRODUCT_CARD_LABELS / _PRODUCT_CAT_TO_SIDEBAR_LABEL / '
            '_t(config.<字段>) 这三种已覆盖的来源，要么登记进 '
            'KNOWN_DYNAMIC_SITES 并说明取值来源。')


class N43P0SeoTranslationTests(TestCase):
    """P0 SEO 翻译链路（N-43）：14 条 SEO 文案上线五语。

    两条通道都覆盖：
      * 6 个模板的 <title> / <meta name="description"> 经 `{% blocktrans %}` 进
        gettext 目录（locale/<lang>/LC_MESSAGES/django.{po,mo}）；
      * 全局 meta_title / meta_description 经 `common.py` 的 `_t()` 走
        `_SIDEBAR_I18N`（由 pages/views/i18n_overrides.json 在导入时合并，
        脚本导入，不改源码字典）。

    本组测试证明：① 导入器确实把译文写进了 .mo / overrides；② /de/ 首页真的
    渲染出德文 <title> 与 meta description，且不再回退英文。
    """

    META_TITLE_EN = 'SolarOne — Precision LED Lighting Systems'
    HOME_TITLE_EN = 'SolarOne — Professional LED Sports Lighting Solutions Since 2007'
    HOME_DESC_PREFIX_DE = 'SolarOne entwickelt und fertigt professionelle LED-Sport-'

    def test_siteconfig_meta_routed_via_overrides(self):
        from pages.views.i18n import _t
        self.assertEqual(
            _t(self.META_TITLE_EN, 'de'),
            'SolarOne — Präzise LED-Beleuchtungssysteme')
        # 'en' has no entry in the dict by design -> returns the English label.
        self.assertEqual(_t(self.META_TITLE_EN, 'en'), self.META_TITLE_EN)

    def test_template_title_in_compiled_catalog(self):
        import polib
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            mo_path = Path(settings.BASE_DIR, 'locale', lang,
                           'LC_MESSAGES', 'django.mo')
            mo = polib.mofile(str(mo_path))
            entry = mo.find(self.HOME_TITLE_EN)
            self.assertIsNotNone(
                entry, f'{lang}: home title msgid missing from compiled .mo')
            self.assertTrue(
                entry.msgstr.strip(),
                f'{lang}: home title msgstr is empty in compiled .mo')

    def test_home_renders_german_seo(self):
        from django.core.cache import cache
        cache.delete('site_config')
        resp = self.client.get('/de/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn(
            'SolarOne — Professionelle LED-Sportbeleuchtungslösungen seit 2007',
            content)
        self.assertIn(self.HOME_DESC_PREFIX_DE, content)
        # The English source must NOT leak into the German page head.
        self.assertNotIn(self.HOME_TITLE_EN, content)


class AdminSeedSyncTests(TestCase):
    """后台「保存」→ ``seed_data.json`` 导出链路（N-42）。

    生产（Vercel）的内容源是仓库里提交的 ``seed_data.json``，不是 DB。后台
    保存若不同时把 DB 导出成 seed JSON，本次改动就永远到不了线上 —— 而且旧实现
    只写 ``logger.error``，失败是静默的，可以藏好几周。这组测试锁死四件事：

    1. 链路真的存在（mixins 里的 ``sync_seed_data`` 就是 ``sync_seed_from_db``）；
    2. 5 个内容 admin 的 MRO 真的会走到 mixin（``super()`` 链顺序错了就静默不导出）；
    3. 端到端真的落盘（改 SiteConfig → seed JSON 出现新值）；
    4. 两条异常分支会对管理员发 warning 而不是默默失败，成功时则不发。

    落盘隔离：``seed_sync`` 用 ``settings.BASE_DIR`` 定位输出目录，所以测试把
    BASE_DIR 指到临时目录 —— 真正的 ``seed_data.json``（生产内容源）一次都不碰。
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix='seedsync_')
        (Path(self._tmp) / 'pages').mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_alias_identity(self):
        """mixins 调用的 ``sync_seed_data`` 必须就是 ``sync_seed_from_db``。

        两者一旦分叉（有人把别名重绑到别的函数），后台保存导出的就不再是生产
        真正读取的那份数据 —— 而且没有任何报错。
        """
        from pages import seed_sync
        self.assertIs(seed_sync.sync_seed_data, seed_sync.sync_seed_from_db)

    def test_all_content_admins_have_mixin_before_modeladmin(self):
        """5 个内容 admin 的 MRO 里 CacheClearMixin 必须排在 ModelAdmin 之前。

        排在后面时 ``super().save_model()`` 会直接进 ModelAdmin，mixin 的导出
        永远不执行 —— 表现是「保存成功但线上没变」，最难查的一类。
        """
        for cls in (ProductAdmin, ProjectAdmin, NewsArticleAdmin,
                    SiteConfigAdmin, ProductsPageCardAdmin):
            mro = cls.__mro__
            self.assertIn(CacheClearMixin, mro, cls.__name__)
            self.assertLess(
                mro.index(CacheClearMixin), mro.index(dj_admin.ModelAdmin),
                f'{cls.__name__}: CacheClearMixin 必须排在 ModelAdmin 之前，'
                '否则 save_model 的 super() 链不会经过 mixin。')

    def test_siteconfig_save_writes_seed_json(self):
        """端到端：走 SiteConfigAdmin.save_model → seed JSON 应出现新值。"""
        from pages.models import SiteConfig
        probe = 'QA-PROBE-META-TITLE-1234'
        with self.settings(BASE_DIR=self._tmp):
            cfg = SiteConfig.objects.first() or SiteConfig()
            cfg.meta_title = probe
            cfg.save()
            SiteConfigAdmin(SiteConfig, AdminSite()).save_model(None, cfg, None, False)

            out = Path(self._tmp) / 'seed_data.json'
            self.assertTrue(out.exists(), '保存后没有生成 seed_data.json')
            data = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(
                data['siteconfig'].get('meta_title'), probe,
                'seed_data.json 未包含新值 → 后台保存没有触发导出，改动到不了线上。')

    def test_product_admin_save_path_invokes_sync(self):
        """ProductAdmin 自己重写了 save_model，必须仍通过 super() 链触发导出。"""
        from pages.models import Product
        admin_obj = ProductAdmin(Product, AdminSite())
        obj = mock.MagicMock()
        with mock.patch.object(ProductAdmin, '_sync_product_images'), \
                mock.patch('pages.seed_sync.sync_seed_data') as m:
            admin_obj.save_model(None, obj, None, False)
            obj.save.assert_called_once()
            self.assertTrue(m.called, 'ProductAdmin.save_model 未触发 sync_seed_data')

    def test_project_admin_save_model_forwards_request(self):
        """ProjectAdmin 自己重写了 save_model，且**直接**调用 ``_sync_seed_files()``。

        直接调用的那一处很容易漏掉 ``request`` —— 漏了以后，导出失败或生产环境的
        告警对项目编辑**永远不显示**（默认参数 ``request=None`` → 静默），而其它
        admin 都有告警 —— 最容易被当成「偶发」忽略的一类不一致。
        """
        from pages.models import Project
        req = RequestFactory().get('/admin/')
        obj = mock.MagicMock()
        obj.pdf_file = None
        admin_obj = ProjectAdmin(Project, AdminSite())
        with mock.patch.object(ProjectAdmin, '_sync_project_images'), \
                mock.patch.object(ProjectAdmin, '_sync_seed_files') as m:
            admin_obj.save_model(req, obj, None, False)
        self.assertTrue(m.called, 'ProjectAdmin.save_model 未触发 _sync_seed_files')
        for call in m.call_args_list:
            self.assertTrue(
                call[0] and call[0][0] is req,
                f'_sync_seed_files 调用点漏传 request（告警会静默失效）: {call}')

    def test_delete_model_triggers_sync_with_request(self):
        """后台删除内容也要导出 —— 删掉的产品/项目必须从 seed 里消失。"""
        from pages.models import SiteConfig
        req = RequestFactory().get('/admin/')
        obj = mock.MagicMock()
        with mock.patch('pages.seed_sync.sync_seed_data') as m:
            SiteConfigAdmin(SiteConfig, AdminSite()).delete_model(req, obj)
        obj.delete.assert_called_once()
        self.assertTrue(m.called, 'CacheClearMixin.delete_model 未触发 sync_seed_data')

    def test_save_formset_triggers_sync_with_request(self):
        """内联表单集保存也必须导出（ProjectAdmin 重写了 save_formset）。"""
        from pages.models import Project
        req = RequestFactory().get('/admin/')
        formset = mock.MagicMock()
        with mock.patch('pages.seed_sync.sync_seed_data') as m:
            ProjectAdmin(Project, AdminSite()).save_formset(req, None, formset, False)
        formset.save.assert_called_once()
        self.assertTrue(m.called, 'CacheClearMixin.save_formset 未触发 sync_seed_data')

    def test_production_save_warns_and_skips_export(self):
        """IS_VERCEL 下保存不能假装已上线：要提示，且不碰只读 FS。"""
        req = RequestFactory().get('/admin/')
        with override_settings(IS_VERCEL=True), \
                mock.patch('pages.admin.mixins.messages') as m_msg, \
                mock.patch('pages.seed_sync.sync_seed_data') as m_sync:
            CacheClearMixin()._sync_seed_files(req)
        self.assertTrue(m_msg.warning.called, '生产环境保存必须提示「不会自动上线」')
        self.assertFalse(m_sync.called, '生产环境不应尝试写 seed 文件')

    def test_export_failure_surfaces_as_admin_warning(self):
        """导出失败必须发声 —— 静默失败等于「保存了但没上线」。"""
        req = RequestFactory().get('/admin/')
        with mock.patch('pages.seed_sync.sync_seed_data', return_value=False) as m_sync, \
                mock.patch('pages.admin.mixins.logger') as m_log, \
                mock.patch('pages.admin.mixins.messages') as m_msg:
            CacheClearMixin()._sync_seed_files(req)
        self.assertTrue(m_sync.called)
        self.assertTrue(m_log.error.called, '导出失败至少要留下服务端日志')
        self.assertTrue(m_msg.warning.called, 'sync 返回 False 时必须发 warning')
        self.assertIn('导出失败', m_msg.warning.call_args[0][1])

    def test_successful_export_does_not_warn(self):
        """成功时不能刷 warning，否则管理员会习惯性忽略真警告。"""
        req = RequestFactory().get('/admin/')
        with mock.patch('pages.seed_sync.sync_seed_data', return_value=True), \
                mock.patch('pages.admin.mixins.messages') as m_msg:
            CacheClearMixin()._sync_seed_files(req)
        self.assertFalse(m_msg.warning.called, '导出成功不应产生 warning')


class ImageSitemapAndAltTests(TestCase):
    """Image SEO（零改名）：image sitemap 扩展 + 描述性 alt 文本。

    背景：审计结论——图片**文件名**是很弱的 SEO 信号。两个高价值、零改名的
    改进是（1）此前完全缺失的 image sitemap 扩展，和（2）把画廊 alt 从几乎
    无文本的 ``"<name> — view N"`` 换成带分类/地点的描述。本类只验证这两项
    的**意图（行为）**，不断言实现细节。
    """

    ORIGIN = 'https://www.solaronelighting.com'
    IMAGE_NS = 'http://www.google.com/schemas/sitemap-image/1.1'

    def _sitemap(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode('utf-8')

    # -- 1. image sitemap 扩展 -------------------------------------------
    def test_image_namespace_is_declared(self):
        self.assertIn(f'xmlns:image="{self.IMAGE_NS}"', self._sitemap())

    def test_many_absolute_image_locs(self):
        locs = re.findall(r'<image:loc>(.*?)</image:loc>', self._sitemap())
        self.assertGreater(
            len(locs), 20, f'image:loc 仅 {len(locs)} 条，产品+项目应远超 20')
        for loc in locs:
            self.assertTrue(
                loc.startswith(self.ORIGIN),
                f'image:loc 必须是绝对 URL（前缀 {self.ORIGIN}）: {loc}')
            self.assertNotIn(
                '/media/', loc,
                f'seed 驱动的 sitemap 不应出现 /media/ 路径: {loc}')

    def test_known_product_image_loc_resolves_to_a_real_file(self):
        from django.contrib.staticfiles import finders
        locs = re.findall(r'<image:loc>(.*?)</image:loc>', self._sitemap())
        target = next(
            (loc for loc in locs
             if loc.endswith('/static/images/products/m-series/rt200-m.webp')),
            None,
        )
        self.assertIsNotNone(target, 'm-series 主图未出现在 image:loc 中')
        rel = _strip_static_hash(target[len(self.ORIGIN):])
        self.assertTrue(rel.startswith('/static/'), rel)
        resolved = finders.find(rel[len('/static/'):])
        self.assertIsNotNone(resolved, f'image:loc 指向不存在的静态文件: {rel}')
        self.assertTrue(Path(resolved).is_file())

    def test_every_sitemap_image_loc_resolves_to_a_real_file(self):
        """每个对外广告的 <image:loc> 都必须在磁盘上真实存在。

        ``_static_url`` / ``_dict_product_image_url``（pages/views/utils.py）
        的**既定契约**是「即使文件缺失也返回一个 URL」——这是有意为之，因此
        sitemap 有可能把一个 404 的图片地址投喂给 Google。

        守卫选择在**渲染产物**上检查（而非直接查两个 helper），这样不仅能拦住
        一次改了 seed 却指向缺失资源的编辑，也能拦住未来任何 URL 解析回归。
        这里**不**给生产代码加运行时存在性过滤：基于 ``_find_static`` 的过滤在
        Vercel 的 ``BundledManifestStaticFilesStorage`` 下要先剥 manifest 哈希，
        一旦失手会静默清空整个图片列表——比它要修的潜在风险更糟。
        """
        from pages.views.utils import _find_static, strip_hash_suffix
        locs = re.findall(r'<image:loc>(.*?)</image:loc>', self._sitemap())
        # 反空洞：提取不到任何 loc 时断言方式已失效，必须失败而非假绿。
        self.assertTrue(
            locs, '未从 sitemap 提取到任何 <image:loc>，该测试形同虚设')

        checked = 0
        skipped = 0
        missing = []
        for loc in locs:
            rel = loc[len(self.ORIGIN):] if loc.startswith(self.ORIGIN) else loc
            if rel.startswith('/static/'):
                rel = rel[len('/static/'):]
            if not rel.startswith('images/'):
                # /media/ 或 CDN 绝对 URL —— 不在 static/ 下，单独计数跳过。
                skipped += 1
                continue
            # strip_hash_suffix 作用于「文件名」（生产 Manifest 存储会加
            # _<hash> 后缀），故只对 basename 处理后拼回目录。
            directory, _, basename = rel.rpartition('/')
            clean = strip_hash_suffix(basename)
            rel_clean = f'{directory}/{clean}' if directory else clean
            checked += 1
            if not _find_static(rel_clean):
                missing.append(loc)

        self.assertGreater(
            checked, 0, '没有任何 /static/images/ 下的 loc 被检查到')
        self.assertEqual(
            missing, [],
            f'{len(missing)} 个 <image:loc> 指向磁盘上不存在的文件'
            f'（前 10 条）: {missing[:10]}'
            f'（已检查 {checked} 条，跳过 {skipped} 条非 /static/images/ 条目）')

    def test_image_title_and_caption_carry_real_text(self):
        content = self._sitemap()
        self.assertIn('<image:title>', content)
        self.assertIn('<image:caption>', content)
        # 描述文本来自详情对象（文件名本身没有关键词）——标题应含产品名。
        self.assertIn('<image:title>M Series</image:title>', content)

    # -- 2. 画廊 alt 增强（变更 2 的回归守卫）-----------------------------
    def test_product_gallery_alt_carries_category(self):
        from pages.views.data_loaders import get_product_detail
        product = get_product_detail('m-series', 'en')
        self.assertIsNotNone(product)
        self.assertTrue(product.gallery)
        alt = product.gallery[0]['alt']
        self.assertIn(product.name_t, alt)
        self.assertIn(product.category_display, alt,
                      f'画廊 alt 未带分类文本: {alt!r}')
        self.assertNotEqual(alt, f'{product.name_t} — view 1')

    def test_project_gallery_alt_carries_location(self):
        from pages.views.data_loaders import get_project_detail
        from pages.views.utils import _load_seed
        seed_proj = next(
            (p for p in _load_seed().get('projects', [])
             if p.get('slug') and p.get('location')),
            None,
        )
        self.assertIsNotNone(seed_proj, 'seed 中找不到带 location 的项目')
        project = get_project_detail(seed_proj['slug'], 'en')
        self.assertIsNotNone(project)
        self.assertTrue(project.gallery)
        # 英文下 location_t 即 seed 源值 —— 用 seed 值断言，不硬编码。
        self.assertEqual(project.location_t, seed_proj['location'])
        alt = project.gallery[0]['alt']
        self.assertIn(project.location_t, alt,
                      f'项目画廊 alt 未带地点文本: {alt!r}')
        self.assertNotEqual(alt, f'{project.title_t} — view 1')

    # -- 3. 硬编码英文 alt 已本地化 ---------------------------------------
    def test_ordering_image_alt_is_translated(self):
        content = self.client.get('/fr/products/m-series/').content.decode('utf-8')
        self.assertIn('informations de commande', content)


class ProductPageLayoutSplitTests(TestCase):
    """产品页两套模板，由 ``Product.page_layout`` 决定（后台 Page template）。

    背景：`/products/<slug>/` 曾是"一个模板走天下"，M Series 靠模板里
    `{% if product.slug != 'm-series' %}` 这类硬编码 slug 分支隐藏技术区块 ——
    数据驱动页面上出现了业务特例。现在拆成两个模板：

      * ``overview`` → `product_overview.html`：系列落地页（banner + 主图轮播 +
        文字说明 + 自由图文位），**刻意不含**光束角/尺寸图/参数表/订购表/CTA；
      * ``detail``   → `product_detail.html`：叶子型号页，全量技术参数。

    守卫四件事：① 分流真的由字段驱动（不是 slug 白名单）；② overview 页确实
    没有技术区块，但**保留** canonical/OG/JSON-LD；③ 无状态生产路径
    （`IS_VERCEL` → seed JSON）与本地 DB 路径分流一致（seed 漏字段会让线上
    静默回退成 detail）；④ overview 模板自身的 LCP / 断点 / RTL 契约。
    """

    OVERVIEW_BLOCKS_ABSENT = (
        'class="detail-dimension"',
        'class="detail-energy-data"',
        'class="detail-ordering-table"',
        'class="detail-request-sample"',
        'class="scroll-hint"',
    )

    @classmethod
    def _seed_products(cls):
        from pages.views.utils import _load_seed
        return _load_seed().get('products', [])

    @classmethod
    def _overview_slugs(cls):
        return [p['slug'] for p in cls._seed_products()
                if p.get('page_layout') == 'overview']

    @classmethod
    def _detail_slugs(cls):
        return [p['slug'] for p in cls._seed_products()
                if p.get('page_layout', 'detail') == 'detail']

    def _template_name(self, path):
        """返回该 URL 实际命中的产品模板名（必须恰好一个）。"""
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200, path)
        names = {t.name for t in resp.templates}
        overview = 'product_overview.html' in names
        detail = 'product_detail.html' in names
        self.assertNotEqual(
            overview, detail,
            f'{path} 必须恰好命中一个产品模板，实际：{sorted(names)}')
        return ('product_overview.html' if overview else 'product_detail.html'), resp

    # -- ① 分流由字段驱动 ------------------------------------------------------
    def test_overview_slugs_render_overview_template(self):
        slugs = self._overview_slugs()
        self.assertTrue(slugs, 'seed 里没有任何 page_layout=overview 的产品')
        for slug in slugs:
            name, _ = self._template_name(f'/products/{slug}/')
            self.assertEqual(name, 'product_overview.html',
                             f'{slug} 的 page_layout=overview，却渲染了 {name}')

    def test_detail_slugs_render_detail_template(self):
        slugs = self._detail_slugs()
        self.assertTrue(slugs)
        for slug in slugs:
            name, _ = self._template_name(f'/products/{slug}/')
            self.assertEqual(name, 'product_detail.html',
                             f'{slug} 的 page_layout=detail，却渲染了 {name}')

    def test_unknown_slug_returns_real_404(self):
        """未知 slug 必须返回真 404。

        契约在 v1.8.2 反转：此前 product 为 None 时渲染 product_detail.html 的
        "Product Not Found" 分支并返回 200 —— 软 404 会让 Google 收录任意
        伪造 URL 并判为低质页。现在直接抛 Http404 走 templates/404.html。
        """
        resp = self.client.get('/products/no-such-product-xyz/')
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn('Product Not Found', resp.content.decode('utf-8'))

        # 404 分支不得误伤真实产品页
        slug = self._detail_slugs()[0]
        self.assertEqual(
            self.client.get(f'/products/{slug}/').status_code, 200)

    # -- ② overview 页：无技术区块，但有 SEO head ------------------------------
    def test_overview_pages_drop_technical_blocks(self):
        for slug in self._overview_slugs():
            html = self.client.get(f'/products/{slug}/').content.decode('utf-8')
            body = re.sub(r'<style.*?</style>|<script.*?</script>', '', html,
                          flags=re.S)
            for needle in self.OVERVIEW_BLOCKS_ABSENT:
                self.assertNotIn(
                    needle, body,
                    f'{slug}: 系列首页不应出现技术区块 {needle}')

    def test_overview_pages_keep_seo_head(self):
        for slug in self._overview_slugs():
            html = self.client.get(f'/products/{slug}/').content.decode('utf-8')
            for needle, label in (
                ('rel="canonical"', 'canonical'),
                ('property="og:image"', 'og:image'),
                ('"@type": "Product"', 'Product JSON-LD'),
                ('"@type": "BreadcrumbList"', 'BreadcrumbList JSON-LD'),
                ('class="series-hero-bg"', 'hero banner'),
            ):
                self.assertIn(needle, html, f'{slug}: 缺少 {label}')
            self.assertRegex(
                html, r'class="series-hero-content">\s*<span',
                f'{slug}: hero 区块结构变化（标签 + H1 应在 overlay 内）')

    # -- ③ 双通道一致：seed 必须带 page_layout --------------------------------
    @override_settings(IS_VERCEL=True)
    def test_stateless_path_splits_identically(self):
        """生产走 seed JSON；若导出漏了 page_layout，线上会静默全变 detail。"""
        for slug in self._overview_slugs():
            name, _ = self._template_name(f'/products/{slug}/')
            self.assertEqual(
                name, 'product_overview.html',
                f'无状态路径下 {slug} 落到了 {name} —— '
                'seed_data.json / pages/seed_data.py 里的 page_layout 丢了？')
        name, _ = self._template_name(f'/products/{self._detail_slugs()[0]}/')
        self.assertEqual(name, 'product_detail.html')

    def test_seed_export_carries_page_layout(self):
        """`_product_to_dict`（后台保存 → seed 导出）必须带上 page_layout。"""
        from pages.seed_sync import _product_to_dict
        from pages.models import Product
        # 不入库：只验证导出字典的键集合（TestCase 的测试库是空的）。
        probe = Product(slug='qa-layout-probe', name='QA probe',
                        category='AREA_SITE', description='')
        self.assertIn('page_layout', _product_to_dict(probe))

    # -- ④ 后台字段 ------------------------------------------------------------
    def test_admin_exposes_page_layout_field(self):
        from pages.models import Product
        field = Product._meta.get_field('page_layout')
        self.assertEqual(
            field.default, 'detail',
            '默认必须是 detail（新建产品忘记选 = 全量详情页，不会静默变空壳）')
        self.assertEqual({c[0] for c in field.choices}, {'detail', 'overview'})
        flat = []
        for _title, opts in ProductAdmin.fieldsets:
            for entry in opts['fields']:
                flat.extend(entry if isinstance(entry, (list, tuple)) else (entry,))
        self.assertIn('page_layout', flat, '后台字段组里没有 Page template 选项')

    # -- ⑤ 侧栏层级：系列首页在父级，型号页在子级 -------------------------------
    def test_sidebar_nests_overview_homes_above_their_models(self):
        from pages.views.i18n import (_get_products_sidebar,
                                      _resolve_product_sidebar)
        seed = {p['slug']: p for p in self._seed_products()}
        overview_slugs = set(self._overview_slugs())

        series = [s for cat in _get_products_sidebar('en') for s in cat['series']]
        nested = {s['slug']: [x['slug'] for x in s.get('subseries', [])]
                  for s in series if s.get('subseries')}
        self.assertIn('m-series', nested,
                      'M Series 变成了没有子级的扁平条目')

        for parent_slug, kids in nested.items():
            self.assertIn(parent_slug, seed,
                          f'侧栏父级 {parent_slug} 在 seed 里没有对应产品（会 404）')
            self.assertIn(parent_slug, overview_slugs,
                          f'侧栏父级 {parent_slug} 应是系列首页'
                          '（page_layout=overview）')
            self.assertEqual(
                set(kids),
                {s for s, p in seed.items()
                 if p.get('parent_slug') == parent_slug},
                f'{parent_slug} 的侧栏子级与 seed 的 parent_slug 不一致')

            for kid in kids:
                series_key, sub_key, resolved_parent = \
                    _resolve_product_sidebar(kid, 'en')
                self.assertTrue(series_key, f'{kid} 未解析出父级系列 key')
                self.assertTrue(sub_key, f'{kid} 未解析出子级层 key')
                self.assertEqual(resolved_parent, parent_slug)

            series_key, sub_key, resolved_parent = \
                _resolve_product_sidebar(parent_slug, 'en')
            self.assertTrue(series_key, f'{parent_slug} 未解析出父级 key')
            self.assertEqual((sub_key, resolved_parent), ('', ''),
                             f'{parent_slug} 是系列首页，不应高亮任何子项')

    # -- ⑥ overview 模板自身的源码契约 -----------------------------------------
    def _overview_src(self):
        return (Path(settings.BASE_DIR) / 'templates' /
                'product_overview.html').read_text(encoding='utf-8')

    def test_overview_hero_is_lcp(self):
        tags = re.findall(r'<img[^>]*series-hero-bg[^>]*>', self._overview_src())
        self.assertEqual(len(tags), 1, 'overview hero 应恰好一个 LCP 图')
        self.assertNotIn('loading="lazy"', tags[0])
        self.assertIn('fetchpriority="high"', tags[0])
        self.assertIn('decoding="async"', tags[0])

    def test_overview_keeps_detail_template_breakpoints(self):
        src = self._overview_src()
        self.assertRegex(
            src,
            r'@media \(max-width: 1024px\)\s*\{[^}]*detail-grid\s*\{'
            r'[^}]*grid-template-columns:\s*1fr',
            'overview: detail-grid 折单列断点必须与 detail 模板一致（1024px）')
        self.assertIn('.series-hero { height: 160px; }', src,
                      'overview: ≤767px hero 高度收口丢失')
        self.assertIn('[dir="rtl"] .series-hero-content', src,
                      'overview: RTL 适配丢失')
        self.assertIn('inset-inline-start: 32px', src,
                      'overview: hero 文案定位未用逻辑属性（RTL 会错位）')

    def test_overview_has_no_dead_table_or_cta_css(self):
        src = self._overview_src()
        for dead in ('detail-energy-table', 'detail-ordering-table',
                     'detail-dimension-img', 'detail-beam-angle-img',
                     'detail-request-sample', 'detail-btn', 'scroll-hint'):
            self.assertNotIn(dead, src,
                             f'overview: 残留了无效的 {dead} 样式/类名')

    def test_overview_reuses_shared_carousel_script(self):
        """轮播脚本必须复用 include，不得再内联一份（旧模板的教训）。"""
        src = self._overview_src()
        self.assertIn('{% include "includes/carousel_js.html" %}', src)
        self.assertNotIn('psCarousel.render', src)


class ProductAdminSidebarTreeTests(SimpleTestCase):
    """后台 changelist 镜像前台侧栏：分类 ▸ 系列 ▸ 型号的顺序与父子关系。

    `_sidebar_rank_map()` 以 `_get_products_sidebar('en')` 为唯一事实来源，
    所以侧栏一旦调整，后台列表顺序与面包屑自动跟随 —— 不允许出现两份硬编码。
    """

    def setUp(self):
        # 保险：清掉模块级缓存，确保测试每次从侧栏数据重建
        from pages.admin import product as pa
        pa._SIDEBAR_RANK_MAP_CACHE = None
        self.pa = pa
        self.rank_map = pa._sidebar_rank_map()

    def test_rank_map_covers_every_sidebar_entry(self):
        from pages.views.i18n import _get_products_sidebar
        expected = []
        for cat in _get_products_sidebar('en'):
            for s in cat['series']:
                expected.append(s['slug'])
                expected.extend(x['slug'] for x in s.get('subseries', []))
        self.assertEqual(sorted(self.rank_map), sorted(expected),
                         'rank_map 与侧栏条目集不一致')

    def test_ranks_follow_sidebar_traversal_order(self):
        from pages.views.i18n import _get_products_sidebar
        expected_order = []
        for cat in _get_products_sidebar('en'):
            for s in cat['series']:
                expected_order.append(s['slug'])
                expected_order.extend(x['slug'] for x in s.get('subseries', []))
        actual_order = sorted(self.rank_map, key=lambda slug: self.rank_map[slug][0])
        self.assertEqual(actual_order, expected_order)

    def test_parent_child_grouping_flows_into_ranks(self):
        """子型号的 rank 必须紧跟其系列首页（父子关系可见）。"""
        get_rank = lambda slug: self.rank_map[slug][0]  # noqa: E731
        self.assertLess(get_rank('m-series'), get_rank('fl1m'))
        self.assertLess(get_rank('fl16m'), get_rank('rgb-rgbw'))
        self.assertLess(get_rank('rgb-rgbw'), get_rank('fl9m-rgbw'))
        self.assertLess(get_rank('fl9m-rgbw'), get_rank('accessory'))
        self.assertLess(get_rank('accessory'), get_rank('glare-shield-for-rt410'))

    def test_breadcrumb_labels(self):
        self.assertEqual(self.rank_map['fl4m'][1],
                         ['Area and Site', 'M Series', 'FL4M'])
        self.assertEqual(self.rank_map['fl9m-rgbw'][1],
                         ['Area and Site', 'RGB / RGBW', 'FL9M-RGBW'])
        self.assertEqual(self.rank_map['glare-shield-for-rt410'][1],
                         ['Area and Site', 'Accessory', 'RT410 GS'])
        self.assertEqual(self.rank_map['rt590fl-s'][1],
                         ['Flood Lighting', 'RT590FL-S'])

    def test_sidebar_tree_column_renders_breadcrumb(self):
        from types import SimpleNamespace
        html = str(self.pa.ProductAdmin.sidebar_tree(
            self.pa.ProductAdmin, SimpleNamespace(slug='fl4m')))
        self.assertIn('M Series', html)
        self.assertIn('FL4M', html)
        self.assertIn(' ▸ ', html)

    def test_sidebar_tree_falls_back_for_unknown_slug(self):
        from types import SimpleNamespace
        html = str(self.pa.ProductAdmin.sidebar_tree(
            self.pa.ProductAdmin, SimpleNamespace(slug='not-in-sidebar')))
        self.assertIn('outside sidebar', html)

    def test_detail_only_fieldsets_tagged_for_layout_toggle(self):
        """仅详细页渲染的区块必须带 detail-only 标记，供 page_layout JS 隐藏。"""
        detail_only = [
            name for name, opts in self.pa.ProductAdmin.fieldsets
            if 'detail-only' in (opts or {}).get('classes', ())
        ]
        self.assertIn('Detail-page images (仅在「产品详细页」显示)', detail_only)
        self.assertIn(
            'Energy & Performance Data (17 standard parameters — 仅「产品详细页」)',
            detail_only)
        # overview 也用到的区块不得被标记
        for name, opts in self.pa.ProductAdmin.fieldsets:
            if name in ('Images', 'Ordering Information (订购信息 — 两种模板)'):
                self.assertNotIn('detail-only', (opts or {}).get('classes', ()),
                                 f'{name} 在系列首页也渲染，不能隐藏')

    def test_page_layout_toggle_js_served(self):
        """联动 JS 必须随 Product change form 下发。"""
        self.assertIn('admin/js/page_layout_toggle.js',
                      self.pa.ProductAdmin.Media.js)
        from django.conf import settings
        import os
        self.assertTrue(os.path.exists(os.path.join(
            settings.BASE_DIR, 'static', 'admin', 'js',
            'page_layout_toggle.js')))

    def test_page_layout_widget_and_toggle_js_are_compatible(self):
        """2026-09-26 故障回归：page_layout 在 admin 渲染为 <select>（默认
        控件），而 page_layout_toggle.js 旧版只监听 radio input → 选择
        「系列首页」后 detail-only 区块从不隐藏。JS 必须同时支持 select 与
        radio；若将来把控件换成其他类型，须同步核对该 JS 的选择器。"""
        js = Path(settings.BASE_DIR, 'static', 'admin', 'js',
                  'page_layout_toggle.js').read_text(encoding='utf-8')
        self.assertIn("select[name=\"page_layout\"]", js,
                      'toggle JS 必须监听 <select>（admin 当前实际控件）')
        self.assertIn("input[name=\"page_layout\"]", js,
                      'toggle JS 必须继续兼容 radio 渲染')
        from django import forms as dj_forms
        from pages.admin.product import ProductAdminForm
        widget = ProductAdminForm().fields['page_layout'].widget
        self.assertIsInstance(widget, dj_forms.Select,
                              'page_layout 控件类型变更时须同步 page_layout_toggle.js')

    def test_get_queryset_annotates_sidebar_rank(self):
        """get_queryset 只做 annotate；排序权在 SidebarOrderedChangeList。

        历史事故：把 order_by('_sidebar_rank') 放进 get_queryset/get_ordering，
        会被 Django 内部（ModelAdmin.get_queryset 链、RelatedFieldListFilter.
        field_choices → field.get_choices(ordering=...)）应用到**没有该注解**
        的其它 queryset 上，直接 FieldError → changelist 500。
        """
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.contrib import admin as django_admin
        from django.db.models import Case
        from pages.models import Product
        admin = self.pa.ProductAdmin(Product, django_admin.site)
        rank_map = {
            'bbb': (0, ['C', 'S1']),
            'aaa': (1, ['C', 'S2']),
        }
        fallback = 2

        class FakeQS(list):
            def annotate(self, *a, **k):
                self.annotate_kwargs = k
                return self

            def order_by(self, *fields):
                self.order_fields = fields
                return self

        fake = FakeQS([SimpleNamespace(slug='aaa', pk=1),
                       SimpleNamespace(slug='bbb', pk=2),
                       SimpleNamespace(slug='zzz', pk=3)])
        # 只 patch 掉 ModelAdmin 的基类实现；被测的 ProductAdmin.get_queryset 原样执行
        with patch.object(django_admin.ModelAdmin, 'get_queryset',
                          lambda self, request: fake), \
             patch.object(self.pa, '_SIDEBAR_RANK_MAP_CACHE', rank_map):
            admin.get_queryset(SimpleNamespace())
        self.assertFalse(getattr(fake, 'order_fields', None),
                         'get_queryset 不得自行 order_by（annotation 尚不可用）')
        case = fake.annotate_kwargs['_sidebar_rank']
        self.assertIsInstance(case, Case)
        self.assertEqual(len(case.cases), len(rank_map),
                         '每个侧栏 slug 都要有一个 When 分支')
        # When 分支的顺序与 rank_map 一致（侧栏遍历顺序）
        slugs = [w.condition.children[0][1] for w in case.cases]
        self.assertEqual(slugs, list(rank_map.keys()))
        self.assertEqual(case.default.value, fallback,
                         '不在侧栏里的 slug 必须兜底排到最后')

    def test_get_ordering_not_overridden(self):
        """get_ordering 必须保持默认 —— 列表筛选器会把它借用到别的 queryset 上。"""
        from django.contrib import admin as django_admin
        from pages.models import Product
        admin = self.pa.ProductAdmin(Product, django_admin.site)
        self.assertEqual(admin.get_ordering(None), ('order', 'pk'))

    def test_change_list_orders_by_sidebar_rank(self):
        """ChangeList.get_ordering 在标注过的 queryset 上注入侧栏排序。"""
        from django.contrib import admin as django_admin
        from django.db.models import Value
        from pages.models import Product
        from pages.admin.product import SidebarOrderedChangeList

        admin = self.pa.ProductAdmin(Product, django_admin.site)
        cl = SidebarOrderedChangeList.__new__(SidebarOrderedChangeList)
        cl.params = {}
        cl.model_admin = admin

        qs = Product.objects.none().annotate(_sidebar_rank=Value(0))
        ordering = cl.get_ordering(None, qs)
        self.assertEqual(ordering[0], '_sidebar_rank',
                         '侧栏 rank 必须是第一排序键')
        self.assertIn('pk', ordering, '必须以 pk 兜底保证确定性排序')

    def test_change_list_respects_explicit_column_sort(self):
        """用户点击列排序（?o=...）时，侧栏默认顺序让位。"""
        from django.contrib import admin as django_admin
        from django.db.models import Value
        from pages.models import Product
        from pages.admin.product import SidebarOrderedChangeList

        admin = self.pa.ProductAdmin(Product, django_admin.site)
        cl = SidebarOrderedChangeList.__new__(SidebarOrderedChangeList)
        cl.params = {'o': '1'}
        cl.model_admin = admin
        cl.list_display = ()

        qs = Product.objects.none().annotate(_sidebar_rank=Value(0))
        ordering = cl.get_ordering(None, qs)
        self.assertNotIn('_sidebar_rank', ordering)

    def test_get_queryset_survives_empty_sidebar(self):
        """侧栏构建失败 → admin 绝不能崩，退回默认排序。"""
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.contrib import admin as django_admin
        from pages.models import Product
        admin = self.pa.ProductAdmin(Product, django_admin.site)

        class FakeQS(list):
            def order_by(self, *fields):
                self.order_fields = fields
                return self

        fake = FakeQS([SimpleNamespace(slug='x', pk=1)])
        with patch.object(django_admin.ModelAdmin, 'get_queryset',
                          lambda self, request: fake), \
             patch.object(self.pa, '_SIDEBAR_RANK_MAP_CACHE', {}):
            result = admin.get_queryset(SimpleNamespace())
        self.assertIs(result, fake)
        self.assertFalse(getattr(fake, 'order_fields', None),
                         '侧栏为空时不得追加 _sidebar_rank 排序')


class ProductDetailTemplateIsLeafOnlyTests(SimpleTestCase):
    """detail 模板不再按 slug 特判：硬编码业务特例已随两模板拆分删除。

    M Series 曾靠 `{% if product.slug != 'm-series' %}` / `category !=
    'ACCESSORY'` 在**同一个**模板里隐藏技术区块。既然系列首页现在有独立
    模板，detail 模板里任何 slug/单系列 key 判断都是死条件或新的特例，
    必须挡住（防止特例悄悄长回来）。
    """

    def setUp(self):
        self.src = (Path(settings.BASE_DIR) / 'templates' /
                    'product_detail.html').read_text(encoding='utf-8')

    def test_no_hardcoded_slug_conditional(self):
        self.assertNotIn("product.slug !=", self.src,
                         'detail 模板里又出现了按 slug 特判的隐藏逻辑')
        self.assertNotIn("product.slug ==", self.src)

    def test_no_category_conditional(self):
        self.assertNotIn("product.category !=", self.src,
                         'detail 模板里又出现了按 category 特判的隐藏逻辑')

    def test_no_single_series_bottom_align_special_case(self):
        """detail-grid-bottom-align 只应为 RT410 保留（M 已迁往 overview）。"""
        hits = re.findall(r'active_series == \'([A-Z0-9_]+)\'',
                          self.src)
        self.assertEqual(sorted(set(hits)), ['RT410_SERIES'],
                         f'detail 模板的单系列特判集合变化：{sorted(set(hits))}')

    def test_bottom_align_class_still_defined(self):
        self.assertIn('.detail-grid-bottom-align', self.src)


class P1ContactFormConsistencyTests(SimpleTestCase):
    """Contact form layout/control styles must use the shared semantic classes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(settings.BASE_DIR)
        cls.template = (base / 'templates' / 'contact.html').read_text(encoding='utf-8')
        cls.css = (base / 'static' / 'css' / 'base.css').read_text(encoding='utf-8')

    def test_contact_form_uses_shared_layout_classes(self):
        form = self.template.split('id="contactForm"', 1)[1].split('</form>', 1)[0]
        self.assertIn('class="contact-form"', self.template)
        self.assertNotIn('style="display: flex; flex-direction: column; gap: 20px;"', form)
        self.assertEqual(form.count('class="contact-form-field"'), 5)
        self.assertEqual(form.count('class="contact-form-label"'), 5)
        self.assertEqual(form.count('class="contact-form-control'), 5)

    def test_contact_form_class_values_preserve_existing_design(self):
        for selector, required in (
            ('.contact-form {', 'gap: 20px;'),
            ('.contact-form-field {', 'gap: 6px;'),
            ('.contact-form-control {', 'padding: 12px 16px;'),
            ('.contact-form-textarea {', 'min-height: 100px;'),
        ):
            match = re.search(re.escape(selector) + r'[^}]*}', self.css)
            self.assertIsNotNone(match, f'缺少 {selector} 规则')
            self.assertIn(required, match.group(0))



class P0StyleConsistencyTests(TestCase):
    """v1.6.3 P0 前端风格一致性修复防回归（设计审计 P0 三项）。

    1. P0-1: cookie 横幅曾引用未定义的 var(--surface) → 背景 transparent 透底。
    2. P0-2: admin 曾直接注入 --accent（同 specificity + 后发 → 冲掉 light
       压暗覆盖），且 --accent 有 4 个分歧字面值、btn hover 与 accent 同色；
       现约定 admin 只注入 --accent-brand，其余一律由 base.css 推导。
    3. P0-3: 字体栈五处一致（critical / base.css / seed py+json / models
       默认）；渲染用到的字重必须有自托管 face 且文件真实存在。
    按项目惯例全部读源码文件断言（部署产物由 collectstatic 生成）。
    """

    CANONICAL_FF = (
        "'Inter', system-ui, -apple-system, BlinkMacSystemFont, "
        "'PingFang SC', 'Hiragino Sans GB', "
        "'Microsoft YaHei', 'Source Han Sans CN', 'Noto Sans CJK SC', "
        "Roboto, sans-serif"
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(settings.BASE_DIR)
        cls.css = (base / 'static' / 'css' / 'base.css').read_text(
            encoding='utf-8')
        cls.base_html = (base / 'templates' / 'base.html').read_text(
            encoding='utf-8')
        cls.fonts_css = (base / 'static' / 'css' / 'fonts.css').read_text(
            encoding='utf-8')
        cls.seed = json.loads(
            (base / 'seed_data.json').read_text(encoding='utf-8'))
        cls.seed_py = (base / 'pages' / 'seed_data.py').read_text(
            encoding='utf-8')

    @staticmethod
    def _norm_ff(value):
        """归一化字体栈：剥引号与空白，只比 token 序列。

        CSS 源是双引号多行、py/json 是单引号单行 —— 格式差异不是漂移。
        """
        return re.sub(r"[\s'\"]+", '', value)

    # ---- P0-1 ----
    def test_cookie_banner_uses_defined_surface_token(self):
        self.assertNotIn('var(--surface)', self.base_html,
                         '--surface 从未定义 → 背景 transparent 透底')
        self.assertRegex(
            self.base_html,
            r'id="cookie-banner"[^>]*background:var\(--bg-raised\)',
            'cookie 横幅背景必须用双主题均已定义的 --bg-raised')

    # ---- P0-2 ----
    def test_admin_injects_accent_brand_not_accent(self):
        self.assertIn('--accent-brand: {{ config.accent_color }}',
                      self.base_html, 'admin 必须只注入 --accent-brand')
        self.assertNotRegex(
            self.base_html,
            r'--accent:\s*\{\{\s*config\.accent_color',
            'admin 直接写 --accent 会冲掉 light 主题压暗覆盖（历史 bug）')

    def test_accent_derivation_gated_and_from_brand(self):
        self.assertIn('--accent-brand: #0088FF', self.css,
                      'base.css 默认 brand 必须等于 SiteConfig 默认值')
        self.assertIn('var(--accent-brand, #0088FF)', self.css,
                      '--accent 必须由 --accent-brand 推导')
        self.assertIn('@supports (color: color-mix', self.css,
            'color-mix 派生必须包 @supports：自定义属性不做语法校验，'
            '裸写会让老浏览器把字面量代入消费属性 → 整条声明失效')
        self.assertRegex(
            self.css,
            r'\[data-theme="light"\]\s*\{[^}]*--accent:\s*'
            r'color-mix\(in srgb, var\(--accent-brand',
            'light 主题 accent 必须从 --accent-brand 压暗派生')

    def test_accent_defaults_consistent_no_stale_literals(self):
        self.assertEqual(self.seed['siteconfig']['accent_color'], '#0088FF')
        self.assertIn('--accent-brand:#0088FF', self.base_html,
                      'critical CSS 默认值必须与 seed/base.css 一致')
        css_no_comment = re.sub(r'/\*.*?\*/', '', self.css, flags=re.DOTALL)
        for stale in ('#0077ED', '#0062C4', '#0090FF', '#005BB5',
                      '#004A99'):
            self.assertNotIn(stale, css_no_comment,
                             f'旧 accent 字面 {stale} 残留在 base.css')

    def test_btn_hover_follows_accent_token(self):
        m = re.search(r'\.btn-primary:hover\s*\{[^}]*\}', self.css)
        self.assertIsNotNone(m, '.btn-primary:hover 规则缺失')
        # 先剥注释：规则内的说明注释会提到旧字面量，只断言真实声明
        block = re.sub(r'/\*.*?\*/', '', m.group(0), flags=re.DOTALL)
        self.assertIn('var(--accent-hover)', block,
            'hover 必须走派生 token（写死 #0088FF 与默认 accent 同色 → 无色差）')
        self.assertNotIn('#0088FF', block)

    # ---- P0-3 ----
    def _extract_ff_stack(self, source, var):
        m = re.search(rf'{var}:\s*([^;]+);', source)
        self.assertIsNotNone(m, f'{var} 未找到')
        return m.group(1)

    def test_font_stack_aligned_across_all_sources(self):
        canon = self._norm_ff(self.CANONICAL_FF)
        for field in ('font_family_body', 'font_family_heading'):
            self.assertEqual(
                self._norm_ff(self.seed['siteconfig'][field]), canon,
                f'seed_data.json {field} 与 canonical 不一致')
            py_val = re.search(rf'"{field}":\s*"([^"]+)"', self.seed_py)
            self.assertIsNotNone(py_val, f'seed_data.py 缺 {field}')
            self.assertEqual(self._norm_ff(py_val.group(1)), canon,
                             f'seed_data.py {field} 与 canonical 不一致')
        crit = self.base_html.split('id="critical-css"', 1)[1]
        for var in ('--ff-display', '--ff-body'):
            self.assertEqual(
                self._norm_ff(self._extract_ff_stack(crit, var)), canon,
                f'critical CSS {var} 与 canonical 不一致')
        root = re.search(r':root\s*\{(.*?)\n\s*\}', self.css, re.DOTALL)
        self.assertIsNotNone(root, 'base.css :root 块缺失')
        for var in ('--ff-display', '--ff-body'):
            self.assertEqual(
                self._norm_ff(self._extract_ff_stack(root.group(1), var)),
                canon, f'base.css {var} 与 canonical 不一致')

    def test_no_space_grotesk_in_render_path(self):
        self.assertNotIn('Space Grotesk', self.base_html,
                         'critical CSS 不得引用 Space Grotesk（首帧与 admin '
                         '注入不一致且白下载 9 个 woff2）')
        self.assertNotIn('Space Grotesk', self.css)

    def test_cjk_fallback_present_in_base_css(self):
        for token in ('PingFang SC', 'Noto Sans CJK', 'Microsoft YaHei',
                      '-apple-system'):
            self.assertIn(token, self.css)

    def test_fonts_css_covers_rendered_weights(self):
        for family, weight in (('Inter', '500'), ('Inter', '700'),
                               ('IBM Plex Mono', '500'),
                               ('IBM Plex Mono', '600')):
            self.assertRegex(
                self.fonts_css,
                rf"font-family:\s*'{re.escape(family)}';\s*"
                rf"font-style:\s*normal;\s*font-weight:\s*{weight};",
                f'fonts.css 缺 {family} {weight} @font-face')

    def test_every_fonts_css_file_exists_and_is_woff2(self):
        fonts_dir = Path(settings.BASE_DIR) / 'static' / 'fonts'
        urls = re.findall(r'url\(\.\./fonts/([^)]+)\)', self.fonts_css)
        self.assertGreaterEqual(len(urls), 52,
                                'fonts.css 声明的 face 数量异常下降')
        for fname in urls:
            fpath = fonts_dir / fname
            self.assertTrue(fpath.exists(), f'声明了但文件不存在：{fname}')
            self.assertEqual(fpath.read_bytes()[:4], b'wOF2',
                             f'{fname} 不是合法 woff2')

    def test_model_defaults_match_canonical(self):
        from pages.models import SiteConfig
        for field in ('font_family_body', 'font_family_heading'):
            default = SiteConfig._meta.get_field(field).default
            self.assertEqual(self._norm_ff(default),
                             self._norm_ff(self.CANONICAL_FF),
                             f'models.py {field} 默认值与 canonical 不一致')



class P2RadiusTokenTests(SimpleTestCase):
    """P2-1: shared control geometry uses one radius token."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'base.css').read_text(
            encoding='utf-8')

    def test_control_radius_token_is_defined_once(self):
        self.assertEqual(self.css.count('--radius-control: 8px;'), 1)
        self.assertIn('    --radius-control: 8px;', self.css)

    def test_shared_controls_use_radius_token(self):
        selectors = (
            '.theme-toggle',
            '.lang-switch-btn',
            '.lang-switch-menu',
            '.panel-actions .lang-switch-btn',
            '.contact-form-control',
            r'.form-group input,\s*\.form-group textarea',
            '.form-submit .btn-primary',
        )
        for selector in selectors:
            match = re.search(
                rf'{selector}\s*\{{(?P<body>[^}}]*)\}}',
                self.css,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, f'缺少公共控件规则：{selector}')
            self.assertIn('border-radius: var(--radius-control);', match.group('body'))

    def test_radius_token_is_not_used_for_page_specific_shapes(self):
        for selector in ('.hero-slide', '.project-card', '.product-card',
                         '.sidebar-nav-parent', '.contact-whatsapp'):
            match = re.search(
                rf'{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}',
                self.css,
                flags=re.DOTALL,
            )
            if match:
                self.assertNotIn(
                    'border-radius: var(--radius-control);', match.group('body'),
                    f'页面特有形状不应被控制类 token 接管：{selector}')

    # P1-1 侧栏样式统一暂不纳入回归契约：详情页仍保留有意差异。


class P2SectionLabelTests(SimpleTestCase):
    """P2-4: shared section labels preserve their page-specific spacing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(settings.BASE_DIR)
        cls.css = (base / 'static' / 'css' / 'base.css').read_text(encoding='utf-8')
        cls.projects = (base / 'templates' / 'projects.html').read_text(encoding='utf-8')
        cls.news = (base / 'templates' / 'news.html').read_text(encoding='utf-8')
        cls.news_detail = (base / 'templates' / 'news_detail.html').read_text(encoding='utf-8')
        cls.about = (base / 'templates' / 'about.html').read_text(encoding='utf-8')
        cls.contact = (base / 'templates' / 'contact.html').read_text(encoding='utf-8')

    def test_compact_modifier_preserves_twelve_pixel_spacing(self):
        self.assertRegex(
            self.css,
            r'\.section-accent-label--compact\s*\{\s*margin-bottom:\s*12px;\s*\}',
        )
        for template in (self.projects, self.news):
            self.assertIn(
                'class="section-accent-label section-accent-label--compact"',
                template,
            )

    def test_existing_label_variants_remain_unchanged(self):
        self.assertIn('class="section-accent-label"', self.about)
        self.assertIn('style="font-family: var(--ff-mono); font-size: 11px;', self.contact)
        self.assertIn('margin-bottom: 16px;', self.contact)
        self.assertNotIn('section-accent-label--compact', self.about)
        self.assertNotIn('section-accent-label--compact', self.contact)

    def test_news_detail_media_is_a_bento_grid_with_object_fit_cover(self):
        """详情页媒体区是 bento 网格：左大图跨两行，右侧小图上下叠放。

        v1.6.4 用户明确要求主图缩小、三张图按 bento 排布、允许裁剪铺满以
        减少桌面端滚动。本守卫把这一契约钉在 `news_detail.html` 源码上。
        """
        self.assertIn('.news-detail-media', self.news_detail)
        self.assertIn('.news-detail-media-cell--large', self.news_detail)
        self.assertIn('grid-template-columns:', self.news_detail)
        self.assertIn('grid-row: 1 / 3', self.news_detail)
        self.assertIn('object-fit: cover', self.news_detail)

    def test_list_card_covers_render_the_uniform_16x9_contract(self):
        """列表卡片封面统一 16:9 —— 改版后 object-fit: cover 是故意的。"""
        html = self.news
        self.assertIn(
            'aspect-ratio: 16 / 9', html,
            '列表卡片必须统一 16:9 封面（网格版式契约）')
        self.assertIn('object-fit: cover', html)
        # 反空洞：封面规则与卡片标记都得真实存在
        self.assertIn('.news-card-cover img', html)
        self.assertIn('class="news-card-cover"', html)


# ---------------------------------------------------------------------------
# P3-1：生产静态构建闸门（collectstatic → staticfiles.json → 索引 → public/）
# ---------------------------------------------------------------------------
# 生产用 BundledManifestStaticFilesStorage，`public/static/` 里只发布内容哈希
# 文件名；`pages/static_index_data.HASHED_FILES` 是运行期唯一能拿到「原名 → 哈希名」
# 的通道。若 collectstatic 失败（或清单里没有 paths）而构建继续，线上每个
# {% static %} 都退回未哈希 URL → 全站资源 404。下面这组测试钉死三件事：
#   ① pages/static_index.py 严格模式（--require-manifest，build.sh 用）必须 fail closed
#   ② 默认宽松模式仍可用（CI 拿源码 static/ 生成索引，那里没有清单）
#   ③ build.sh 两处失败路径都必须 exit 1，而不是告警后继续
class P3StaticBuildGateTests(SimpleTestCase):
    """P3-1: the production static build must fail closed, never ship hash-less."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(settings.BASE_DIR)
        cls.build_sh = (base / 'build.sh').read_text(encoding='utf-8')
        cls.ci_yml = (base / '.github' / 'workflows' / 'ci.yml').read_text(
            encoding='utf-8')
        cls.verify_script = (base / 'scripts' / 'verify_static_build.py').read_text(
            encoding='utf-8')

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _segment(source, start_marker, end_marker):
        start = source.index(start_marker)
        return source[start:source.index(end_marker, start)]

    @staticmethod
    def _run_main(argv):
        """跑 pages.static_index.main()，吞掉它写到 stderr 的提示。"""
        import contextlib
        import io

        from pages.static_index import main
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(argv)
        return code, err.getvalue()

    @staticmethod
    def _manifest(paths):
        return json.dumps({'paths': paths, 'version': '1.1', 'hash': 'deadbeef'})

    def _fake_root(self, tmp, manifest_body=None):
        """建一个最小 collectstatic 产物目录，返回 (root, out)。"""
        root = Path(tmp, 'staticfiles')
        Path(root, 'css').mkdir(parents=True)
        Path(root, 'css', 'base.css').write_text('body{}', encoding='utf-8')
        if manifest_body is not None:
            Path(root, 'staticfiles.json').write_text(manifest_body, encoding='utf-8')
        return str(root), str(Path(tmp, 'pages', 'static_index_data.py'))

    # ---- ① 严格模式（build.sh / verify 脚本走这条）------------------------
    def test_strict_mode_fails_when_root_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp, 'pages', 'static_index_data.py'))
            code, err = self._run_main(
                ['--root', str(Path(tmp, 'nope')), '--out', out, '--require-manifest'])
            self.assertEqual(code, 2, '缺 staticfiles/ 必须非零退出（fail closed）')
            self.assertIn('ERROR', err)
            self.assertFalse(Path(out).exists(), '失败时不得留下半成品索引')

    def test_strict_mode_fails_when_manifest_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = self._fake_root(tmp)
            code, err = self._run_main(
                ['--root', root, '--out', out, '--require-manifest'])
            self.assertEqual(code, 2, '缺 staticfiles.json 必须非零退出')
            self.assertIn('ERROR', err)
            self.assertFalse(Path(out).exists())

    def test_strict_mode_fails_when_manifest_has_no_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = self._fake_root(tmp, self._manifest({}))
            code, err = self._run_main(
                ['--root', root, '--out', out, '--require-manifest'])
            self.assertEqual(code, 2, '清单里没有 paths 等于没有哈希名')
            self.assertIn('ERROR', err)
            self.assertFalse(Path(out).exists())

    def test_strict_mode_writes_index_when_manifest_is_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = self._fake_root(
                tmp, self._manifest({'css/base.css': 'css/base.280e03822c88.css'}))
            code, err = self._run_main(
                ['--root', root, '--out', out, '--require-manifest'])
            self.assertEqual(code, 0, err)
            namespace = {}
            exec(compile(Path(out).read_text(encoding='utf-8'), out, 'exec'), namespace)
            self.assertEqual(namespace['HASHED_FILES'],
                             {'css/base.css': 'css/base.280e03822c88.css'})

    # ---- ② 默认宽松模式：CI 从源码 static/ 生成索引必须仍然可用 -----------
    def test_default_mode_still_generates_index_for_source_static(self):
        """ci.yml `--root static` —— 源码目录本来就没有 collectstatic 产物。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp, 'pages', 'static_index_data.py'))
            code, _err = self._run_main(
                ['--root', str(Path(settings.BASE_DIR, 'static')), '--out', out])
            self.assertEqual(code, 0, 'CI 从 static/ 生成索引必须仍然成功（默认宽松）')
            namespace = {}
            exec(compile(Path(out).read_text(encoding='utf-8'), out, 'exec'), namespace)
            self.assertEqual(namespace['HASHED_FILES'], {},
                             '源码 static/ 没有清单 → 哈希映射为空，只有目录索引')
            self.assertIn('css', namespace['STATIC_INDEX']['dirs'])

    def test_default_mode_keeps_writing_index_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = self._fake_root(tmp)
            code, _err = self._run_main(['--root', root, '--out', out])
            self.assertEqual(code, 0, '未加开关时必须保持历史宽松行为')
            self.assertTrue(Path(out).exists())

    # ---- ③ build.sh 的失败语义 -------------------------------------------
    def test_build_sh_collectstatic_failure_is_fatal(self):
        segment = self._segment(self.build_sh, 'Running collectstatic',
                               '[build.sh] collectstatic done')
        self.assertIn('exit 1', segment,
                      'collectstatic 失败必须中断构建（fail closed）')
        self.assertNotIn('WARNING: collectstatic failed', self.build_sh,
                         '旧的「只告警然后继续」语义必须彻底删除')

    def test_build_sh_static_index_step_is_strict_and_fatal(self):
        segment = self._segment(self.build_sh, 'Generating static index',
                               'Creating public/ directory')
        self.assertIn('--require-manifest', segment,
                      'build.sh 必须以严格模式生成索引（缺清单＝构建失败）')
        self.assertIn('exit 1', segment, '索引生成失败必须中断构建')

    def test_ci_index_generation_stays_permissive(self):
        """CI 不能加 --require-manifest：它从源码 static/ 生成，本来就没有清单。"""
        self.assertIn('--root static --out pages/static_index_data.py', self.ci_yml)
        self.assertNotIn('--require-manifest', self.ci_yml)

    def test_verify_script_exercises_the_production_storage_path(self):
        self.assertIn('--require-manifest', self.verify_script)
        self.assertIn('"VERCEL"', self.verify_script,
                      '冒烟脚本必须用 VERCEL=1 触发生产静态存储后端')


# ---------------------------------------------------------------------------
# P3-2：可视化评审工具的覆盖面（每种页面模板 × 深/浅双主题）
# ---------------------------------------------------------------------------
# visual_review.py 是「改完先看图」的唯一手段，它最危险的失效方式不是崩，
# 而是**静默缩水**：少跑一个页面、少跑一套主题，报告照样生成得漂漂亮亮，
# 看的人却以为已经全看过了。所以把三件事钉成断言：
#   ① 默认路径覆盖 pages/urls.py 里每一个公开页面视图，且不指向 301 别名
#   ② 主题注入与 templates/base.html 的 localStorage['theme'] 契约一致
#   ③ 页面非 200 / 主题没生效必须非零退出，而不是安静地截一张没用的图
class P3VisualReviewCoverageTests(SimpleTestCase):
    """P3-2: the visual review tool must cover every page template + both themes."""

    # robots.txt / sitemap.xml 不是给人看的 HTML；diagnostic 只在 DEBUG=True 存在
    # （且限 STAFF）；product_series 是历史 URL 的 301 别名（规范 URL 是
    # /products/<slug>/），评审默认路径不应落在它上面。
    # news_feed 是 RSS 2.0 XML 输出（B4），同属机器可读端点，没有可截图的人眼
    # HTML 评审价值，故同样排除在默认视觉评审路径之外。
    NON_PAGE_ROUTES = {'robots_txt', 'sitemap_xml', 'diagnostic', 'product_series',
                       'news_feed'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(settings.BASE_DIR)
        script = base / 'scripts' / 'e2e' / 'visual_review.py'
        cls.src = script.read_text(encoding='utf-8')
        cls.base_html = (base / 'templates' / 'base.html').read_text(encoding='utf-8')
        cls.seed = json.loads((base / 'seed_data.json').read_text(encoding='utf-8'))
        cls.module = cls._load_module(script)

    @staticmethod
    def _load_module(path):
        """按路径加载模块：visual_review.py 顶层只有常量，import 无副作用。"""
        import importlib.util

        spec = importlib.util.spec_from_file_location('visual_review_under_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # ---- ① 页面模板覆盖 ---------------------------------------------------
    def test_default_paths_cover_every_public_page_view(self):
        """每条公开路由都必须有默认评审路径（新增页面忘了加 → 这条会红）。"""
        from django.urls import resolve

        from pages.urls import urlpatterns

        covered = {resolve(p).url_name for p in self.module.DEFAULT_PATHS}
        public = {getattr(p, 'name', None) for p in urlpatterns}
        public = {n for n in public if n} - self.NON_PAGE_ROUTES
        self.assertEqual(
            public - covered, set(),
            f'这些页面没有任何默认评审路径：{sorted(public - covered)}')
        self.assertNotIn('product_series', covered,
                         '默认路径不应落到 301 别名路由（规范 URL 是 /products/<slug>/）')

    def test_default_paths_are_well_formed_and_unique(self):
        paths = self.module.DEFAULT_PATHS
        self.assertEqual(len(paths), len(set(paths)), '默认路径不能重复')
        for path in paths:
            self.assertTrue(path.startswith('/'), f'路径必须以 / 开头：{path}')
            self.assertTrue(path.endswith('/'), f'路径必须以 / 结尾：{path}')

    def test_project_detail_default_path_points_at_real_seed_content(self):
        """详情页 slug 必须来自 seed_data.json，否则空库渲染出来是 404。"""
        slugs = {project['slug'] for project in self.seed['projects']}
        detail_paths = [p for p in self.module.DEFAULT_PATHS
                        if re.fullmatch(r'/projects/[^/]+/', p)]
        self.assertTrue(detail_paths, '默认路径必须包含一个项目详情页')
        for path in detail_paths:
            slug = path.strip('/').split('/')[1]
            self.assertIn(slug, slugs,
                          f'{path} 的 slug 不在 seed_data.json 里 → 评审会截到 404')

    # ---- ② 主题轴 ---------------------------------------------------------
    def test_both_themes_are_reviewed_and_labelled(self):
        self.assertEqual(tuple(self.module.THEMES), ('dark', 'light'),
                         '必须同时评审深色与浅色（dark 是 base.html 的默认主题）')
        self.assertEqual(set(self.module.THEME_LABELS), set(self.module.THEMES),
                         'THEMES 与 THEME_LABELS 必须一一对应，否则报告渲染 KeyError')

    def test_theme_injection_matches_base_html_contract(self):
        """主题靠 base.html 读 localStorage['theme']；评审脚本必须注入同一个键。"""
        self.assertEqual(self.module.THEME_STORAGE_KEY, 'theme')
        self.assertIn(f"localStorage.getItem('{self.module.THEME_STORAGE_KEY}')",
                      self.base_html,
                      'base.html 的主题初始化脚本改了 → 评审脚本的注入键要同步')
        self.assertIn('data-theme', self.base_html)
        self.assertIn('%s', self.module.THEME_INIT_JS,
                      'THEME_INIT_JS 必须留出插值位给 storage key / 主题名')
        self.assertIn('add_init_script', self.src,
                      '主题必须在文档开始前注入（点按钮在移动端不可靠）')

    # ---- ③ 失败必须响 -----------------------------------------------------
    def test_non_200_and_theme_drift_are_fatal(self):
        self.assertIn('if d.get("httpStatus") != 200:', self.src,
                      '页面非 200 必须记为问题（否则 404 也照样出报告）')
        self.assertIn('if d.get("theme") != theme:', self.src,
                      '主题未生效必须记为问题（否则深浅两张图一模一样）')
        self.assertIn('return 1', self.src, '有问题时必须非零退出')
        self.assertIn('sys.exit(main())', self.src, '退出码必须真的传出去')


# ---------------------------------------------------------------------------
# 新闻卡片图集：seed / DB 两条路径必须给出同一套 `article.images` 接口，
# 且图片按原始尺寸展示（不裁剪、不放大）。
#
# 背景：news.html 原先用一张 `NewsArticle.image` + `aspect-ratio: 16/9` +
# `object-fit: cover`。新闻素材常只有 600px 左右，拉满卡片必然糊，还会切掉
# 画面。改成「每张文章卡片渲染全部 NewsImage，按原始比例、受限宽度」之后，
# 下面这些断言替代原来的版式契约。
# ---------------------------------------------------------------------------
class NewsGalleryLayoutTests(TestCase):
    """新闻图集排版：双通道一致 + 详情页原尺寸渲染。

    v1.6.3 起列表卡片只渲染一张统一 16:9 封面（裁剪是网格版式的核心诉求），
    图集照片全部迁到详情页 `/news/<slug>/` 原尺寸渲染 —— 本类的 figure 断言
    随之全部指向详情页；列表侧的 16:9 契约由
    ``P2SectionLabelTests.test_list_card_covers_render_the_uniform_16x9_contract``
    钉住。
    """

    CELL_RE = re.compile(r'<figure class="news-detail-media-cell[^"]*">.*?</figure>', re.S)
    IMG_RE = re.compile(r'<img\b[^>]*>')

    FAKE = [
        {
            'image': 'images/news/qa-news-a.jpg',
            'alt': 'QA alt A — apron at dusk',
            'caption': 'QA caption A',
            'order': 0,
            'width': 581,
            'height': 380,
        },
        {
            'image': 'images/news/qa-news-b.jpg',
            'alt': 'QA alt B — ground level assembly',
            'caption': 'QA caption B',
            'order': 1,
            'width': 600,
            'height': 337,
        },
    ]

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _cells(html):
        return NewsGalleryLayoutTests.CELL_RE.findall(html)

    @staticmethod
    def _imgs(html):
        return NewsGalleryLayoutTests.IMG_RE.findall(html)

    # ---- ① seed JSON 路径 -------------------------------------------------
    @override_settings(IS_VERCEL=True)
    def test_seed_json_renders_all_three_photos_with_alt_and_dimensions(self):
        """生产（无状态）路径：cover + 2 gallery 共 3 张图都要进 bento 网格。"""
        seed = {'news': [{
            'slug': 'qa-news',
            'title': 'QA NewsTitleXYZ',
            'summary': 's',
            'content': 'c',
            'image': 'images/news/qa-news-cover.jpg',
            'images': NewsGalleryLayoutTests.FAKE,
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
        }]}
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            resp = self.client.get(reverse('news_detail', args=['qa-news']))

        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')

        self.assertIn('QA NewsTitleXYZ', html, 'seed 文章没有被渲染')
        cells = self._cells(html)
        self.assertEqual(len(cells), 3,
                         'seed 里有 3 张图（cover+2 gallery），bento 必须渲染 3 个 cell')
        joined = '\n'.join(cells)
        for needle in ('images/news/qa-news-cover.jpg', 'images/news/qa-news-a.jpg',
                       'images/news/qa-news-b.jpg', 'QA alt A — apron at dusk',
                       'QA alt B — ground level assembly'):
            self.assertIn(needle, joined, f'图集里缺少：{needle}')
        # 反空洞：width / height / lazy 不能是空字符串占位
        self.assertIn('width="581"', joined)
        self.assertIn('height="380"', joined)
        self.assertIn('loading="lazy"', joined)

    @override_settings(IS_VERCEL=True)
    def test_seed_entry_without_images_key_renders_single_large_cell(self):
        """只有旧 `image` 键的 seed 条目：详情页只渲染一个左大图 cell。"""
        seed = {'news': [{
            'slug': 'qa-legacy-news',
            'title': 'QA LegacyNewsXYZ',
            'summary': 's',
            'content': 'c',
            'image': 'images/news/qa-legacy.jpg',
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
        }]}
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            resp = self.client.get(reverse('news_detail', args=['qa-legacy-news']))

        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertIn('QA LegacyNewsXYZ', html)
        cells = self._cells(html)
        self.assertEqual(len(cells), 1, '没有 images 时详情页应只渲染一个 cell')
        self.assertIn('news-detail-media-cell--large', cells[0])
        self.assertIn('images/news/qa-legacy.jpg', cells[0])

        # 列表页不受影响：旧条目照样渲染出卡片封面（16:9 裁剪是故意的）
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            list_resp = self.client.get(reverse('news'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertIn('class="news-card-cover"',
                      list_resp.content.decode('utf-8'))

    # ---- ② DB 路径 --------------------------------------------------------
    def test_db_path_renders_all_three_images_with_correct_urls(self):
        from pages.models import NewsArticle, NewsImage

        article = NewsArticle.objects.create(
            slug='qa-news-db',
            title='QA DB NewsTitleXYZ',
            summary='s',
            content='c',
            published_at='2026-02-02T00:00:00Z',
            is_published=True,
        )
        article.image = 'news/qa-news-cover.jpg'
        article.save()
        for spec in (
            dict(order=0, image='news/qa-news-a.jpg',
                 alt_text='QA alt A — apron at dusk',
                 caption='QA caption A', width=581, height=380),
            dict(order=1, image='news/qa-news-b.jpg',
                 alt_text='QA alt B — ground level assembly',
                 caption='QA caption B', width=600, height=337),
        ):
            NewsImage.objects.create(article=article, **spec)

        resp = self.client.get(reverse('news_detail', args=['qa-news-db']))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')

        cells = self._cells(html)
        self.assertEqual(
            len(cells), 3,
            f'DB 路径必须渲染出 3 个 bento cell，实际 {len(cells)}')

        srcs = []
        for idx, cell in enumerate(cells):
            img = re.search(r'<img\b[^>]*>', cell)
            self.assertIsNotNone(img, 'cell 里必须有 img')
            tag = img.group(0)
            # 大图（封面，bento 左格）eager 利于 LCP；图集图 lazy。
            if idx == 0:
                self.assertIn('loading="eager"', tag,
                              '首格大图应 eager 渲染封面')
            else:
                self.assertIn('loading="lazy"', tag,
                              '图集格应 lazy 渲染')
            self.assertRegex(tag, r'src="/media/news/qa-news-(cover|[ab])\.jpg"',
                             f'图片 URL 不对：{tag}')
            srcs.append(tag)
        # 反空洞：三张图的 src 必须真的不同
        self.assertEqual(len(set(srcs)), 3, '三张图必须渲染成不同的 src')
        self.assertIn('QA alt A — apron at dusk', cells[1])
        self.assertIn('QA alt B — ground level assembly', cells[2])


class NewsTranslationTests(TestCase):
    """/news/ 的多语言守卫（2026-09-25 建）。

    ``NewsArticle.translations`` 是新加的第三条翻译路径 —— 它的特殊之处是
    **两条数据路径都必须带译文**：

      * 本地（``_get_news_from_db``）走模型，模板读 ``article.<field>_t``；
      * Vercel（``_get_news_from_json``）走 seed dict，同一个模板。

    这两个坑都是实测踩出来的，本守卫就是为了防止它们重来：

    1. ``get_news(lang)`` 曾经**收下 lang 却完全不用**（只渲染英文），界面上不
       报错，只是非英语页面的新闻永远不变。运行时 spy 能抓到「请求了某语种却
       一次查询都没命中该语种」。
    2. ``_news_to_dict`` 一旦漏掉 ``translations``，后台**任意一次保存**都会把
       五种语言从 seed 里抹掉 —— 而本地看不出来，因为本地还留着 DB 行。所以
       这条必须静态钉死在函数返回值里。
    3. 缺译文时必须**回退英文**而不是返回空串，否则半翻译的文章在 /ar/ 上是
       一个空白卡片，比整篇英文更难看。

    第 ① 层是常量钉死（字段集变了要显式改表），第 ②③④ 层靠运行时 spy 与
    端到端渲染，不依赖能否静态分析出来。
    """

    ALL_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    def _seed_news(self, **over):
        row = {
            'slug': 'qa-news-tr',
            'title': 'QA EN title.',
            'summary': 'QA EN summary.',
            'content': 'QA EN content.',
            'image': '',
            'images': [],
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
            'translations': {},
        }
        row.update(over)
        return row

    # ---- ① 字段集钉死 ----------------------------------------------------
    def test_translatable_field_set_is_pinned(self):
        from pages.views.data_loaders import (
            NEWS_TRANSLATABLE_FIELDS,
            NEWS_TRANSLATED_KEYS,
        )
        self.assertEqual(
            NEWS_TRANSLATABLE_FIELDS, ('title', 'summary', 'content'),
            '可译字段集被改动 —— 模板/seed/后台都要同步改，请显式确认')
        self.assertEqual(
            NEWS_TRANSLATED_KEYS, ('title_t', 'summary_t', 'content_t'))

    # ---- ② 两条路径的 key 集必须一致 -------------------------------------
    def test_seed_and_db_rows_expose_identical_key_sets(self):
        from pages.models import NewsArticle
        from pages.views.data_loaders import (
            _NEWS_ROW_BASE,
            _normalize_news_article,
            _normalize_news_row,
            NEWS_TRANSLATED_KEYS,
        )
        self.assertEqual(
            set(_NEWS_ROW_BASE) | set(NEWS_TRANSLATED_KEYS),
            set(_normalize_news_article(self._seed_news()).keys()),
            'seed 路径的 key 集变了')
        article = NewsArticle.objects.create(
            slug='qa-news-tr-db',
            title='QA EN title.',
            summary='QA EN summary.',
            content='QA EN content.',
            published_at='2026-01-01T00:00:00Z',
            is_published=True,
        )
        self.assertEqual(
            set(_normalize_news_row(article).keys()),
            set(_NEWS_ROW_BASE) | set(NEWS_TRANSLATED_KEYS),
            'DB 路径与 seed 路径的 key 集必须完全一致，否则模板在 Vercel 上会缺字段')

    # ---- ③ 缺译文回退英文（不能是空串） ----------------------------------
    @override_settings(IS_VERCEL=True)
    def test_missing_translation_falls_back_to_english(self):
        from pages.views.data_loaders import _get_news_from_json

        seed = {'news': [self._seed_news()]}
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            for lang in self.ALL_LANGS:
                rows = _get_news_from_json(lang)
                row = rows[0]
                for field in ('title', 'summary', 'content'):
                    self.assertEqual(
                        row[f'{field}_t'], f'QA EN {field}.',
                        f'{lang} 缺少译文时应回退英文，实际拿到空值')

    @override_settings(IS_VERCEL=True)
    def test_translated_seed_overrides_english(self):
        from pages.views.data_loaders import _get_news_from_json

        tr = {lang: {'title': f'TR {lang} title',
                     'summary': f'TR {lang} summary',
                     'content': f'TR {lang} content'}
              for lang in self.ALL_LANGS}
        seed = {'news': [self._seed_news(translations=tr)]}
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            for lang in self.ALL_LANGS:
                row = _get_news_from_json(lang)[0]
                for field in ('title', 'summary', 'content'):
                    self.assertEqual(
                        row[f'{field}_t'], f'TR {lang} {field}',
                        f'{lang} 的 {field} 译文未生效')

    # ---- ④ 运行时 spy：lang 真的被用上了 ---------------------------------
    def test_every_requested_lang_reaches_the_lookup(self):
        from pages.views import data_loaders
        from pages.views.data_loaders import _get_news_from_json

        seen = set()
        real = data_loaders._news_translated

        def spy(row, field, lang):
            seen.add((field, lang))
            return real(row, field, lang)

        with mock.patch.object(data_loaders, '_news_translated', spy):
            for lang in ('fr', 'de', 'ar'):
                with override_settings(IS_VERCEL=True):
                    with mock.patch(
                        'pages.views.data_loaders._load_seed',
                        return_value={'news': [self._seed_news()]},
                    ):
                        data_loaders.get_news(lang)
        for lang in ('fr', 'de', 'ar'):
            for field in ('title', 'summary', 'content'):
                self.assertIn(
                    (field, lang), seen,
                    f'{lang} 请求下 {field} 没有真正走翻译查找（get_news 大概又忽略了 lang）')

    # ---- ⑤ 渲染端到端 ----------------------------------------------------
    @override_settings(IS_VERCEL=True)
    def test_french_article_renders_french_on_the_page(self):
        """译文真的渲染出来。v1.6.3 起列表卡片只显示 title + summary（正文
        迁到详情页），所以 title/summary 在列表页断言，content 在详情页断言。
        """
        fr = {'fr': {'title': 'TR fr titre',
                     'summary': 'TR fr résumé',
                     'content': 'TR fr contenu'}}
        seed = {'news': [self._seed_news(translations=fr)]}
        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            list_resp = self.client.get('/fr/news/')
        self.assertEqual(list_resp.status_code, 200)
        list_html = list_resp.content.decode('utf-8')
        self.assertIn('TR fr titre', list_html)
        self.assertIn('TR fr résumé', list_html)
        self.assertNotIn('QA EN title.', list_html)

        with mock.patch('pages.views.data_loaders._load_seed', return_value=seed):
            detail_resp = self.client.get('/fr/news/qa-news-tr/')
        self.assertEqual(detail_resp.status_code, 200)
        detail_html = detail_resp.content.decode('utf-8')
        self.assertIn('TR fr contenu', detail_html)
        self.assertNotIn('QA EN content.', detail_html)

    # ---- ⑥ seed 导出必须带 translations ---------------------------------
    def test_news_to_dict_exports_translations(self):
        """漏掉这一行，后台任意一次保存都会把五种语言抹出 seed。"""
        from pages import seed_sync

        src = inspect.getsource(seed_sync._news_to_dict)
        self.assertIn(
            "'translations'", src,
            '_news_to_dict 不再导出 translations：后台保存会静默删除所有译文')

    def test_article_model_exposes_translations(self):
        from pages.models import NewsArticle
        field_names = {f.name for f in NewsArticle._meta.get_fields()}
        self.assertIn('translations', field_names,
                      'NewsArticle 缺少 translations 字段')
        self.assertTrue(callable(getattr(NewsArticle, 't')))

    def test_admin_wires_the_translations_widget(self):
        from django.contrib.admin.sites import AdminSite
        from pages.models import NewsArticle
        from pages.admin.news import NewsArticleAdmin
        from pages.admin.widgets import TranslationsWidget
        admin = NewsArticleAdmin(NewsArticle, AdminSite())
        field = admin.formfield_for_dbfield(
            NewsArticle._meta.get_field('translations'), None)
        self.assertIsInstance(field.widget, TranslationsWidget,
                              '后台的多语言输入框没挂上')


class NewsChipsAndCopyTests(TestCase):
    """/news/ 顶部分类 chips 与正文语言的守卫（2026-09-25 建）。

    三个 bug 都是「代码不报错、界面慢慢不对」型，所以这里既有静态断言也有
    渲染断言：

    1. ``{% trans %}`` 只接受**字面量**。模板里原来写的是 ``{% trans cat.name %}``
       （变量），Django 不报错、直接渲染空串 —— 分类名全部消失。现在的约定
       是「视图用 ``_t()`` 算好 label，模板只负责 ``{{ cat.label }}``」。
    2. 新闻正文的**英文基础字段被写成了中文**。英文站读不到译文时回退基础字段，
       于是什么语种都显示中文。约定：基础字段永远是英文，中文等译文进
       ``translations``。
    3. v1.6.3 版式改版：原左侧栏目录换成顶部 chips（企业 newsroom 惯例，
       调研结论见 .workbuddy/preview/news-redesign-mockup.html），本类从
       ``NewsSidebarAndCopyTests`` 更名而来，断言目标同步迁移。
    """

    ALL_LANGS = ('fr', 'es', 'de', 'ru', 'ar')
    CJK_RE = re.compile(r'[　-〿一-鿿！-｠]')

    def _row(self, slug, category='Company News'):
        return {
            'slug': slug,
            'title': f'QA EN title {slug}',
            'summary': f'QA EN summary {slug}',
            'content': f'QA EN content {slug}',
            'category': category,
            'image': '',
            'images': [],
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
            'translations': {},
        }

    def _render(self, lang='en', query='', seed_news=None):
        """Render the news page, optionally against a three-category seed.

        ``i18n_patterns(prefix_default_language=False)`` means English lives at
        ``/news/`` and everything else at ``/<lang>/news/`` — ``/en/news/``
        is a legitimate 404, not a typo.
        """
        path = '/news/' if lang == 'en' else f'/{lang}/news/'
        if seed_news is None:
            seed_news = [
                self._row('qa-co', 'Company News'),
                self._row('qa-pn', 'Product News'),
                self._row('qa-cs', 'Case Studies'),
            ]
        with override_settings(IS_VERCEL=True):
            with mock.patch(
                'pages.views.data_loaders._load_seed',
                return_value={'news': seed_news},
            ):
                resp = self.client.get(f'{path}{query}')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode('utf-8')

    def _chips(self, html):
        nav = re.search(r'<nav class="news-chips"[^>]*>(.*?)</nav>', html, re.S)
        self.assertIsNotNone(nav, '分类 chips 整块没渲染出来')
        # Label 是 <a> 与计数 <span> 之间的文本节点；class 可能带 ` is-active`
        # 修饰符。href 与 class 属性在模板里分行书写 —— 模式必须容忍换行。
        return re.findall(
            r'<a\s+href="([^"]*)"\s+class="news-chip([^"]*)"\s*>\s*([^<]*)<',
            nav.group(1), re.S,
        )

    # ---- ① 模板不许再用 {% trans %} 包变量 --------------------------------
    def test_template_never_runs_trans_tag_on_a_variable(self):
        src = (Path(__file__).resolve().parent.parent
               / 'templates' / 'news.html').read_text(encoding='utf-8')
        offenders = re.findall(r'{%\s*trans\s+[^{}%]+\s*%}', src)
        offenders = [o for o in offenders if not re.fullmatch(r'{%\s*trans\s+"[^"]*"\s*%}', o)]
        self.assertEqual([], offenders,
                         '{% trans %} 只接受字面量，套在变量上会渲染成空串：' + str(offenders))

    # ---- ② 分类名在每个语种都本地化 ---------------------------------------
    def test_chip_labels_are_localised_in_every_language(self):
        expected = {
            'fr': 'Nouvelles de l\'Entreprise',   # Company News
            'es': 'Noticias de la Empresa',
            'de': 'Unternehmensnachrichten',
            'ar': 'أخبار الشركة',
            'ru': 'Корпоративные новости',
        }
        html = self._render('en')
        labels = [html_unescape(entry[2].strip()) for entry in self._chips(html)]
        self.assertIn('All News', labels, '英文页丢了 All News 聚合 chip')
        self.assertIn('Company News', labels, '英文 chips 丢了分类')
        self.assertIn('Product News', labels)
        self.assertIn('Case Studies', labels)
        for lang, want in expected.items():
            html = self._render(lang)
            labels = [html_unescape(entry[2].strip()) for entry in self._chips(html)]
            self.assertIn(want, labels,
                          f'{lang} chips 没有本地化分类名（_SIDEBAR_I18N 缺条目或视图没走 _t）')
            self.assertNotIn(
                'Company News', labels,
                f'{lang} chips 仍在显示英文原文')

    # ---- ③ 分类链接真的会筛选 --------------------------------------------
    def test_category_link_filters_the_feed_and_marks_itself_active(self):
        html = self._render(query='?category=Case+Studies')
        entries = self._chips(html)
        active = [e for e in entries if 'active' in e[1]]
        self.assertEqual(['Case Studies'], [e[2].strip() for e in active],
                         '筛选后选中态没落在正确的分类 chip 上')
        self.assertEqual(1, html.count('<h3 class="news-card-title">'),
                         '?category= 没有真的过滤文章')

    def test_unknown_category_key_falls_back_to_the_full_feed(self):
        """A stale bookmark must not render as an empty news page."""
        html = self._render(query='?category=No+Such+Category')
        self.assertEqual(3, html.count('<h3 class="news-card-title">'))
        active = [e for e in self._chips(html) if 'active' in e[1]]
        self.assertEqual(['All News'], [e[2].strip() for e in active])

    # ---- ④ 正文基础字段必须是英文 ----------------------------------------
    @override_settings(IS_VERCEL=True)
    def test_english_news_copy_contains_no_chinese(self):
        """中文写进基础字段 → 英文站回退显示中文。译文请放进 translations。"""
        from pages.views.data_loaders import _load_seed
        seed = _load_seed()
        articles = seed.get('news') or []
        self.assertTrue(articles, 'seed 里一条新闻都没有，这条守卫失去意义')
        for a in articles:
            for field in ('title', 'summary', 'content'):
                value = a.get(field) or ''
                self.assertIsNone(
                    self.CJK_RE.search(value),
                    f"seed 新闻 {a.get('slug')} 的 {field} 是中文："
                    f'{value[:60]}… 请改用英文基础字段，中文放进 translations')

    def test_english_page_renders_no_chinese_in_the_card_body(self):
        html = self._render('en')
        # 卡片整体是 <a>（整卡可点），body 是其最后一个子元素。
        bodies = re.findall(r'<div class="news-card-body">(.*?)</a>', html, re.S)
        self.assertTrue(bodies, '新闻卡片正文没渲染出来')
        for body in bodies:
            self.assertIsNone(
                self.CJK_RE.search(body),
                '英文页面上出现中文正文 —— 基础字段里混进了中文')

    # ---- ⑤ 封面 + 图集一张不少（列表 1 张 + 详情 3 张） --------------------
    @override_settings(IS_VERCEL=True)
    def test_article_shows_its_cover_plus_every_gallery_photo(self):
        """Against the real seed: one cover on the list card; cover + 2 gallery
        photos on the detail page — never a lone one.

        Regression: the second gallery photo was deleted during the dead-file
        audit as "unreferenced" (it referenced the article through a join
        table, which the audit's grep could not see), leaving one image.
        v1.6.3: the list card shows only the 16:9 cover; the gallery moved to
        the detail page.
        """
        from pages.views.data_loaders import _load_seed
        articles = _load_seed().get('news') or []

        def _is_target(a):
            urls = [a.get('image') or ''] + [
                (i.get('image') or '') for i in (a.get('images') or [])]
            return any('tianjin-binhai' in u for u in urls)

        slug = next((a.get('slug') for a in articles if _is_target(a)), None)
        self.assertIsNotNone(slug, 'seed 里找不到天津新闻，守卫失去意义')

        resp = self.client.get('/news/')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertEqual(1, html.count('class="news-card-cover"'))
        # v1.8.2: the seed images were converted to WebP; the old `.jpg`
        # assertion could never match again.
        self.assertIn('tianjin-binhai-high-mast-retrofit-hero.webp', html)

        detail = self.client.get(f'/news/{slug}/')
        self.assertEqual(detail.status_code, 200)
        detail_html = detail.content.decode('utf-8')
        # v1.6.4: 详情页改为 bento 网格（左大图跨两行 + 右 2 小图上下叠），
        # 封面与 2 张图集图统一为 3 个 .news-detail-media-cell。
        self.assertIn('class="news-detail-media"', detail_html)
        self.assertEqual(
            3, detail_html.count('class="news-detail-media-cell'),
            '详情页应显示封面 + 2 张图集图，统一为 3 个 media-cell')
        for name in ('hero', 'head-work', 'ground-work'):
            self.assertIn(f'tianjin-binhai-high-mast-retrofit-{name}.webp',
                          detail_html)


class NewsDetailPageTests(TestCase):
    """新闻详情页的路由 / 发布门 / related 卡片守卫（v1.6.3 新增）。

    列表卡片改版后整卡都链到 `/news/<slug>/`，这条路由成了新闻模块的门面：
    未知 slug 与未发布草稿必须 404（否则站外坏链渲染成空页），related 只出
    别人的文章。
    """

    def _row(self, slug, title=None, category='Company News'):
        return {
            'slug': slug,
            'title': title or f'QA EN title {slug}',
            'summary': f'QA EN summary {slug}',
            'content': f'QA EN content {slug}',
            'category': category,
            'image': '',
            'images': [],
            'published_at': '2026-01-01T00:00:00',
            'is_published': True,
            'translations': {},
        }

    def _get(self, path, seed):
        with override_settings(IS_VERCEL=True):
            with mock.patch('pages.views.data_loaders._load_seed',
                            return_value={'news': seed}):
                return self.client.get(path)

    def test_unknown_or_unpublished_slug_is_a_404(self):
        seed = [self._row('qa-live'),
                dict(self._row('qa-draft'), is_published=False)]
        self.assertEqual(self._get('/news/qa-nope/', seed).status_code, 404,
                         '未知 slug 必须是 404')
        self.assertEqual(self._get('/news/qa-draft/', seed).status_code, 404,
                         '未发布草稿必须 404（is_published 门失效）')

    def test_related_cards_link_to_other_articles_with_labels(self):
        seed = [
            self._row('qa-live', category='Product News'),
            self._row('qa-other', title='QA Related TitleXYZ',
                      category='Case Studies'),
        ]
        resp = self._get('/news/qa-live/', seed)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertIn('QA Related TitleXYZ', html, 'related 卡片没渲染')
        self.assertIn('href="/news/qa-other/"', html)
        self.assertIn('Case Studies', html, 'related 卡片缺分类徽章')
        # 自己不出现在自己的 More news 里
        self.assertNotIn('href="/news/qa-live/"', html)


class NewsImageSyncTests(TestCase):
    """Guards the media/ -> static/ copy that news photos depend on.

    Regression: ``NewsArticle``/``NewsImage`` had no post_save receiver, so an
    admin upload only ever landed under ``media/``. The production seed records
    news photos as ``images/news/<slug>/...``, which resolve against ``static/``
    -- so every news photo 404'd on Vercel while looking perfect locally. The
    DB row still rendered ``/media/...``, which is exactly why the mismatch is
    invisible until you deploy.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.media = self.root / 'media'
        self.media.mkdir(exist_ok=True)
        # Everything points into the temp tree so nothing can escape.
        self.ctx = override_settings(
            BASE_DIR=str(self.root),
            MEDIA_ROOT=str(self.media),
        )
        self.ctx.enable()

    def tearDown(self):
        self.ctx.disable()
        self.tmp.cleanup()

    # ---- helpers ---------------------------------------------------------
    def _put_media(self, relpath):
        path = self.media / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'\x89PNG\r\n\x1a\nQA')
        return str(path)

    def _static_dir_for(self, slug):
        return self.root / 'static' / 'images' / 'news' / slug

    def _article(self, slug='qa-news-sync'):
        from django.utils.timezone import now
        from pages.models import NewsArticle
        return NewsArticle.objects.create(
            slug=slug, title='QA sync', content='QA sync body',
            published_at=now())

    # ---- ① 拷贝行为 -------------------------------------------------------
    def test_saving_an_article_copies_its_cover_into_static(self):
        self._put_media('news/cover_a1b2c3d.jpg')
        article = self._article()
        article.image = 'news/cover_a1b2c3d.jpg'
        article.save()

        target = self._static_dir_for('qa-news-sync') / 'cover.jpg'
        self.assertTrue(target.exists(),
                        '封面没拷进 static/：线上 seed 会指向一个不存在的路径')

    def test_saving_a_gallery_image_copies_it_into_static(self):
        from pages.models import NewsImage
        self._put_media('news/gal_a1b2c3d.jpg')
        article = self._article()
        NewsImage.objects.create(article=article,
                                 image='news/gal_a1b2c3d.jpg')

        target = self._static_dir_for('qa-news-sync') / 'gal.jpg'
        self.assertTrue(target.exists(),
                        '图集图没拷进 static/：Vercel 上会 404')

    # ---- ② 真正在线上炸的那个 bug -----------------------------------------
    def test_seed_export_path_points_at_a_real_static_file(self):
        """The end-to-end check: what the seed writes must exist on disk.

        Locally the DB path (``/media/...``) still renders, so the only way to
        catch this class of bug is to compare the *exported* path with the disk.
        """
        from pages import seed_sync

        self._put_media('news/export_a1b2c3d.jpg')
        article = self._article()
        article.image = 'news/export_a1b2c3d.jpg'
        article.save()

        row = seed_sync._news_to_dict(article)
        exported = row['image']
        self.assertTrue(exported.startswith('images/news/'),
                        f'seed 导出的封面不是 static 相对路径：{exported!r}')
        on_disk = self.root / 'static' / exported
        self.assertTrue(on_disk.exists(),
                        f'seed 导出的封面在磁盘上不存在 → 线上 404：{exported}')

    # ---- ③ 剪枝安全网 -----------------------------------------------------
    def test_prune_keeps_files_that_media_still_backs(self):
        """A static photo the sync could not re-derive must survive the prune.

        If the DB-stored media path no longer matches the file on disk, the
        sync silently skips the copy. Pruning it anyway would turn a recoverable
        image into a permanent 404 -- exactly the failure mode this guard exists
        to prevent.
        """
        from pages.models import _sync_news_media_to_static

        self._put_media('news/orphan_a1b2c3d.jpg')
        article = self._article()
        static_dir = self._static_dir_for('qa-news-sync')
        static_dir.mkdir(parents=True, exist_ok=True)
        (static_dir / 'orphan.jpg').write_bytes(b'\x89PNG\r\n\x1a\nQA')

        _sync_news_media_to_static(article)
        self.assertTrue((static_dir / 'orphan.jpg').exists(),
                        '剪枝把 media/ 里仍在用的图删掉了')

    def test_prune_removes_files_referenced_by_nothing(self):
        from pages.models import _sync_news_media_to_static

        article = self._article()
        static_dir = self._static_dir_for('qa-news-sync')
        static_dir.mkdir(parents=True, exist_ok=True)
        (static_dir / 'unreferenced.jpg').write_bytes(b'\x89PNG\r\n\x1a\nQA')

        _sync_news_media_to_static(article)
        self.assertFalse((static_dir / 'unreferenced.jpg').exists(),
                         '无人引用的图没被清掉，static 目录会无限膨胀')

    def test_build_media_protected_set_scans_the_news_subdir(self):
        """The ``subdir`` argument must be honoured, or news photos are not
        protected the way product photos are."""
        from pages.models import _build_media_protected_set

        self._put_media('news/kept_a1b2c3d.jpg')
        self.assertEqual({'kept.jpg'},
                         _build_media_protected_set(str(self.media), 'news'))
        # Defaulting back to products must not accidentally protect news files.
        self.assertEqual(set(), _build_media_protected_set(str(self.media)))

    # ---- ④ receiver 接线 --------------------------------------------------
    def test_deleting_a_gallery_image_triggers_the_static_sync(self):
        from pages.models import NewsImage

        # ``doomed.jpg`` deliberately survives: media/ still backs that file, so
        # the prune safety net keeps it. What this test proves is that the
        # delete *re-ran* the sync -- evidenced by the orphan below, which
        # nothing else would have removed.
        self._put_media('news/doomed_a1b2c3d.jpg')
        orphan = self._static_dir_for('qa-news-sync') / 'stale.jpg'
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_bytes(b'\x89PNG\r\n\x1a\nQA')

        article = self._article()
        image = NewsImage.objects.create(article=article,
                                         image='news/doomed_a1b2c3d.jpg')

        image.delete()
        self.assertFalse(orphan.exists(),
                         '删除图集图没有触发 static 同步 → 孤儿文件会留在函数包里')




class RtlBidiIsolationTests(TestCase):
    """v1.8.2 — RTL 双向文本隔离守卫。

    阿语站 (/ar/) 此前**零** bidi 隔离：卡片里的拉丁型号 (VSP-4200W-9M-YP)、
    地名 ("Beijing, China") 与数值 ("2200 lux, U0 0.8") 会被周围 RTL 段落
    方向重排。修复是把这些动态文本包进 <bdi>（规范默认 unicode-bidi:
    isolate），并在 base.css 显式声明 `[dir="rtl"] bdi`，防止被作者样式覆盖。

    本类只锁「已修复的渲染点」，不追求全站覆盖 —— 规格表数值等仍待专项。
    """

    def _template(self, name):
        from django.conf import settings
        return (settings.BASE_DIR / 'templates' / name).read_text(
            encoding='utf-8')

    # NOTE: assertions are made against the template source, not rendered HTML.
    # The test DB carries no Product/Project rows, so /ar/products/ renders an
    # empty grid — a rendered-HTML assertion would pass vacuously. Source-level
    # checks still fail if someone removes the <bdi> wrapper.
    def test_card_titles_are_wrapped_in_bdi(self):
        cases = [
            ('products.html', '<h3 class="product-card-title"><bdi>'),
            ('projects.html', '<h3 class="project-card-title"><bdi>'),
            ('news.html', '<h3 class="news-card-title"><bdi>'),
        ]
        for name, needle in cases:
            self.assertIn(needle, self._template(name),
                          f'{name}: 卡片标题未包 <bdi>，RTL 下拉丁型号会被重排')

    def test_project_location_and_results_are_isolated(self):
        src = self._template('projects.html')
        self.assertIn('<div class="project-card-location"><bdi>', src)
        self.assertIn('<bdi>{{ project.results_t }}</bdi>', src)

    def test_detail_headings_are_isolated(self):
        for name in ('news_detail.html', 'product_detail.html',
                     'product_overview.html'):
            src = self._template(name)
            self.assertIn('<bdi>', src, name)
        self.assertIn('<h1 class="news-detail-title"><bdi>',
                      self._template('news_detail.html'))
        self.assertIn('<h3><bdi>{{ a.title_t|default:a.title }}</bdi></h3>',
                      self._template('news_detail.html'))

    def test_model_number_is_isolated(self):
        self.assertIn('<bdi>{{ product.model_number }}</bdi>',
                      self._template('product_detail.html'))

    def test_arabic_pages_still_render(self):
        # Guard against the bdi markup breaking the RTL pages outright.
        for path in ('/ar/', '/ar/products/', '/ar/projects/', '/ar/news/',
                     '/ar/contact/'):
            resp = self.client.get(path, HTTP_HOST='localhost')
            self.assertEqual(resp.status_code, 200, path)

    def test_css_declares_bidi_isolate_for_rtl(self):
        from django.conf import settings
        css = (settings.BASE_DIR / 'static' / 'css' / 'base.css').read_text(
            encoding='utf-8')
        self.assertIn('[dir="rtl"] bdi', css)
        self.assertIn('unicode-bidi: isolate', css)

class JsonLdValidityTests(TestCase):
    """Guard tests for the structured-data (JSON-LD) P0 fixes.

    This class is the anti-regression net for the audit's P0 items:

    * ``test_every_page_has_parsable_jsonld`` / ``test_organization_block_is_valid``
      — P0-1: ``base.html`` built ``Organization.sameAs`` by concatenating
      ``{% if %}``-guarded strings in the template, so an empty *last* field
      (seed ships ``social_linkedin=""``) left a trailing comma and made the
      block invalid JSON on 8/8 pages. The list is now built in Python
      (``SiteConfig.social_same_as``) and joined in the template.
    * ``test_organization_logo_is_absolute`` — P0-2: ``logo`` was the relative
      ``/static/images/logo.webp``; consumers reject relative logo URLs.
    * ``test_organization_same_as_entries_are_absolute`` — P0-1 follow-up: no
      empty strings may slip back into ``sameAs``.
    * ``test_home_website_block_has_no_search_action`` — P0-4: ``home.html``
      advertised a ``SearchAction`` pointing at ``/en/products/?q=...``, but the
      English site has no ``/en/`` prefix and no search route/view exists. The
      block was deleted; this locks the contract so nobody re-adds it without
      also building the page.
    * ``test_product_url_uses_canonical_origin`` — P0-5: Product blocks used
      ``request.build_absolute_uri``, which emits ``http://localhost/...``
      locally and ``*.vercel.app`` on preview deploys.

    Every request passes ``HTTP_HOST='localhost'`` because DEBUG=False +
    ALLOWED_HOSTS would otherwise answer 400.
    """

    #: Paths exercised. Includes an Arabic page (RTL + translated config) and
    #: both product layouts (``detail`` for fl6m, ``overview`` for m-series).
    PAGE_PATHS = (
        '/',
        '/products/',
        '/projects/',
        '/news/',
        '/about/',
        '/contact/',
        '/products/fl6m/',
        '/products/m-series/',
        '/ar/',
        '/ar/products/',
    )

    JSONLD_RE = re.compile(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )

    @classmethod
    def setUpTestData(cls):
        """Seed one Product and one Project so list-page ItemList is non-empty."""
        from pages.models import Product, Project
        Product.objects.create(
            name='Guard Product',
            category='AREA_SITE',
            slug='guard-product',
            description='A product used only to validate list-page JSON-LD.',
        )
        Project.objects.create(
            title='Guard Project',
            location='Beijing, China',
            slug='guard-project',
            description='A project used only to validate list-page JSON-LD.',
        )

    def _blocks(self, path):
        """Return every JSON-LD block on ``path`` as (raw_text, parsed_obj)."""
        resp = self.client.get(path, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, f'{path} did not render')
        html = resp.content.decode('utf-8')
        return [m.group(1) for m in self.JSONLD_RE.finditer(html)]

    def _types(self, obj):
        """Return the set of @type values of a parsed block (or a nested graph)."""
        if '@graph' in obj:
            return {node.get('@type') for node in obj.get('@graph', [])}
        return {obj.get('@type')} if obj.get('@type') else set()

    def _blocks_of_type(self, path, want_type):
        """Return every parsed JSON-LD block on ``path`` whose @type is ``want_type``."""
        out = []
        for raw in self._blocks(path):
            obj = json.loads(raw)
            if want_type in self._types(obj):
                out.append(obj)
        return out

    def test_every_page_has_parsable_jsonld(self):
        """P0-1 guard: >=1 block per page and every block is valid JSON."""
        for path in self.PAGE_PATHS:
            blocks = self._blocks(path)
            self.assertTrue(blocks, f'{path} emitted no JSON-LD block at all')
            for raw in blocks:
                try:
                    json.loads(raw)
                except ValueError as exc:
                    snippet = raw.strip()[:400]
                    self.fail(
                        f'{path}: invalid JSON-LD ({exc}). Offending block://n'
                        f'{snippet}'
                    )

    def test_organization_block_is_valid(self):
        """P0-1/P0-3: the Organization block parses and carries the entity fields."""
        for path in self.PAGE_PATHS:
            orgs = self._blocks_of_type(path, 'Organization')
            self.assertEqual(len(orgs), 1,
                             f'{path}: expected exactly 1 Organization block')
            org = orgs[0]
            self.assertEqual(org.get('@context'), 'https://schema.org')
            self.assertTrue(org.get('name'), f'{path}: Organization.name empty')
            # P0-3: entity enrichment (foundingDate / address / areaServed / knowsAbout).
            self.assertEqual(org.get('foundingDate'), '2007', path)
            address = org.get('address') or {}
            self.assertEqual(address.get('@type'), 'PostalAddress', path)
            self.assertEqual(address.get('addressLocality'), 'Beijing', path)
            self.assertEqual(address.get('addressCountry'), 'China', path)
            self.assertIn('areaServed', org, path)
            self.assertTrue(org.get('knowsAbout'), f'{path}: knowsAbout empty')

    def test_organization_logo_is_absolute(self):
        """P0-2: Organization.logo must be an absolute URL, not a static path."""
        for path in self.PAGE_PATHS:
            for org in self._blocks_of_type(path, 'Organization'):
                logo = org.get('logo', '')
                self.assertTrue(
                    logo.startswith('http'),
                    f'{path}: Organization.logo is not absolute: {logo!r}',
                )

    def test_organization_same_as_entries_are_absolute(self):
        """P0-1: no empty string may re-enter ``sameAs`` via a template comma."""
        for path in self.PAGE_PATHS:
            for org in self._blocks_of_type(path, 'Organization'):
                # v1.8.2 (QA): the original guard did ``if same_as is None:
                # continue``, so *deleting* the ``sameAs`` key entirely still
                # passed — mutation-verified (removing the line from base.html
                # kept all 8 tests green). Require the key to be present; an
                # empty list is still legitimate (no social profiles configured)
                # and remains valid JSON as ``[]``.
                self.assertIn('sameAs', org,
                              f'{path}: Organization.sameAs key missing')
                same_as = org['sameAs']
                self.assertIsInstance(same_as, list, path)
                for url in same_as:
                    self.assertTrue(url, f'{path}: empty entry in sameAs')
                    self.assertTrue(
                        url.startswith('http'),
                        f'{path}: non-absolute sameAs entry: {url!r}',
                    )

    def test_home_website_block_has_no_search_action(self):
        """P0-4: WebSite must not advertise a SearchAction we cannot serve."""
        sites = self._blocks_of_type('/', 'WebSite')
        self.assertEqual(len(sites), 1, 'expected exactly 1 WebSite block on /')
        site = sites[0]
        self.assertNotIn('potentialAction', site)
        self.assertNotIn('SearchAction', json.dumps(site))
        # The block itself must survive: @type / name / url stay.
        self.assertTrue(site.get('name'))
        self.assertTrue(site.get('url'))

    def test_product_url_uses_canonical_origin(self):
        """P0-5: Product.url must use CANONICAL_ORIGIN, never the request host."""
        origin = settings.CANONICAL_ORIGIN
        for path in ('/products/fl6m/', '/products/m-series/'):
            products = self._blocks_of_type(path, 'Product')
            self.assertEqual(len(products), 1,
                             f'{path}: expected exactly 1 Product block')
            url = products[0].get('url', '')
            self.assertTrue(
                url.startswith(origin),
                f'{path}: Product.url not rooted at CANONICAL_ORIGIN: {url!r}',
            )
            self.assertNotIn('localhost', url, path)

    def test_news_article_url_uses_canonical_origin(self):
        """P0-5 (same class of bug): NewsArticle.url must be canonical too.

        Checked at the template level on purpose: locally ``get_news_detail``
        reads the DB and the test database carries no news rows, so
        ``/news/<slug>/`` 404s in tests. Pinning the template keeps the guard
        honest without seeding a fixture.
        """
        src = (settings.BASE_DIR / 'templates' / 'news_detail.html').read_text(
            encoding='utf-8')
        block = src.split('"@type": "NewsArticle"', 1)[1].split('</script>', 1)[0]
        self.assertIn('"url": "{{ canonical_origin }}{% url \'news_detail\' article.slug %}"',
                      block)
        self.assertNotIn('build_absolute_uri', block)

    def test_arabic_pages_have_parsable_organization_block(self):
        """RTL pages run the config through _t(); the JSON must still parse."""
        for path in ('/ar/', '/ar/products/', '/ar/about/', '/ar/contact/'):
            orgs = self._blocks_of_type(path, 'Organization')
            self.assertEqual(len(orgs), 1, f'{path}: Organization block missing')
            self.assertTrue(orgs[0]['logo'].startswith('http'), path)

    def test_additional_property_field_set_is_stable(self):
        """Follow-up QA finding: `additionalProperty` is now built in Python.

        The array used to be assembled in the template with a trailing comma on
        every intermediate entry, surviving only because the final `Category`
        entry was unconditional. The expected sets below are pinned so a future
        change to ``pages.utils.JSONLD_PROPERTY_FIELDS`` cannot silently drop
        or reorder advertised properties.
        """
        expected = {
            '/products/fl6m/': [
                ('Power', '480W'), ('Efficacy', '130lm/W'), ('Output', '60K+ lm'),
                ('Beam Angle', '18~50°'), ('Category', 'AREA_SITE'),
            ],
            '/products/m-series/': [
                ('Power', '80~1280W+'), ('Efficacy', '130lm/W'),
                ('Category', 'AREA_SITE'),
            ],
        }
        for path, want in expected.items():
            products = self._blocks_of_type(path, 'Product')
            self.assertEqual(len(products), 1, path)
            actual = [
                (p['name'], p['value'])
                for p in products[0].get('additionalProperty', [])
            ]
            self.assertEqual(actual, want, path)

    def test_list_pages_use_itemlist_with_webpage_items(self):
        """ItemList on /products/ and /projects/ must use ListItem -> WebPage.

        Previously the list pages embedded ``Product``/``Article`` items directly,
        which triggered Google rich-result warnings because list cards lack the
        required offers/review/image/publisher fields. Using ``WebPage`` keeps the
        structured data valid while still exposing name/url/description.
        """
        for path in ('/products/', '/projects/'):
            item_lists = self._blocks_of_type(path, 'ItemList')
            self.assertEqual(len(item_lists), 1,
                             f'{path}: expected exactly 1 ItemList block')
            item_list = item_lists[0]
            elements = item_list.get('itemListElement', [])
            self.assertTrue(elements, f'{path}: ItemList has no items')
            for element in elements:
                self.assertEqual(element.get('@type'), 'ListItem', path)
                item = element.get('item') or {}
                self.assertEqual(item.get('@type'), 'WebPage', path)
                self.assertTrue(item.get('name'), f'{path}: WebPage.name empty')
                self.assertTrue(item.get('url'), f'{path}: WebPage.url empty')
                self.assertIn('description', item, f'{path}: WebPage.description missing')

    def test_list_pages_do_not_advertise_product_or_article_summary(self):
        """/products/ must not emit Product blocks; /projects/ must not emit Article.

        These types belong on the detail pages where the full entity fields are
        available; listing cards lack the required fields and would be flagged as
        invalid rich results.
        """
        for path, forbidden in (('/products/', 'Product'), ('/projects/', 'Article')):
            for raw in self._blocks(path):
                obj = json.loads(raw)
                types = self._types(obj)
                if 'ItemList' in types:
                    # The ItemList itself is fine; inspect its children.
                    for element in obj.get('itemListElement', []):
                        item = element.get('item') or {}
                        self.assertNotEqual(item.get('@type'), forbidden,
                                            f'{path}: list item uses {forbidden}')

    def test_product_block_does_not_fabricate_offers_or_ratings(self):
        """GSC「产品摘要：缺少 offers/review/aggregateRating」是**已知且接受**的状态。

        Product 详情页的 JSON-LD 没有 ``offers``/``review``/``aggregateRating``
        （B2B 询盘制没有公开价格，也没有评价系统），因此永远拿不到「产品摘要」
        富媒体片段资格 —— GSC 会常驻一条「严重问题」告警。这是业务模式决定的，
        **不是 bug**：收录/排名完全不受影响（GSC 实测 2026-09-30：「网址可编入
        Google 索引，但存在一些问题」），告警只表示"无增强资格"。

        保留 Product 标记是决策（brand/sku/mpn/additionalProperty 喂知识图谱与
        AI 搜索实体识别，GEO 资产）。本用例锁住「宁缺毋假」：任何人不得为了消
        告警而伪造 offers 价格或 aggregateRating 评分 —— 那是虚假信息 + 富媒体
        作弊风险。真要消告警，正确做法是整块删除 Product 标记。
        """
        for path in ('/products/fl6m/', '/products/m-series/'):
            products = self._blocks_of_type(path, 'Product')
            self.assertEqual(len(products), 1, path)
            p = products[0]
            self.assertNotIn('offers', p, f'{path}: fabricated offers')
            self.assertNotIn('aggregateRating', p, f'{path}: fabricated aggregateRating')
            self.assertNotIn('review', p, f'{path}: fabricated review')

    # NOTE (QA round 2): every entry is ``(template, needle, expected_count)``.
    # Counting — not just ``assertIn`` — is what makes this guard real:
    # ``products.html`` and ``projects.html`` used to render their ItemList array
    # with a duplicated ``{% if not forloop.last %} / {% else %}`` pair, so the
    # needle legitimately appeared TWICE. The list pages now use a single
    # ListItem -> WebPage template branch with a trailing comma conditional, so
    # every interpolated string appears exactly once. A plain ``assertIn`` was
    # mutation-verified to pass even after deleting ``|escapejs`` from one
    # branch, because the surviving branch still satisfied the containment check.
    ESCAPEJS_CHECKS = (
        ('base.html', '"name": "{{ config.brand_name|escapejs }}"', 1),
        ('base.html', '"description": "{{ config.meta_description|escapejs }}"', 1),
        ('base.html', '"streetAddress": "{{ config.address_street|escapejs }}"', 1),
        ('base.html', '"addressLocality": "{{ config.address_locality|escapejs }}"', 1),
        ('base.html', '"addressCountry": "{{ config.address_country|escapejs }}"', 1),
        ('base.html', '"{{ topic|escapejs }}"', 1),
        ('base.html', '"email": "{{ config.contact_email|escapejs }}"', 1),
        ('base.html', '"phone": "{{ config.contact_phone_1|escapejs }}"', 1),
        ('home.html', '"name": "{{ config.brand_name|escapejs }}"', 1),
        ('products.html', '"name": "{{ config.products_title|escapejs }}"', 1),
        ('products.html', '"name": "{{ product.name_t|escapejs }}"', 1),
        ('products.html', '"description": "{{ product.description_t|escapejs }}"', 1),
        ('projects.html', '"name": "{{ config.projects_title|escapejs }}"', 1),
        ('projects.html', '"name": "{{ project.title_t|escapejs }}"', 1),
        ('projects.html', '"description": "{{ project.description_t|escapejs }}"', 1),
        ('news_detail.html',
         '"headline": "{{ article.title_t|default:article.title|escapejs }}"', 1),
        ('news_detail.html',
         '"description": "{{ article.summary_t|default:article.summary|escapejs }}"', 1),
        # Breadcrumb trails are array members too: the include passes an
        # escaped leaf name so " translated titles cannot break BreadcrumbList.
        ('news_detail.html', 'leaf_name=article.title_t|escapejs', 1),
        ('product_detail.html', 'leaf_name=product.name_t|escapejs', 1),
        ('product_overview.html', 'leaf_name=product.name_t|escapejs', 1),
        ('project_detail.html', 'leaf_name=project.title_t|escapejs', 1),
        ('product_detail.html', '"name": "{{ product.name_t|escapejs }}"', 1),
        ('product_detail.html',
         '"description": "{{ product.description_t|default:\'\'|escapejs }}"', 1),
        ('product_detail.html',
         '"sku": "{{ product.model_number|default:product.slug|escapejs }}"', 1),
        ('product_detail.html',
         '"mpn": "{{ product.model_number|default:product.slug|escapejs }}"', 1),
        ('product_detail.html', '"value": "{{ value|escapejs }}"', 1),
        ('product_overview.html', '"name": "{{ product.name_t|escapejs }}"', 1),
        ('product_overview.html',
         '"description": "{{ product.description_t|default:\'\'|escapejs }}"', 1),
        ('product_overview.html',
         '"sku": "{{ product.model_number|default:product.slug|escapejs }}"', 1),
        ('product_overview.html',
         '"mpn": "{{ product.model_number|default:product.slug|escapejs }}"', 1),
        ('product_overview.html', '"value": "{{ value|escapejs }}"', 1),
        ('project_detail.html', '"headline": "{{ project.title_t|escapejs }}"', 1),
        ('project_detail.html',
         '"description": "{{ project.description_t|default:\'\'|escapejs }}"', 1),
        ('project_detail.html', '"name": "{{ config.brand_name|escapejs }}"', 1),
        ('project_detail.html', '"name": "{{ project.location_t|escapejs }}"', 1),
    )

    def test_jsonld_strings_are_js_escaped(self):
        """Follow-up QA finding: every interpolated JSON-LD string needs escapejs.

        An unescaped admin-editable value containing a backslash broke the whole
        block (`Invalid \\escape`); a double quote survived HTML autoescaping as
        `&quot;` and silently corrupted the value Google reads. Round 1 pinned 7
        spots; round 2 pins every remaining one (32 checks) and switches to
        counted assertions so a duplicated template branch cannot mask a removal.
        URLs/paths stay deliberately unescaped — see the class docstring.
        """
        for name, needle, want in self.ESCAPEJS_CHECKS:
            src = (settings.BASE_DIR / 'templates' / name).read_text(
                encoding='utf-8')
            self.assertEqual(
                src.count(needle), want,
                f'{name}: expected {want} x {needle!r}, found '
                f'{src.count(needle)}')

        # The template-built-array pattern must not come back.
        for name in ('product_detail.html', 'product_overview.html'):
            src = (settings.BASE_DIR / 'templates' / name).read_text(
                encoding='utf-8')
            self.assertNotIn('{% if product.efficacy %}{"@type": "PropertyValue"',
                             src)
            self.assertEqual(
                src.count('{% for label, value in product.jsonld_properties %}'),
                1, f'{name}: additionalProperty loop missing or duplicated')


class ProductFaqSchemaTests(TestCase):
    """B3 guard (SEO/GEO 2026-09): product pages emit a valid FAQPage JSON-LD
    with exactly the 6 confirmed Q&A, and a visible (no-JS) FAQ section.

    Mirrors the JSON-LD acquisition pattern from JsonLdValidityTests but
    asserts the FAQPage-specific contract. ``HTTP_HOST='localhost'`` is passed
    because DEBUG=False + ALLOWED_HOSTS would otherwise answer 400.
    """

    PATHS = ('/products/fl6m/', '/products/m-series/')

    JSONLD_RE = re.compile(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )

    def _blocks(self, path):
        resp = self.client.get(path, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, f'{path} did not render')
        html = resp.content.decode('utf-8')
        return [m.group(1) for m in self.JSONLD_RE.finditer(html)], html

    def test_faqpage_block_present_parseable_and_has_six_entries(self):
        for path in self.PATHS:
            blocks, _ = self._blocks(path)
            faq_blocks = []
            for raw in blocks:
                # Must be valid JSON (this is what locks the json.dumps contract).
                obj = json.loads(raw)
                types = set()
                if '@graph' in obj:
                    types |= {n.get('@type') for n in obj.get('@graph', [])}
                else:
                    types.add(obj.get('@type'))
                if 'FAQPage' in types:
                    faq_blocks.append(obj)
            self.assertEqual(len(faq_blocks), 1,
                             f'{path}: expected exactly 1 FAQPage block')
            main = faq_blocks[0].get('mainEntity', [])
            self.assertEqual(len(main), 6,
                             f'{path}: expected 6 FAQ entries, got {len(main)}')
            for item in main:
                self.assertEqual(item.get('@type'), 'Question', path)
                self.assertTrue(item.get('name'), f'{path}: empty question name')
                ans = item.get('acceptedAnswer', {})
                self.assertEqual(ans.get('@type'), 'Answer', path)
                self.assertTrue(ans.get('text'), f'{path}: empty answer text')

    def test_faq_visible_section_renders_with_six_details(self):
        """The FAQ must be user-visible without JavaScript (GEO/SEO value)."""
        for path in self.PATHS:
            _, html = self._blocks(path)
            self.assertIn('class="detail-faq"', html,
                          f'{path}: visible FAQ section missing')
            self.assertIn('class="detail-faq-list"', html,
                          f'{path}: FAQ list wrapper missing')
            # Six <details> items — one per question.
            self.assertEqual(
                html.count('<details'), 6,
                f'{path}: expected 6 <details> FAQ items, got '
                f'{html.count("<details")}')
            # The first question reads as visible text (Django-autoescaped).
            self.assertIn(
                'Are SolarOne stadium lights flicker-free for broadcast?', html,
                f'{path}: first FAQ question not visible')


class NewsFeedTests(TestCase):
    """B4 guard (SEO/GEO 2026-09): /news/feed.xml serves a valid RSS 2.0 feed.

    AI crawlers and human aggregators hit this endpoint; it must return 200,
    advertise ``application/rss+xml``, parse as XML, and list exactly the
    published seed news entries (currently 1).
    """

    def _seed_published_news_count(self):
        import json as _json
        seed = _json.loads(
            (settings.BASE_DIR / 'seed_data.json').read_text(encoding='utf-8'))
        return len([
            n for n in seed.get('news', []) if n.get('is_published', True)
        ])

    def test_feed_renders_valid_rss(self):
        import xml.etree.ElementTree as ET

        resp = self.client.get('/news/feed.xml', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, 'feed.xml did not render')
        self.assertIn('rss+xml', resp['Content-Type'])

        content = resp.content.decode('utf-8')
        # Valid XML (this is what locks the Python-built-XML contract).
        root = ET.fromstring(content)
        self.assertEqual(root.tag, 'rss')
        channel = root.find('channel')
        self.assertIsNotNone(channel, 'RSS missing <channel>')
        self.assertIsNotNone(channel.find('title').text, 'feed title empty')
        self.assertIsNotNone(channel.find('link').text, 'feed link empty')

        items = channel.findall('item')
        expected = self._seed_published_news_count()
        self.assertEqual(len(items), expected,
                         f'feed item count {len(items)} != published news {expected}')
        for it in items:
            self.assertIsNotNone(it.find('title').text, 'item title empty')
            self.assertIsNotNone(it.find('link').text, 'item link empty')
            self.assertIsNotNone(
                it.find('description').text, 'item description empty')
            # pubDate must be present and RFC-822 shaped.
            pub = it.find('pubDate').text or ''
            self.assertRegex(pub, r'^\w{3}, \d{2} \w{3} \d{4} ',
                             f'non-RFC822 pubDate: {pub!r}')

    def test_feed_item_links_are_canonical(self):
        import xml.etree.ElementTree as ET

        resp = self.client.get('/news/feed.xml', HTTP_HOST='localhost')
        root = ET.fromstring(resp.content.decode('utf-8'))
        origin = settings.CANONICAL_ORIGIN
        for it in root.find('channel').findall('item'):
            link = it.find('link').text or ''
            self.assertTrue(
                link.startswith(f'{origin}/news/'),
                f'feed item link not rooted at CANONICAL_ORIGIN: {link!r}')
            self.assertNotIn('localhost', link)
