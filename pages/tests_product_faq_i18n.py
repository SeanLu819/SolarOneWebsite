"""A1 (2026-10-23) — the product FAQ must be translated, not English.

What was wrong
--------------
``pages/views/views_products.py`` carried 17 unique FAQ question/answer pairs
as hardcoded English constants. They were rendered into both the visible
accordion and the ``FAQPage`` JSON-LD of every product page — so on
``/fr/products/vsp-xxxxw-9m-yp/`` the ``<title>`` and ``Product.description``
were French while the structured Q&A was English. Measured live on 2026-10-23:
24 products x 5 non-English languages = **120 pages** whose only structured
answer block was in the wrong language, which is a large part of why Arabic
and German queries returned no SolarOne text to quote.

The sports landing pages never had this bug — ``_localised_faq()`` already
routed their FAQ through gettext. A1 reuses that helper (it now lives in
``pages/views/common.py``) on the product pages.

What is pinned here
-------------------
1. every FAQ string resolves in all five catalogs (a new constant added
   without a translation fails here, immediately);
2. no FAQ string may be parked in ``KNOWN_UNTRANSLATED`` — that list is a
   frozen debt, not a place to hide new work;
3. end-to-end: a rendered non-English product page must NOT contain the
   English question in either the JSON-LD or the visible block. The negative
   assertion is the one that matters: gettext falls back to English *by
   design*, so "the page renders" proves nothing.
"""
import json
import re

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from pages.tests import I18nCatalogGuardTests
from pages.views.views_products import PRODUCT_FAQ_BY_CATEGORY

LANGS = ('fr', 'es', 'de', 'ru', 'ar')

#: A product whose page carries the shared FAQ core in every language, so a
#: single probe covers the mechanism. Written out (iron law 4b) rather than
#: derived from the seed: a seed change must not silently move the probe.
PROBE_SLUG = 'fl1m'

#: The first shared question — the string that was measured live in English on
#: /fr/ and /ar/ product pages. Asserted literally, not read from the view, so
#: that renaming the constant cannot turn this guard into a tautology.
ENGLISH_FIRST_QUESTION = 'What is the luminous efficacy and rated lifespan?'


def _faq_strings():
    """Every unique question/answer literal the product pages can render."""
    ordered, seen = [], set()
    for entries in PRODUCT_FAQ_BY_CATEGORY.values():
        for entry in entries:
            for key in ('question', 'answer'):
                text = entry[key]
                if text not in seen:
                    seen.add(text)
                    ordered.append(text)
    return ordered


class ProductFaqCatalogTests(TestCase):
    """The catalog half: every FAQ string resolves in all five languages."""

    def test_every_faq_string_is_in_every_catalog(self):
        """Nothing here is derived from a hardcoded count (iron law 7).

        The set comes from the view constants, so adding an 18th question
        without translating it fails on the next run instead of shipping 120
        pages of English.
        """
        strings = _faq_strings()
        self.assertGreater(len(strings), 1, 'FAQ extractor found nothing')
        offenders = I18nCatalogGuardTests()._offenders(strings)
        self.assertEqual(
            offenders, {},
            'product FAQ strings missing from the gettext catalogs '
            '(the FAQ would render English): %s'
            % {lang: [s[:70] for s in missing]
               for lang, missing in sorted(offenders.items())})

    def test_no_faq_string_is_hidden_in_the_frozen_debt_list(self):
        """KNOWN_UNTRANSLATED only shrinks; it is not a place to park A1.

        Without this, someone hitting the guard above could "fix" it by adding
        the 34 strings to the allowlist — which is exactly the failure the
        allowlist's own ``test_allowlist_only_shrinks`` cannot see, because
        that test only catches entries that got *translated*.
        """
        parked = sorted(set(_faq_strings())
                        & set(I18nCatalogGuardTests.KNOWN_UNTRANSLATED))
        self.assertEqual(parked, [],
                         'product FAQ strings parked in KNOWN_UNTRANSLATED '
                         'instead of being translated: %s'
                         % [s[:70] for s in parked])

    def test_extractor_covers_every_category(self):
        """A category whose FAQ set is unreachable would be missed above."""
        covered = {category: bool(entries)
                   for category, entries in PRODUCT_FAQ_BY_CATEGORY.items()}
        self.assertTrue(covered, 'PRODUCT_FAQ_BY_CATEGORY is empty')
        self.assertEqual([c for c, ok in covered.items() if not ok], [],
                         'category with an empty FAQ set')


