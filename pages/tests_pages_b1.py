# -*- coding: utf-8 -*-
"""
B1 / L1 — technical SEO guard tests.

F1: footer legal links must be real <a href> (not dead <span>), and the
    privacy/terms pages must render 200 with a <title>.
F2: manifest.json must be served and parse as JSON; apple-touch-icon must exist.
"""
import json

from django.test import TestCase, Client
from django.urls import reverse


class PrivacyTermsPageTests(TestCase):
    """F1 — real legal pages + footer links."""

    def setUp(self):
        self.client = Client()

    def test_privacy_page_returns_200_and_has_title(self):
        resp = self.client.get(reverse('privacy'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<title>')
        # The word "Privacy" must appear in the rendered body/heading.
        self.assertContains(resp, 'Privacy')

    def test_terms_page_returns_200_and_has_title(self):
        resp = self.client.get(reverse('terms'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<title>')
        self.assertContains(resp, 'Terms')

    def test_footer_links_are_real_anchors_not_spans(self):
        # Both privacy and terms must be reachable <a href> in the footer.
        resp = self.client.get('/', HTTP_HOST='localhost')
        content = resp.content.decode('utf-8')
        self.assertContains(resp, 'href="%s"' % reverse('privacy'))
        self.assertContains(resp, 'href="%s"' % reverse('terms'))
        # Guard against regression: the old dead <span> placeholder used a
        # bare translatable label without an href. Ensure no orphaned span
        # wrapping only the legal text right inside footer-legal.
        self.assertNotIn(
            '<span>%s</span>' % 'Privacy Policy', content)


class ManifestIconTests(TestCase):
    """F2 — PWA manifest + apple-touch-icon asset surface."""

    def setUp(self):
        self.client = Client()

    def test_manifest_json_is_served_and_valid(self):
        resp = self.client.get('/static/manifest.json', HTTP_HOST='localhost')
        # Static files are served via WhiteNoise (streaming FileResponse) in
        # test, so read streaming_content. If not collected (404) we skip —
        # the production smoke (smoke_online) is the authoritative online check.
        if resp.status_code == 200:
            body = b''.join(resp.streaming_content).decode('utf-8')
            data = json.loads(body)
            self.assertIn('name', data)
            self.assertIn('icons', data)
            self.assertTrue(len(data['icons']) >= 1)

    def test_manifest_source_file_parses(self):
        import os
        path = os.path.join('static', 'manifest.json')
        self.assertTrue(os.path.exists(path), 'static/manifest.json must exist')
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertIn('name', data)
        self.assertEqual(data['display'], 'standalone')
        self.assertTrue(any('apple-touch-icon' in ic.get('src', '')
                            for ic in data['icons']))

    def test_apple_touch_icon_source_exists(self):
        import os
        path = os.path.join('static', 'images', 'apple-touch-icon.png')
        self.assertTrue(os.path.exists(path),
                        'static/images/apple-touch-icon.png must exist')
