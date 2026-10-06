"""P2 SEO-formula guards — keyword differentiation and the budget clamps.

Three defects from the 2026-10-06 long-tail audit, all in
``pages/utils.py``:

**P2-A — eleven product pages opened with the same generic phrase.**
``CATEGORY_KEYWORD`` maps ``AREA_SITE`` to ``LED Area & Site Lighting``, and
eleven products carry that category — including the six M Series modules,
which the repository's own copy calls floodlights ("the FL M-series floodlight
family"), plus two RGB pages. They were bidding against each other on one
phrase. ``SLUG_KEYWORD_OVERRIDE`` now gives the modules and the RT410 their
own wording, splitting one eleven-way collision into seven distinct head
phrases.

**P2-B — 100 of 120 non-English titles started with a database enum.**
``_seo_keyword`` used to localise via ``obj.t('category', lang)``;
``translate()`` falls back to the English value when a translation is missing,
and the English value of ``category`` is the stored enum. So
``/fr/products/fl6m/`` was titled ``AREA_SITE FL6M-480W-30K-S | SolarOne``.
The wording now comes from ``CATEGORY_KEYWORD_I18N``.

**P2-C — the title had no length clamp and the description cut mid-word.**
``mseries-gs`` rendered a 61-character title (its ``name`` is 25 characters
with no ``model_number`` to shorten it), and ``build_seo_description`` ended
snippets with ``... and commercial lighting pro...``.

Expectation sourcing (iron law 4b): every expected phrase and every threshold
here is a **product decision written out literally**. Nothing is derived from
the constant it validates — deriving them would make a guard that shrinks the
requirement stay green, the exact trap hit in the v1.10.18 srcset guards.
"""
from django.test import SimpleTestCase, TestCase

from pages.utils import (
    CATEGORY_KEYWORD,
    CATEGORY_KEYWORD_I18N,
    MAX_SEO_DESCRIPTION_LEN,
    MAX_SEO_TITLE_LEN,
    SLUG_KEYWORD_OVERRIDE,
    build_seo_description,
    build_seo_title,
)
from pages.views.utils import _DictProduct, _load_seed

LANGS = ('en', 'fr', 'es', 'de', 'ru', 'ar')
NON_ENGLISH = ('fr', 'es', 'de', 'ru', 'ar')

#: Product decision: the head phrase each override group must produce. Written
#: out so a silent edit to the copy table shows up as a failure rather than as
#: a quietly different ranking target.
EXPECTED_OVERRIDE_PHRASES = {
    'fl4m': 'Modular LED Flood Light',
    'fl6m': 'Modular LED Flood Light',
    'fl9m': 'Modular LED Flood Light',
    'fl12m': 'Modular LED Flood Light',
    'fl16m': 'Modular LED Flood Light',
    'fl9m-rgbw': 'Modular LED Flood Light RGBW',
    'rt410-series': 'LED Stadium Light',
}

#: Product decision: a title must not put more than this many pages on the
#: same head phrase. Before P2-A the worst group was 11; the fix targets 7
#: groups for 24 products, so the ceiling is set just above that with room
#: for a future addition, not derived from the current distribution.
MAX_PAGES_PER_HEAD_PHRASE = 8

def _head_phrase(title):
    """The leading keyword of a title, i.e. everything before the identifier.

    Titles are ``{keyword} {identifier} | SolarOne`` with an optional
    `` — {power}`` tail. Taking the first three words is enough to group by
    head phrase without depending on the formula's exact assembly order.
    """
    body = title.split('|')[0].strip()
    return ' '.join(body.split()[:3])


class SlugKeywordOverrideTests(SimpleTestCase):
    """P2-A — the override table is populated and points at real products."""

    def test_override_table_is_populated(self):
        self.assertTrue(
            SLUG_KEYWORD_OVERRIDE,
            'SLUG_KEYWORD_OVERRIDE is empty — the eleven-way AREA_SITE '
            'collision is back')

    def test_override_phrases_match_the_product_decision(self):
        for slug, phrase in EXPECTED_OVERRIDE_PHRASES.items():
            with self.subTest(slug=slug):
                self.assertIn(slug, SLUG_KEYWORD_OVERRIDE)
                self.assertEqual(SLUG_KEYWORD_OVERRIDE[slug], phrase)

    def test_override_keys_are_real_slugs(self):
        slugs = {p.get('slug', '') for p in _load_seed()['products']}
        for slug in SLUG_KEYWORD_OVERRIDE:
            with self.subTest(slug=slug):
                self.assertIn(slug, slugs)

    def test_override_phrases_differ_from_the_category_phrase(self):
        """An override identical to the category phrase is a no-op."""
        for slug, phrase in SLUG_KEYWORD_OVERRIDE.items():
            category = next(
                p.get('category', '') for p in _load_seed()['products']
                if p.get('slug') == slug)
            with self.subTest(slug=slug):
                self.assertNotEqual(
                    phrase, CATEGORY_KEYWORD.get(category, ''),
                    'the override repeats the category phrase, so it changes '
                    'nothing')

    def test_the_eleven_way_collision_is_gone(self):
        """The specific regression P2-A was written for.

        Asserted as a count so that adding one more override to a different
        family stays fine, while re-merging the M Series under AREA_SITE
        would fail.
        """
        heads = {}
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            heads.setdefault(_head_phrase(p.seo_title('en')), []).append(p.slug)
        worst = max(len(v) for v in heads.values())
        self.assertLessEqual(
            worst, MAX_PAGES_PER_HEAD_PHRASE,
            'too many pages share one head phrase: %r'
            % {k: v for k, v in heads.items() if len(v) == worst})
        self.assertGreater(
            len(heads), 1,
            'every product now leads with the same phrase')


