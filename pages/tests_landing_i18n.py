"""Guards the three keyword landing pages across all five non-English locales.

The landing-page templates used hard-coded English <title>/<h1>/meta
description (verbatim SEMrush head keywords) which left /fr/ /es/ /de/ /ru/
/ar/ pages serving an English <title> — a self-contradicting hreflang signal.
The strings now go through {% blocktrans %} and live in .po/.mo.

These tests lock the contract so a future edit cannot silently fall back to
English. They also guard the newline-folding trap: a msgstr longer than ~70
chars is folded across two .po lines, and if the fold eats the separating
space "| SolarOne" quietly becomes "|SolarOne".
"""
import re

from django.test import TestCase
from django.test import Client as TestClient

PAGES = [
    'sports-lighting',
    'football-stadium-lights',
    'tennis-court-lighting',
]
LANGS = ['fr', 'es', 'de', 'ru', 'ar']

# English source strings that must still be served verbatim to EN traffic.
EN_TITLE = {
    'sports-lighting': 'LED Stadium Lights & Sports Lighting Solutions | SolarOne',
    'football-stadium-lights': 'Football Stadium Lights — LED Field Lighting | SolarOne',
    'tennis-court-lighting': 'Tennis Court Lighting — LED Court Lights | SolarOne',
}

# Loose per-language fingerprint: at least one of these must appear, which is
# far more robust than pinning the whole translated title.
FINGERPRINT = {
    'fr': ['rojecteur', 'clairage', 'stade'],
    'es': ['rojector', 'luminación', 'estadio'],
    'de': ['Stadion', 'leuchtung'],
    'ru': ['ожектор', 'освещ', 'стадион'],
    'ar': ['ضاءة', 'ملعب', 'إض'],
}

SPACED_BRANDSUFFIX = '| SolarOne'


def _title_of(html):
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
    return m.group(1).strip() if m else ''


def _meta_of(html):
    m = re.search(
        r'<meta name="description" content="(.*?)"',
        html, re.S,
    )
    return m.group(1).strip() if m else ''


def _h1_of(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if not m:
        return ''
    inner = re.search(r'>(.*?)<', m.group(1), re.S)
    return (inner.group(1).strip() if inner else m.group(1).strip())


class LandingPageLocalizationTests(TestCase):
    """Every landing page must render a localized head in all five locales."""

    def test_every_locale_serves_a_localized_title(self):
        for lang in LANGS:
            for slug in PAGES:
                with self.subTest(lang=lang, slug=slug):
                    html = self._get(lang, slug)
                    title = _title_of(html)
                    if title == EN_TITLE[slug]:
                        self.fail(
                            '%s/%s fell back to the English title: %r' % (lang, slug, title)
                        )
                    self.assertTrue(
                        any(k.lower() in title.lower() for k in FINGERPRINT[lang]),
                        'no %s fingerprint in title %r' % (lang, title),
                    )

    def test_every_locale_serves_a_localized_h1(self):
        for lang in LANGS:
            for slug in PAGES:
                with self.subTest(lang=lang, slug=slug):
                    html = self._get(lang, slug)
                    h1 = _h1_of(html).replace('&amp;', '&')
                    if h1 == EN_TITLE[slug].split(' |')[0]:
                        self.fail('%s/%s H1 fell back to English: %r' % (lang, slug, h1))
                    self.assertTrue(
                        any(k.lower() in h1.lower() for k in FINGERPRINT[lang]),
                        'no %s fingerprint in H1 %r' % (lang, h1),
                    )

    def test_every_locale_serves_a_localized_meta_description(self):
        for lang in LANGS:
            for slug in PAGES:
                with self.subTest(lang=lang, slug=slug):
                    html = self._get(lang, slug)
                    desc = _meta_of(html)
                    self.assertTrue(len(desc) > 40, '%s/%s short meta: %r' % (lang, slug, desc))
                    self.assertNotIn('stadium light poles and modular', desc)

    def test_translated_titles_keep_the_space_before_the_brand_suffix(self):
        """A folded .po msgstr must not swallow the space in '| SolarOne'."""
        for lang in LANGS:
            for slug in PAGES:
                with self.subTest(lang=lang, slug=slug):
                    html = self._get(lang, slug)
                    title = _title_of(html)
                    self.assertTrue(
                        title.endswith(SPACED_BRANDSUFFIX),
                        '%s/%s title does not end with %r: %r'
                        % (lang, slug, SPACED_BRANDSUFFIX, title),
                    )

    def test_english_traffic_still_gets_the_verbatim_keyword_titles(self):
        """EN must keep the raw SEMrush wording — translation must not leak in."""
        for slug in PAGES:
            with self.subTest(slug=slug):
                html = self._get('en', slug)
                self.assertEqual(_title_of(html), EN_TITLE[slug])

    def _get(self, lang, slug):
        # English has no /en/ prefix (i18n_patterns, prefix_default_language=False).
        url = '/products/%s/' % slug if lang == 'en' else '/%s/products/%s/' % (lang, slug)
        response = TestClient().get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200, '%s returned %s'
                         % (url, response.status_code))
        return response.content.decode('utf-8')
