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