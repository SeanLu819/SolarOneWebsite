"""Guard: SEO batch B3 — project Article JSON-LD carries author (no date field).

Per user decision (2026-10-06) the project Article JSON-LD carries only
``author`` (an Organization named after the brand). No date field is emitted
for now: ``datePublished`` is unavailable in seed data, and ``dateModified``
was deferred. Both date keys are explicitly asserted absent so a later change
that silently re-adds a date without a real value is caught.
"""
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
    def test_article_jsonld_has_author_no_date(self):
        resp = self.client.get('/projects/football-field-led-retrofit/',
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        blob = _article_blob(content)
        self.assertIsNotNone(blob, 'project detail must emit an Article JSON-LD')
        # author is an Organization named after the brand (never empty).
        self.assertIn('"author"', blob)
        self.assertIn('"@type": "Organization"', blob)
        # No date field for now (deferred per user): neither key may appear.
        self.assertNotIn('"datePublished"', blob)
        self.assertNotIn('"dateModified"', blob)

    def test_french_project_also_carries_author_no_date(self):
        resp = self.client.get('/fr/projects/football-field-led-retrofit/',
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        blob = _article_blob(content)
        self.assertIsNotNone(blob)
        self.assertIn('"author"', blob)
        self.assertNotIn('"dateModified"', blob)