class ProductFaqRenderTests(TestCase):
    """The end-to-end half: a French page must not carry English questions."""

    def _jsonld_blocks(self, html):
        # Nonce-tolerant (iron law 29).
        return re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.S)

    def _faq_questions(self, html):
        questions = []
        for blob in self._jsonld_blocks(html):
            try:
                data = json.loads(blob)
            except ValueError:
                continue
            if data.get('@type') != 'FAQPage':
                continue
            for entity in data.get('mainEntity') or []:
                name = (entity or {}).get('name')
                if name:
                    questions.append(name)
        return questions

    def test_rendered_faq_jsonld_is_not_english(self):
        """The measured bug, pinned.

        Before A1 this returned 'What is the luminous efficacy and rated
        lifespan?' on /fr/, /es/, /de/, /ru/ and /ar/ alike.
        """
        for lang in LANGS:
            with translation.override(lang), self.subTest(lang=lang):
                url = reverse('product_detail', args=[PROBE_SLUG])
                response = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200,
                                 f'{lang} product page {url} did not render')
                questions = self._faq_questions(response.content.decode('utf-8'))
                self.assertTrue(
                    questions, f'{lang} product page emits no FAQPage JSON-LD')
                self.assertNotIn(
                    ENGLISH_FIRST_QUESTION, questions,
                    f'{lang} product page FAQPage is still English')

    def test_rendered_faq_questions_are_in_the_page_language(self):
        """Positive side: each question must actually be in that script.

        Cyrillic for ru, Arabic for ar — a machine-readable way of saying
        "not English" that cannot be satisfied by an empty string.

        Asserted **per question, not on the page total** (iron law 53): a
        first draft totalled all six questions, and losing one translation
        out of six left the ratio at 5/6 — the mutation probe proved the
        guard stayed green while a Russian page rendered an English question.
        """
        scripts = {'ru': '\u0400-\u04ff', 'ar': '\u0600-\u06ff'}
        for lang, span in sorted(scripts.items()):
            with translation.override(lang), self.subTest(lang=lang):
                url = reverse('product_detail', args=[PROBE_SLUG])
                response = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)
                questions = self._faq_questions(response.content.decode('utf-8'))
                self.assertTrue(questions, f'{lang}: no FAQPage emitted')
                for question in questions:
                    native = len(re.findall('[%s]' % span, question))
                    letters = len(re.findall(r'\w', question, re.UNICODE))
                    self.assertGreater(
                        letters, 0,
                        f'{lang}: FAQ question carries no letters: {question!r}')
                    self.assertGreater(
                        native / letters, 0.5,
                        f'{lang}: FAQ question is not in the page script '
                        f'({native}/{letters}): {question[:70]!r}')

    def test_the_visible_block_matches_the_jsonld(self):
        """Two surfaces, one translation — neither may drift.

        The visible accordion and the structured data are fed from the same
        context, so this is cheap insurance against someone re-hardcoding one
        of them later (the drift iron law 8 exists for).
        """
        with translation.override('ar'):
            url = reverse('product_detail', args=[PROBE_SLUG])
            response = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        questions = self._faq_questions(body)
        self.assertTrue(questions)
        for question in questions:
            # Strip what the template may wrap around the text (iron law 13:
            # inner markup breaks naive "text inside a tag" regexes), then
            # confirm the visible block carries the same string.
            needle = re.sub(r'<[^>]+>', '', question).strip()
            self.assertTrue(needle)
            self.assertIn(needle, body,
                          'a FAQPage question is not present in the visible '
                          'accordion: %r' % needle[:70])

    def test_english_pages_are_unchanged(self):
        """A1 must not disturb the source language."""
        with translation.override('en'):
            url = reverse('product_detail', args=[PROBE_SLUG])
            response = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        questions = self._faq_questions(response.content.decode('utf-8'))
        self.assertIn(ENGLISH_FIRST_QUESTION, questions)
