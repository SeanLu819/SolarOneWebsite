"""
B0 / D3 + L1 — conversion-event & analytics guard tests.

These verify the analytics foundation without a real GA4 property:
- the 4 conversion events (generate_lead / contact_click / pdf_download / quote_view)
  are wired and degrade safely when GA4 is not configured;
- GA4 / GSC tags render only when their env vars are set (no third-party request
  otherwise).

Run:  E:/Python/python3/python.exe manage.py test pages.tests_analytics
"""
import os
from importlib import import_module

from django.test import TestCase, override_settings, Client
from django.urls import reverse

BASE_HOST = 'localhost'


def _get(path):
    return Client().get(path, HTTP_HOST=BASE_HOST).content.decode('utf-8')


class ConversionEventTests(TestCase):
    """D3 / H3: the four conversion events are wired and safe to degrade."""

    def test_home_renders_event_handlers_and_safe_guard(self):
        html = _get('/')
        # Global click handler covers contact_click + pdf_download ...
        self.assertIn('contact_click', html)
        self.assertIn('pdf_download', html)
        # ... and the product-page exposure hook is referenced.
        self.assertIn('quote_view', html)
        # Critical: every gtag call is guarded so it never throws when GA4 is off.
        self.assertIn("typeof window.gtag === 'function'", html)
        self.assertIn('function gaTrack', html)

    def test_product_detail_has_quote_view_hook(self):
        html = _get(reverse('product_detail', args=['m-series']))
        self.assertIn('data-ga-event="quote_view"', html)

    def test_generate_lead_absent_on_get(self):
        # A plain GET of the contact page must NOT contain the lead event.
        html = _get(reverse('contact'))
        self.assertNotIn('generate_lead', html)

    def test_generate_lead_fires_on_contact_success(self):
        # B0 contract: a genuine successful POST renders the generate_lead script.
        from django.core.cache import cache
        cache.clear()  # reset the per-IP rate limiter for a deterministic POST
        resp = Client().post(
            reverse('contact'),
            {
                'name': 'Test Buyer',
                'email': 'buyer@example.com',
                'message': 'Please send a quote for stadium lighting.',
                # honeypot left empty on purpose
            },
            HTTP_HOST=BASE_HOST,
        )
        html = resp.content.decode('utf-8')
        self.assertIn('generate_lead', html)
        # The event must still be guarded (no GA4 in test settings).
        self.assertIn("typeof window.gtag === 'function'", html)

    def test_ga4_absent_when_not_configured(self):
        html = _get('/')
        self.assertNotIn('googletagmanager.com/gtag/js', html)
        self.assertNotIn('google-site-verification', html)


class AnalyticsTagRenderingTests(TestCase):
    """GA4 / GSC tags render only when their env vars are set (no third-party
    request otherwise — the safe-by-default behavior of the head block)."""

    @override_settings(
        GA4_MEASUREMENT_ID='G-TEST123456',
        GSC_VERIFICATION_CODE='test-gsc-verification-code',
    )
    def test_ga4_and_gsc_present_when_configured(self):
        html = _get('/')
        self.assertIn('gtag/js?id=G-TEST123456', html)
        self.assertIn('google-site-verification', html)
        self.assertIn('test-gsc-verification-code', html)

    @override_settings(GA4_MEASUREMENT_ID='G-TEST123456', GSC_VERIFICATION_CODE='')
    def test_gsc_meta_absent_without_code(self):
        html = _get('/')
        self.assertIn('gtag/js?id=G-TEST123456', html)
        self.assertNotIn('google-site-verification', html)
