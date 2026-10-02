"""Guard: project detail pages inject a keyword-rich internal anchor link to the
Tier-1/2 SEMrush landing pages, mapped from the project's sport_type.

Non-sports venues (AIRPORT / ROADWAY / INFRASTRUCTURE) must NOT show the block.
The block is rendered by templates/project_detail.html and driven by the
SPORT_TYPE_TO_LANDING map in pages/views/views_projects.py.
"""
import re

from django.test import TestCase


class ProjectRelatedLinkTests(TestCase):
    def _get(self, slug, extra=None):
        headers = {'HTTP_HOST': 'localhost'}
        if extra:
            headers.update(extra)
        return self.client.get('/projects/%s/' % slug, **headers)

    def test_football_project_links_to_football_landing(self):
        resp = self._get('football-field-led-retrofit')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Related Lighting Solutions', content)
        self.assertIn('href="/products/football-stadium-lights/"', content)
        self.assertIn('Football Stadium Lights', content)

    def test_tennis_project_links_to_tennis_landing(self):
        resp = self._get('morgan-state-university-tennis-courts')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('href="/products/tennis-court-lighting/"', content)
        self.assertIn('Tennis Court Lighting', content)

    def test_baseball_project_falls_back_to_sports_hub(self):
        resp = self._get('baseball-field-led-retrofit')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('href="/products/sports-lighting/"', content)
        self.assertIn('LED Stadium Lights', content)

    def test_non_sports_project_has_no_related_link(self):
        # AIRPORT / INFRASTRUCTURE must not inject an irrelevant product link.
        # The CSS class names exist on every page (inline <style>), so we assert
        # on the rendered block LABEL text and the anchor hrefs, not the class.
        resp = self._get('beijing-capital-international-airport')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('Related Lighting Solutions', content)
        self.assertNotIn('/products/football-stadium-lights/', content)
        self.assertNotIn('/products/tennis-court-lighting/', content)
        self.assertNotIn('/products/sports-lighting/', content)

    def test_french_project_renders_translated_anchor(self):
        # French is served via the /fr/ URL prefix (matches production hreflang).
        resp = self.client.get('/fr/projects/football-field-led-retrofit/',
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # French catalog entry for the football anchor phrase.
        self.assertIn('Projecteurs de stade de football', content)
        self.assertNotIn('>Football Stadium Lights<', content)

    def test_related_link_is_a_real_anchor_not_plain_text(self):
        resp = self._get('football-field-led-retrofit')
        content = resp.content.decode()
        # The anchor must wrap the keyword phrase in an <a> tag.
        self.assertTrue(
            re.search(r'<a[^>]*href="/products/football-stadium-lights/"[^>]*>'
                      r'[^<]*Football Stadium Lights[^<]*</a>', content),
            'related link is not a proper anchor around the keyword phrase')
        # The rendered block label must be present (proves the block rendered).
        self.assertIn('Related Lighting Solutions', content)