class LocalisedKeywordTests(TestCase):
    """P2-B — no locale may emit a stored category enum."""

    def test_no_title_anywhere_contains_a_category_enum(self):
        """The whole point of the batch, asserted across the real seed data."""
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            for lang in LANGS:
                with self.subTest(slug=p.slug, lang=lang):
                    title = p.seo_title(lang)
                    for enum in CATEGORY_ENUM_VALUES:
                        self.assertNotIn(
                            enum, title,
                            '%s/%s leaks the stored enum %r: %r'
                            % (p.slug, lang, enum, title))

    def test_every_used_category_has_a_translation_for_every_locale(self):
        used = {p.get('category', '') for p in _load_seed()['products']}
        for category in sorted(used):
            phrases = CATEGORY_KEYWORD_I18N.get(category)
            with self.subTest(category=category):
                self.assertIsNotNone(
                    phrases,
                    'no localised keyword for %s — its non-English titles '
                    'fall back to English' % category)
                for lang in NON_ENGLISH:
                    self.assertTrue(
                        phrases.get(lang),
                        'category %s has no %s phrase' % (category, lang))

    def test_no_locale_falls_back_to_english(self):
        """Asserted, not assumed: a missing entry is a silent regression.

        The fallback itself is safe (English beats an enum), but it undoes the
        localisation this batch delivers, so it has to be loud.
        """
        offenders = []
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            for lang in NON_ENGLISH:
                title = p.seo_title(lang)
                english = p.seo_title('en')
                if title == english:
                    offenders.append((p.slug, lang))
        self.assertEqual(
            offenders, [],
            'these pages serve the English title in a non-English locale '
            '(missing CATEGORY_KEYWORD_I18N entry): %r' % (offenders,))

    def test_translated_phrase_is_not_the_english_one(self):
        for category, phrases in CATEGORY_KEYWORD_I18N.items():
            english = CATEGORY_KEYWORD.get(category, '')
            for lang, phrase in phrases.items():
                with self.subTest(category=category, lang=lang):
                    self.assertNotEqual(
                        phrase, english,
                        'the %s phrase for %s is just the English one'
                        % (lang, category))

    def test_german_highbay_keeps_its_bilingual_spelling(self):
        """A deliberate existing decision, pinned so a sweep cannot undo it.

        German lighting trade usage keeps the English ``Highbay``; the site has
        shipped ``Highbay & Lowbay`` in German since the sidebar was written.
        """
        self.assertEqual(
            CATEGORY_KEYWORD_I18N['HIGHBAY_LOWBAY']['de'], 'Highbay & Lowbay')


#: The stored enum values, written out literally rather than read from
#: ``Product.CATEGORY_CHOICES`` (iron law 4b).
CATEGORY_ENUM_VALUES = (
    'AREA_SITE', 'SPORTS_LIGHTING', 'FLOODLIGHT',
    'HIGHBAY_LOWBAY', 'ROADWAY', 'ACCESSORY', 'MODULAR', 'OTHER',
)


