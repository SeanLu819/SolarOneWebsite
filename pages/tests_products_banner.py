"""Guard: SEO batch B4 — the light-theme products banner is deferred, not eagerly
fetched. Every dark-theme visitor (the default/server theme) must NOT download the
~90 KB light banner; it is promoted to src= only by the html.js-gated script when
the visitor is actually on the light theme.
"""
import re

from django.test import TestCase


class ProductsBannerLazyLoadTests(TestCase):
    def test_light_banner_has_no_eager_src(self):
        resp = self.client.get('/products/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # locate the light banner <img> tag
        m = re.search(
            r'<img[^>]*class="[^"]*products-banner-light[^"]*"[^>]*>', content)
        self.assertIsNotNone(m, 'light banner <img> must be present')
        tag = m.group(0)
        self.assertIn('data-src=', tag,
                      'light banner must defer its URL in data-src')
        # the eager src= attribute must NOT be on the light banner. Note
        # data-src= contains the substring "src=", so we test for a spaced src.
        self.assertNotRegex(tag, r'\ssrc=',
                           'light banner must not be eagerly fetched (no src=)')
        # dark banner (default theme) is still eager
        dark = re.search(
            r'<img[^>]*class="[^"]*products-banner-dark[^"]*"[^>]*>', content)
        self.assertIsNotNone(dark)
        self.assertRegex(dark.group(0), r'\ssrc=')
