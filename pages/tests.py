import ast
import gettext
import json
import re
import sys
import tempfile
import types
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
        rendered = [
            t.strip() for t in re.findall(
                r'<h3[^>]*class="[^"]*product-card-title[^"]*"[^>]*>\s*([^<]+?)\s*</h3>',
                resp.content.decode('utf-8'))
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
    """

    ALL_LANGS = ('fr', 'es', 'de', 'ru', 'ar')

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