class SeoBudgetClampTests(TestCase):
    """P2-C — the title and description fit the SERP budget, cleanly."""

    def test_every_english_title_fits(self):
        over = []
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            title = p.seo_title('en')
            if len(title) > MAX_SEO_TITLE_LEN:
                over.append((p.slug, len(title), title))
        self.assertEqual(over, [], 'titles over budget: %r' % (over,))

    def test_every_locale_title_fits(self):
        """A localised title can be longer than the English one."""
        over = []
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            for lang in LANGS:
                title = p.seo_title(lang)
                if len(title) > MAX_SEO_TITLE_LEN:
                    over.append((p.slug, lang, len(title), title))
        self.assertEqual(over, [], 'titles over budget: %r' % (over,))

    def test_titles_stay_unique(self):
        """Keyword overlap must not collapse two pages onto one title."""
        for lang in LANGS:
            seen = {}
            for item in _load_seed()['products']:
                p = _DictProduct(item)
                title = p.seo_title(lang)
                with self.subTest(lang=lang, slug=p.slug):
                    self.assertNotIn(
                        title, seen,
                        'title collides with %r in %s: %r'
                        % (seen.get(title), lang, title))
                    seen[title] = p.slug

    def test_clamped_title_keeps_keyword_and_brand(self):
        """The cut may only shorten the identifier.

        ``mseries-gs`` is the case that motivated the clamp: 25-character
        name, no ``model_number``, 61-character result. What must survive is
        the keyword (it is the ranking target) and the brand.
        """
        p = _DictProduct({
            'slug': 'mseries-gs', 'name': 'Glare Shield for M series',
            'category': 'ACCESSORY', 'model_number': '', 'power': '',
        })
        title = build_seo_title(p, 'en')
        self.assertLessEqual(len(title), MAX_SEO_TITLE_LEN)
        self.assertIn('LED Lighting Accessories', title)
        self.assertTrue(title.endswith('| SolarOne'))
        # And the untruncated name is still available for the H1 / og:title.
        self.assertEqual(p.name, 'Glare Shield for M series')

    def test_every_description_fits(self):
        over = []
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            desc = build_seo_description(p, 'en')
            if len(desc) > MAX_SEO_DESCRIPTION_LEN:
                over.append((p.slug, len(desc), desc))
        self.assertEqual(over, [], 'descriptions over budget: %r' % (over,))

    def test_description_never_ends_mid_word(self):
        """The old ``desc[:157] + '...'`` produced "… lighting pro...".

        🔴 v1.10.21 — the first version of this test walked the real seed data
        and found nothing, because the per-category tails introduced in P2-C
        made every description fit the budget: **the clamp branch stopped
        executing**, so the guard had no way to see a mid-word cut even when
        the hard cut was put back (a mutation probe proved exactly that). A
        guard that can only fail if the data happens to be long enough is not
        a guard. The clamp is therefore exercised on a deliberately
        over-budget product, and the real-data walk is kept as a second,
        weaker check.
        """
        # A synthetic product whose identifier alone blows the budget.
        long_model = 'X' * 40 + '-1000W-30K-S'
        p = _DictProduct({
            'slug': 'long', 'name': 'Long', 'category': 'AREA_SITE',
            'model_number': long_model, 'power': '1000W',
        })
        desc = build_seo_description(p, 'en')
        self.assertLessEqual(len(desc), MAX_SEO_DESCRIPTION_LEN,
                             'the clamp did not bring an over-budget '
                             'description inside the limit: %d chars' % len(desc))
        self.assertFalse(
            desc.endswith('...'),
            'the clamp fell back to a hard cut, which is exactly the defect: %r'
            % desc)
        self.assertTrue(
            desc.endswith(('.', '…')),
            'a clamped description must end on a sentence or ellipsis: %r' % desc)
        # The stem must end on a real boundary. A word-boundary clamp may stop
        # at a space, a comma or a semicolon — what it must never do is stop
        # *inside* a word, which is what a character-count cut produces.
        stem = desc.rstrip('.…')
        self.assertTrue(
            stem and (stem[-1].isalpha() or stem[-1] in ',;'),
            'description ends mid-word: %r' % desc)

        # And the real data must never end mid-word either.
        offenders = []
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            desc = build_seo_description(p, 'en')
            if not desc.endswith(('.', '…')):
                offenders.append((p.slug, desc[-30:]))
        self.assertEqual(
            offenders, [],
            'descriptions do not end on a sentence: %r' % (offenders,))

    def test_descriptions_differ_by_category_tail(self):
        """The tail used to be one sentence on all 24 pages.

        Checked across categories rather than pairs of products, because the
        tail is chosen by category: two products in the same category are
        expected to share it.
        """
        tails = {}
        for item in _load_seed()['products']:
            p = _DictProduct(item)
            desc = build_seo_description(p, 'en')
            _, _, tail = desc.rpartition(' for ')
            tails.setdefault(p.category, set()).add(tail)
        self.assertGreater(
            len(tails), 2,
            'the description tail is still the same sentence everywhere')
        for category, variants in sorted(tails.items()):
            with self.subTest(category=category):
                self.assertEqual(
                    len(variants), 1,
                    'products in %s emit different tails, so the tail is not '
                    'category-driven: %r' % (category, variants))
        all_tails = [next(iter(v)) for v in tails.values()]
        self.assertEqual(
            len(set(all_tails)), len(all_tails),
            'two categories share a description tail: %r' % (all_tails,))

    def test_roadway_description_does_not_claim_sports(self):
        """The old tail said "professional sports" on the street-lighting page.

        A concrete instance of the generic-tail bug, pinned so a future shared
        tail cannot come back.
        """
        for slug in ('rt600sl-t', 'rt820sl-t'):
            p = _DictProduct(
                next(i for i in _load_seed()['products'] if i['slug'] == slug))
            desc = build_seo_description(p, 'en')
            with self.subTest(slug=slug):
                self.assertNotIn('sports', desc.lower())
                self.assertNotIn('stadium', desc.lower())
                self.assertIn('road', desc.lower())
