"""Guards for IndexNow (A3 / v1.10.16) — Bing / Yandex push protocol.

IndexNow validates ``https://<host>/<key>.txt`` before it accepts any push. If
that file 404s, returns HTML, or its body differs from the key, every push is
silently rejected — so these guards assert the **served value**, not just that
a route exists.
"""
import re

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

HEX_KEY_RE = re.compile(r'^[a-f0-9]{8,128}$')


class IndexNowKeyTests(TestCase):

    def test_key_is_a_valid_hex_token(self):
        key = getattr(settings, 'INDEXNOW_KEY', '')
        self.assertTrue(key, 'INDEXNOW_KEY must be configured')
        self.assertRegex(key, HEX_KEY_RE,
                         'IndexNow key must be 8-128 hex chars (a-f 0-9)')

    def test_key_file_route_matches_the_key(self):
        """The URL filename and settings.INDEXNOW_KEY_FILE must agree."""
        self.assertEqual(settings.INDEXNOW_KEY_FILE,
                         '%s.txt' % settings.INDEXNOW_KEY)
        self.assertEqual(reverse('indexnow_key'),
                         '/' + settings.INDEXNOW_KEY_FILE)

    def test_key_file_serves_the_key_as_plain_text(self):
        resp = self.client.get(reverse('indexnow_key'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/plain', resp['Content-Type'])
        self.assertEqual(resp.content.decode('utf-8').strip(),
                         settings.INDEXNOW_KEY)

    def test_empty_key_raises_404_instead_of_serving_a_blank_file(self):
        """An empty key file would look valid but fail IndexNow validation."""
        with override_settings(INDEXNOW_KEY=''):
            resp = self.client.get('/' + settings.INDEXNOW_KEY_FILE,
                                   HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 404)

    def test_key_route_does_not_shadow_existing_pages(self):
        """Regression: the 32-hex filename must not be caught by a slug route."""
        for name in ('home', 'products', 'projects', 'news', 'contact'):
            resp = self.client.get(reverse(name), HTTP_HOST='localhost')
            self.assertEqual(resp.status_code, 200,
                             '%s broke after adding the IndexNow route' % name)
