"""v1.9.3 guard: CJK section markers never reach visible project copy.

The seeded project ``description`` uses ``【Customer Profile】`` /
``【Scope of Work】`` as pseudo-headings. v1.9.2 cleaned those markers out of
the *meta* channel only, so the rendered body still opened with a Chinese
bracket in front of English sentences — visible to visitors, and read as noise
by AI crawlers (markers sit at the very start of every project page).

The fix routes the body through the same marker scrubber via the ``descrub``
template filter, which is defined once and therefore covers both the DB model
and the seed mirror at the same time. Paragraph structure must survive intact:
the scrub is marker deletion only, with no whitespace normalisation.
"""
import json
import os

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from django.utils.safestring import mark_safe

from pages.utils import clean_project_prose, scrub_project_markers

SEED_PATH = os.path.join(os.path.dirname(__file__), '..', 'seed_data.json')


def _load_seed():
    with open(SEED_PATH, encoding='utf-8') as fh:
        return json.load(fh)


_ROUTE_TEMPLATE = '{% load text_filters %}{{ x|descrub|nl2para }}'


class ScrubProjectMarkersTests(SimpleTestCase):
    def test_markets_are_deleted_and_line_breaks_untouched(self):
        text = '【Scope of Work】\r\nReplaced 36 gantry fixtures.\r\n\r\n【Result】\r\nUniformity up.'
        out = scrub_project_markers(text)
        self.assertNotIn('【', out)
        self.assertNotIn('】', out)
        # The scrub is marker-only: CRLF pairs are preserved character for
        # character, so nl2para still sees the author's own paragraph breaks.
        # 4 = after the first marker, the blank line, and the second marker,
        # plus one trailing break — what matters is that none was normalised.
        self.assertEqual(out.count('\r\n'), 4, out)

    def test_plain_text_passes_through_unchanged(self):
        text = 'Nothing to strip here.\r\nSecond line.'
        self.assertEqual(scrub_project_markers(text), text)

    def test_clean_project_prose_still_flattens_to_one_line(self):
        """The SERP channel keeps its own whitespace policy (v1.9.2 behaviour)."""
        flat = clean_project_prose('【Result】\r\nUniformity up.')
        self.assertNotIn('\n', flat)
        self.assertNotIn('\r', flat)
        self.assertNotIn('【', flat)
        self.assertEqual(flat, 'Uniformity up.')

    def test_clean_and_scrub_stay_in_sync_for_every_seed_project(self):
        for item in _load_seed()['projects']:
            raw = item.get('description') or ''
            clean = clean_project_prose(raw)
            scrubbed = scrub_project_markers(raw)
            # clean is scrub plus the flat-line normalisation, never more.
            self.assertNotIn('【', clean)
            self.assertNotIn('【', scrubbed)


class DescrubFilterTests(SimpleTestCase):
    def test_filter_removes_markers_from_rendered_html(self):
        html = Template(_ROUTE_TEMPLATE).render(
            Context({'x': '【Customer Profile】\r\nPerryville High School is great.'}))
        self.assertNotIn('【', html)
        self.assertIn('Perryville High School', html)

    def test_paragraph_structure_is_preserved_across_all_seed_projects(self):
        """Marker removal must not repackage the body into different paragraphs."""
        raw_tpl = Template('{% load text_filters %}{{ x|nl2para }}')
        for item in _load_seed()['projects']:
            raw = item.get('description') or ''
            before = raw_tpl.render(Context({'x': raw}))
            after = Template(_ROUTE_TEMPLATE).render(Context({'x': raw}))
            self.assertEqual(before.count('<p>'), after.count('<p>'),
                             f'{item["slug"]} paragraph count changed')

    def test_raw_input_is_still_escaped(self):
        """The filter only drops markers; escaping stays `nl2para`'s job."""
        html = Template(_ROUTE_TEMPLATE).render(
            Context({'x': '【Bad】\r\n<script>alert(1)</script>'}))
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_safe_string_identity_is_preserved(self):
        rendered = Template(_ROUTE_TEMPLATE).render(
            Context({'x': mark_safe('【Note】\r\nAlready safe.')}))
        self.assertNotIn('【', rendered)
        self.assertIn('Already safe.', rendered)

    def test_empty_input_is_forgiving(self):
        self.assertEqual(Template(_ROUTE_TEMPLATE).render(Context({'x': ''})), '')
        self.assertEqual(Template(_ROUTE_TEMPLATE).render(Context({'x': None})), '')


class ProjectBodyCopyRenderTests(TestCase):
    """The rendered pages — not just the formula — must be marker-free."""

    def _detail_html(self, slug='perryville-high-school'):
        # The test runner already called setup_test_environment(); calling it
        # again here raises RuntimeError.
        from django.test import Client
        return Client().get(f'/projects/{slug}/', HTTP_HOST='localhost').content.decode('utf-8')

    def test_detail_page_body_copy_has_no_cjk_markers(self):
        html = self._detail_html()
        self.assertNotIn('【', html, 'CJK markers still ship in the body copy')

    def test_detail_page_still_renders_the_body(self):
        html = self._detail_html()
        self.assertIn('Perryville High School', html)
        self.assertIn('detail-desc', html)

    def test_listing_page_cards_have_no_cjk_markers(self):
        from django.test import Client
        html = Client().get('/projects/', HTTP_HOST='localhost').content.decode('utf-8')
        self.assertNotIn('【', html)

    def test_json_ld_description_survives_the_scrub(self):
        import re
        html = self._detail_html()
        match = re.search(r'"description": "((?:[^"\\]|\\.)*)"', html)
        self.assertIsNotNone(match, 'project JSON-LD description missing')
        import json
        value = json.loads('"' + match.group(1) + '"')
        self.assertNotIn('【', value)
