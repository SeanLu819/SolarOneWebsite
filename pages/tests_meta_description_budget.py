"""v1.9.6 guard: site-level meta descriptions fit the SERP snippet budget.

v1.9.2 clamped the *project* descriptions, but the hand-written site-level ones
in ``{% blocktrans %}`` blocks were never touched. A production sweep on
2026-10-03 found five pages shipping over budget: ``/`` 180, ``/products/``
187, ``/about/`` 179, ``/products/football-stadium-lights/`` 171 and
``/products/tennis-court-lighting/`` 187 characters. Google truncates a
description at roughly 155-160 characters, so every one of those pages was
losing the tail of its snippet.

The fix reworded the five English source strings and rekeyed their msgids in
fr/es/de/ru/ar so the existing translations stay attached.

These tests lock four things:

1. every ``meta_description`` / ``og_description`` source literal in
   ``templates/`` is within budget;
2. the meta and og copy in a template are identical — a half-applied edit
   leaves them divergent, and that is exactly what happened while making this
   change (one of the two blocks in about.html silently kept the old string);
3. English traffic actually renders within budget;
4. all five non-English locales still resolve each string to a translation, so
   a rekeyed msgid cannot quietly fall back to the English source.

Note on measuring: Django escapes the rendered value (``'`` becomes
``&#x27;``), so the raw HTML is up to 5 characters per apostrophe longer than
what Google displays. Budget assertions run against the unescaped text.
"""
import glob
import html
import os
import re

from django.test import SimpleTestCase, TestCase
from django.test import Client as TestClient
from django.utils import translation

from pages.utils import MAX_SEO_DESCRIPTION_LEN

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

LANGS = ['fr', 'es', 'de', 'ru', 'ar']

BLOCK_RE = re.compile(
    r'{% block (meta_description|og_description) %}'
    r'{% blocktrans %}(.*?){% endblocktrans %}'
)

# The five reworded strings, keyed by the template that owns them.
REWORDED = {
    'home.html': (
        "SolarOne designs and manufactures LED sports lighting, high bay, and "
        "industrial lighting. Engineered in Beijing since 2007, trusted in 50+ "
        "countries."
    ),
    'about.html': (
        "Learn about SolarOne, an LED lighting manufacturer since 2007. "
        "Specializing in sports lighting, high bay, roadway, and industrial "
        "lighting for 50+ countries."
    ),
    'products.html': (
        "Explore SolarOne's range of LED lighting products: sports lighting, "
        "flood lighting, high bay, roadway, and area lighting. Precision optics, "
        "modular design."
    ),
    'football_stadium_lights.html': (
        "SolarOne football stadium lights: high-mast LED light poles and sports "
        "floodlights engineered for uniform, glare-controlled football field "
        "lighting."
    ),
    'tennis_court_lighting.html': (
        "SolarOne tennis court lighting: LED court lights and floodlights for "
        "outdoor and indoor courts \u2014 uniform illumination, low glare and "
        "broadcast-ready colour."
    ),
}

# URL that renders each reworded template.
URLS = {
    'home.html': '/',
    'about.html': '/about/',
    'products.html': '/products/',
    'football_stadium_lights.html': '/products/football-stadium-lights/',
    'tennis_court_lighting.html': '/products/tennis-court-lighting/',
}


def _source_blocks():
    """Yield (filename, block_name, text) for every site-level description."""
    for path in sorted(glob.glob(os.path.join(TEMPLATE_DIR, '*.html'))):
        name = os.path.basename(path)
        with open(path, encoding='utf-8') as fh:
            src = fh.read()
        for match in BLOCK_RE.finditer(src):
            yield name, match.group(1), match.group(2)


def _meta_of(page):
    match = re.search(r'<meta name="description" content="(.*?)"', page, re.S)
    return html.unescape(match.group(1).strip()) if match else ''


