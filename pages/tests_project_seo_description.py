"""v1.9.2 guard: project meta description is a SERP snippet, not the body copy.

Before v1.9.2 ``Project.seo_description()`` returned the raw ``description``
field, so all 22 project pages shipped 600-1200 characters of body prose into a
tag Google truncates at ~155, and the snippet opened with a CJK
``【Customer Profile】`` marker. The category keyword never appeared at all.

These tests lock the fix: clamped to 160, keyword-led, marker-free, and
identical across the DB and seed code paths (production runs on the seed one).
"""
import json
import os

from django.test import SimpleTestCase, TestCase

from pages.utils import (
    MAX_SEO_DESCRIPTION_LEN,
    PROJECT_CATEGORY_KEYWORD,
    build_project_og_description,
    build_project_seo_description,
    clean_project_prose,
    get_seo_override,
    project_category_keyword,
)

SEED_PATH = os.path.join(os.path.dirname(__file__), '..', 'seed_data.json')


def _load_seed():
    with open(SEED_PATH, encoding='utf-8') as fh:
        return json.load(fh)


class ProjectSeoDescriptionFormulaTests(SimpleTestCase):
    def test_keyword_leads_and_body_follows(self):
        desc = build_project_seo_description(
            'Perryville High School is a prominent public educational institution.',
            'FOOTBALL_FIELD')
        self.assertTrue(desc.startswith('LED football Stadium Lights — '),
                        desc)

    def test_clean_strips_cjk_section_markers(self):
        cleaned = clean_project_prose(
            '【Customer Profile】\nA venue.  【Scope of Work】\nWe lit it.')
        self.assertNotIn('【', cleaned)
        self.assertNotIn('】', cleaned)
        self.assertNotIn('【Customer Profile】', cleaned)
        self.assertNotIn('\n', cleaned)
        self.assertNotIn('  ', cleaned)
        self.assertEqual(cleaned, 'A venue. We lit it.')

    def test_empty_prose_still_yields_a_keyword(self):
        """A blank description must not collapse the tag to an empty string."""
        self.assertEqual(build_project_seo_description('', 'FOOTBALL_FIELD'),
                         'LED football Stadium Lights | SolarOne')
        self.assertEqual(build_project_seo_description('', 'NONSENSE'),
                         'LED Lighting | SolarOne')

    def test_output_never_exceeds_the_budget(self):
        long_prose = 'Sentence one is here. ' + ('filler words everywhere. ' * 40)
        for sport in PROJECT_CATEGORY_KEYWORD:
            desc = build_project_seo_description(long_prose, sport)
            self.assertLessEqual(len(desc), MAX_SEO_DESCRIPTION_LEN,
                                 f'{sport} overflowed: {len(desc)}')

    def test_truncation_prefers_a_sentence_boundary(self):
        # The first sentence must clear the halfway mark of the budget,
        # otherwise a 12-char snippet would waste most of the SERP line.
        prose = ('This opening sentence is deliberately long enough to clear '
                 'the halfway mark of the available budget. ' + 'padding ' * 40)
        desc = build_project_seo_description(prose, 'FOOTBALL_FIELD')
        self.assertNotIn('…', desc)
        self.assertTrue(desc.endswith('the available budget.'), desc)

    def test_a_too_short_first_sentence_is_rejected_as_the_snippet(self):
        prose = 'Short one. ' + 'padding ' * 40
        desc = build_project_seo_description(prose, 'FOOTBALL_FIELD')
        self.assertTrue(desc.endswith('…'), desc)
        self.assertGreater(len(desc), 80)

    def test_truncation_falls_back_to_a_word_boundary_with_ellipsis(self):
        prose = 'one ' + 'no punctuation at all here ' * 20
        desc = build_project_seo_description(prose, 'FOOTBALL_FIELD')
        self.assertTrue(desc.endswith('…'), desc)
        self.assertNotIn('… ', desc)

    def test_exact_fit_gets_no_ellipsis(self):
        body = 'A perfectly sized sentence.'
        desc = build_project_seo_description(body, 'FOOTBALL_FIELD')
        self.assertFalse(desc.endswith('…'), desc)

    def test_og_description_keeps_the_full_name_unclamped(self):
        og = build_project_og_description(
            'National Olympic Sports Center (Beijing) Tennis Courts', 'TENNIS_COURTS')
        self.assertEqual(
            og,
            'National Olympic Sports Center (Beijing) Tennis Courts'
            ' — LED tennis Court Lights | SolarOne')


