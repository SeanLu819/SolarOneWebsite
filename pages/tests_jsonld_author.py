"""Guard: SEO batch B3 — project Article JSON-LD carries author + dateModified."""
import re

from django.test import TestCase


def _article_blob(content):
    """Return the JSON-LD script whose body is the Article block."""
    scripts = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        content, re.DOTALL)
    for s in scripts:
        if '"@type": "Article"' in s:
            return s
    return None


class ProjectJsonLdAuthorTests(TestCase):
    def test_article_jsonld_has_author_and_date_modified(self):
        resp = self.client.get('/projects/football-field-led-retrofit/',
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        blob = _article_blob(content)
        self.assertIsNotNone(blob, 'project detail must emit an Article JSON-LD')
        # author is an Organization named after the brand (never empty).
        self.assertIn('"author"', blob)
        self.assertIn('"@type": "Organization"', blob)
        self.assertIn('"dateModified"', blob)
        # dateModified must be a real ISO date, not blank.
        self.assertRegex(
            blob, r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"',
            'dateModified must be a valid ISO date')
        # datePublished is intentionally omitted (seed projects have no date).
        self.assertNotIn('"datePublished"', blob)

    def test_french_project_also_carries_author(self):
        resp = self.client.get('/fr/projects/football-field-led-retrofit/',
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        blob = _article_blob(content)
        self.assertIsNotNone(blob)
        self.assertIn('"author"', blob)
        self.assertRegex(
            blob, r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"')