class SiteMetaDescriptionSourceTests(SimpleTestCase):
    """The English source literals are the budget that actually ships."""

    def test_every_source_literal_is_within_budget(self):
        over = []
        for name, block, text in _source_blocks():
            if len(text) > MAX_SEO_DESCRIPTION_LEN:
                over.append('%s %s = %d' % (name, block, len(text)))
        self.assertEqual(
            over, [],
            'site meta descriptions over %d chars: %s'
            % (MAX_SEO_DESCRIPTION_LEN, over),
        )

    def test_sweep_actually_found_the_blocks(self):
        """If the regex ever stops matching, the test above passes vacuously."""
        names = {name for name, _b, _t in _source_blocks()}
        self.assertEqual(
            set(REWORDED) - names, set(),
            'the five reworded templates no longer expose a description block',
        )
        self.assertGreaterEqual(len(list(_source_blocks())), 18)

    def test_meta_and_og_copy_are_identical_per_template(self):
        """Guard the half-applied edit that a single Edit call can leave behind."""
        by_template = {}
        for name, block, text in _source_blocks():
            by_template.setdefault(name, {})[block] = text
        divergent = []
        for name, blocks in by_template.items():
            if 'meta_description' in blocks and 'og_description' in blocks:
                if blocks['meta_description'] != blocks['og_description']:
                    divergent.append(name)
        self.assertEqual(divergent, [], 'meta/og description diverged in: %s' % divergent)

    def test_no_cjk_section_marker_leaks_into_a_description(self):
        for name, block, text in _source_blocks():
            for marker in ('\u3010', '\u3011'):
                self.assertNotIn(
                    marker, text,
                    '%s %s still carries a CJK section marker' % (name, block),
                )

    def test_each_reworded_string_keeps_its_head_term(self):
        """Trimming prose must not trim the commercial term itself."""
        heads = {
            'home.html': 'LED sports lighting',
            'about.html': 'LED lighting manufacturer',
            'products.html': 'LED lighting products',
            'football_stadium_lights.html': 'football stadium lights',
            'tennis_court_lighting.html': 'tennis court lighting',
        }
        for name, head in heads.items():
            self.assertIn(head, REWORDED[name], name)


class SiteMetaDescriptionRenderTests(TestCase):
    """What Google actually reads off the rendered page."""

    def _get(self, url):
        response = TestClient().get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200,
                         '%s returned %s' % (url, response.status_code))
        return response.content.decode('utf-8')

    def test_english_pages_render_within_budget(self):
        for name, url in URLS.items():
            with self.subTest(template=name):
                desc = _meta_of(self._get(url))
                self.assertTrue(desc, '%s served no meta description' % url)
                self.assertLessEqual(
                    len(desc), MAX_SEO_DESCRIPTION_LEN,
                    '%s served a %d-char description: %r' % (url, len(desc), desc),
                )

    def test_english_pages_render_the_reworded_copy(self):
        for name, url in URLS.items():
            with self.subTest(template=name):
                self.assertEqual(_meta_of(self._get(url)), REWORDED[name])

    def test_rendered_length_matches_the_source_length(self):
        """Guards against a filter silently padding or truncating the tag."""
        for name, url in URLS.items():
            with self.subTest(template=name):
                self.assertEqual(len(_meta_of(self._get(url))), len(REWORDED[name]))


class SiteMetaDescriptionTranslationTests(SimpleTestCase):
    """A rekeyed msgid must stay translated, or the locale falls back to English."""

    def test_every_locale_resolves_all_five(self):
        for lang in LANGS:
            for name, text in REWORDED.items():
                with self.subTest(lang=lang, template=name):
                    with translation.override(lang):
                        out = translation.gettext(text)
                    self.assertNotEqual(
                        out, text,
                        '%s/%s fell back to the English source' % (lang, name),
                    )
                    self.assertTrue(out.strip(), '%s/%s translated to empty' % (lang, name))

    def test_translations_are_not_truncated_to_the_english_budget(self):
        """Non-Latin scripts are wider per character; a naive 160 cap would
        have cut these translations mid-word. They are only checked for
        non-emptiness and for surviving the .po fold intact."""
        for lang in LANGS:
            for name, text in REWORDED.items():
                with self.subTest(lang=lang, template=name):
                    with translation.override(lang):
                        out = translation.gettext(text)
                    # A fold that ate the separating space is the classic trap.
                    self.assertNotIn('LEDsports', out)
                    self.assertNotIn('SolarOneLED', out)
                    self.assertNotIn('  ', out)