class ProjectSeoDescriptionSeedTests(TestCase):
    """Every seeded project, on the code path production actually uses."""

    def test_every_seeded_description_fits_the_serp_budget(self):
        projects = _load_seed()['projects']
        self.assertTrue(projects)
        for item in projects:
            desc = build_project_seo_description(
                item.get('description', ''), item.get('sport_type', ''))
            self.assertLessEqual(len(desc), MAX_SEO_DESCRIPTION_LEN,
                                 f"{item['slug']} is {len(desc)} chars")
            self.assertGreaterEqual(len(desc), 60,
                                    f"{item['slug']} snippet is too thin")

    def test_no_seeded_description_leaks_a_cjk_marker(self):
        for item in _load_seed()['projects']:
            desc = build_project_seo_description(
                item.get('description', ''), item.get('sport_type', ''))
            for marker in ('【', '】', '〔', '〕'):
                self.assertNotIn(marker, desc, f"{item['slug']} leaks {marker}")

    def test_every_seeded_description_carries_its_category_keyword(self):
        for item in _load_seed()['projects']:
            sport = item.get('sport_type', '')
            desc = build_project_seo_description(item.get('description', ''), sport)
            self.assertTrue(
                desc.startswith(project_category_keyword(sport)),
                f"{item['slug']} description does not lead with its keyword")

    def test_og_description_is_never_clamped(self):
        """og has no SERP budget — the full project name must survive."""
        for item in _load_seed()['projects']:
            og = build_project_og_description(
                item.get('title', ''), item.get('sport_type', ''))
            self.assertTrue(og.startswith(item['title']),
                            f"{item['slug']} og lost the full name")

    def test_seed_path_and_formula_agree(self):
        from pages.views.utils import _DictProject
        for item in _load_seed()['projects']:
            obj = _DictProject(item)
            self.assertEqual(
                obj.seo_description('en'),
                build_project_seo_description(
                    item.get('description', ''), item.get('sport_type', '')),
                f"{item['slug']} seed path drifted from the formula")
            self.assertEqual(
                obj.og_description('en'),
                build_project_og_description(
                    item.get('title', ''), item.get('sport_type', '')),
                f"{item['slug']} seed og drifted from the formula")

    def test_explicit_override_still_wins(self):
        from pages.views.utils import _DictProject
        obj = _DictProject({'slug': 'x', 'sport_type': 'FOOTBALL_FIELD',
                            'description': 'Body copy that is long enough to be '
                                           'clamped by the formula for sure.',
                            'translations': {'fr': {'seo_description': 'French override'}}})
        self.assertEqual(obj.seo_description('fr'), 'French override')
        self.assertEqual(get_seo_override(obj, 'seo_description', 'fr'),
                         'French override')
        obj.translations = {}
        self.assertTrue(obj.seo_description('en').startswith('LED football Stadium Lights'))


class ProjectSeoDescriptionRenderedTests(TestCase):
    """The tag the crawler actually reads."""

    def test_rendered_meta_description_is_clamped_and_keyword_led(self):
        resp = self.client.get('/projects/perryville-high-school/',
                                HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        marker = '<meta name="description" content="'
        start = html.index(marker) + len(marker)
        desc = html[start:html.index('"', start)]
        self.assertLessEqual(len(desc), MAX_SEO_DESCRIPTION_LEN, desc)
        self.assertTrue(desc.startswith('LED football Stadium Lights'), desc)
        self.assertNotIn('【', desc)

    def test_rendered_og_description_keeps_the_full_project_name(self):
        resp = self.client.get('/projects/perryville-high-school/',
                                HTTP_HOST='localhost')
        html = resp.content.decode('utf-8')
        marker = '<meta property="og:description" content="'
        self.assertIn(marker, html)
        start = html.index(marker) + len(marker)
        og = html[start:html.index('"', start)]
        self.assertIn('Perryville High School', og)
        self.assertIn('LED football Stadium Lights', og)
