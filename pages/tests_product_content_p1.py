"""P1 content guards — heading hierarchy, FAQ differentiation, description depth.

The v1.10.19 audit measured what a crawler actually sees on a product page:

* the ``<h1>`` was the bare model code (``FL6M``) with no commercial spec;
* the four section labels (beam angle, dimensions, energy data, ordering) were
  ``<span>``s, so photometric / beam-angle / ordering / certification long-tail
  queries had data on the page but **no semantic marker**;
* the same six FAQ entries rendered on all 24 pages — 94.3% of the body text of
  ``/products/fl6m/`` and byte-identical across every product, so the 24 URLs
  competed with each other on identical questions;
* the product description was 11 words on six pages and 1 word (``RT590FL-S``)
  on another.

v1.10.20 fixed all four. These guards lock them.

Expectation sourcing (iron law 4b): every threshold and every expected string
here is a **product decision written out literally**. Nothing is derived from
the implementation constants it validates — deriving them would make a guard
that shrinks the requirement stay green (the exact trap hit while writing the
srcset guards in v1.10.18).
"""
import json
import re

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation

from pages.models import Product
from pages.views.utils import _DictProduct, _load_seed
from pages.views.views_products import (
    PRODUCT_FAQ_BY_CATEGORY,
    product_faq_for,
)

LANGS = ('en', 'fr', 'es', 'de', 'ru', 'ar')

#: A description longer than this cannot carry the application, the
#: electrical envelope and the mounting story. Measured baseline before the
#: batch was 11 words (six pages) and 1 word (rt590fl-s).
MIN_DESCRIPTION_WORDS = 80

#: Product decision: two product descriptions whose word-bigram Jaccard
#: similarity reaches this level are treated as the same copy. Doorway pages
#: are near-identical rather than bit-identical, so an exact-match check is
#: not enough — see the mutation note on the test that uses it.
SIMILARITY_LIMIT = 0.80

#: Product decision: the SERP budget for a meta description. Already the
#: project-side constant; repeated here so this module is self-contained and
#: the check does not silently pass if the other module's value moves.
MAX_DESCRIPTION_WORDS = 160

#: The four labels that must be real headings. Listed literally: deriving them
#: from the CSS class names would hide a rename.
SECTION_HEADING_CLASSES = (
    'detail-beam-angle-label',
    'detail-dimension-label',
    'detail-energy-label',
    'detail-ordering-label',
)

#: ``product_overview.html`` deliberately has NO technical blocks — its own
#: header comment says so: "Deliberately has NO technical blocks (beam angle,
#: dimensions, energy/performance table, ordering table, CTA): those live in
#: product_detail.html for leaf products." Only the leaf template carries the
#: four section labels, so only that one is asserted for them.
TECHNICAL_TEMPLATE = 'product_detail.html'

#: Both product templates share the hero / H1 treatment, so both are asserted
#: for those.
BOTH_TEMPLATES = ('product_detail.html', 'product_overview.html')

#: Every category a product can carry **that is actually in use**. Written out
#: literally (iron law 4b). ``MODULAR`` and ``OTHER`` exist in
#: ``Product.CATEGORY_CHOICES`` but no seeded product uses them, and
#: ``product_faq_for`` already degrades to the shared core for them, so
#: requiring a bespoke set would fail on a category nothing renders.
EXPECTED_CATEGORIES = frozenset({
    'AREA_SITE', 'SPORTS_LIGHTING', 'FLOODLIGHT',
    'HIGHBAY_LOWBAY', 'ROADWAY', 'ACCESSORY',
})

#: Categories the product table still allows but nothing uses. Listed so the
#: test fails loudly if one is adopted without a FAQ set.
RESERVED_CATEGORIES = frozenset({'MODULAR', 'OTHER'})

#: A question that only makes sense on a sports/broadcast page. Used to prove
#: the split is real and not a cosmetic reshuffle of the same six entries.
SPORTS_ONLY_QUESTION = 'flicker-free for broadcast'

#: A question that only makes sense on an accessory page.
ACCESSORY_ONLY_QUESTION = 'glare shield'


def _products():
    return {p['slug']: p for p in _load_seed().get('products', [])}


class ProductHeadingHierarchyTests(SimpleTestCase):
    """P1-B — the section structure must be real headings, in both templates."""

    def _template(self, name):
        from django.conf import settings
        path = settings.BASE_DIR / 'templates' / name
        with open(path, encoding='utf-8') as fh:
            return fh.read()

    def test_all_four_section_labels_are_h2(self):
        """Only the leaf template has technical blocks; see
        ``TECHNICAL_TEMPLATE``. The overview template deliberately omits them,
        so demanding the four labels there would force a fake section onto a
        page whose own header comment says it should not have one.
        """
        src = self._template(TECHNICAL_TEMPLATE)
        for cls in SECTION_HEADING_CLASSES:
            with self.subTest(template=TECHNICAL_TEMPLATE, label=cls):
                self.assertRegex(
                    src, r'<h2 class="%s">' % re.escape(cls),
                    f'{TECHNICAL_TEMPLATE}: {cls} must be an <h2> so the section '
                    f'is machine-readable, not a styled <span>')
                self.assertNotRegex(
                    src, r'<span class="%s"' % re.escape(cls),
                    f'{TECHNICAL_TEMPLATE}: {cls} is back to a <span>')

    def test_overview_template_has_no_technical_labels(self):
        """Guards the split in the other direction.

        If someone copies the technical blocks into the overview template, the
        two pages would duplicate the same H2 sections and compete with each
        other — the same doorway problem the FAQ split just fixed.
        """
        src = self._template('product_overview.html')
        for cls in SECTION_HEADING_CLASSES:
            with self.subTest(label=cls):
                self.assertNotIn(
                    cls, src,
                    'product_overview.html must stay free of the technical '
                    'section labels; those belong to product_detail.html')

    def test_h2_visual_reset_is_present(self):
        """A bare ``<h2>`` inherits UA margin/bold, changing the layout.

        The four resets ship as ONE grouped rule (comma-separated selectors),
        so the assertion looks for the whole group rather than four separate
        blocks — otherwise a correct grouped rule reads as four missing ones.
        """
        src = self._template(TECHNICAL_TEMPLATE)
        # Anchor on the marker comment the reset ships with, then read the
        # single rule that follows it. Locating the rule by proximity to its
        # own comment avoids a greedy selector regex wandering into an
        # unrelated block.
        marker = 'the four section labels became real <h2>s'
        self.assertIn(
            marker, src,
            'the h2 visual reset and its explanatory comment are gone')
        after = src.split(marker, 1)[1]
        # The comment closes, then the grouped selector, then the body. Read
        # from the comment terminator so the rule is bounded on both sides.
        self.assertIn('*/', after, 'the reset comment is not terminated')
        after = after.split('*/', 1)[1]
        rule = re.search(r'\{[^}]*\}', after)
        self.assertIsNotNone(rule, 'the reset rule body is missing')
        body = rule.group(0)
        selectors = after[:rule.start()]
        for cls in SECTION_HEADING_CLASSES:
            with self.subTest(label=cls):
                self.assertIn(
                    '.%s' % cls, selectors,
                    f'{cls} is not covered by the grouped reset selector')
        self.assertRegex(body, r'margin:\s*0',
                         'the h2 reset must zero the UA margin')
        self.assertRegex(body, r'font-weight:\s*normal',
                         'the h2 reset must drop the UA bold weight')

    def test_h1_carries_the_wattage(self):
        for name in BOTH_TEMPLATES:
            src = self._template(name)
            with self.subTest(template=name):
                self.assertIn(
                    '<span class="section-title-power">{{ product.power }}</span>',
                    src,
                    f'{name}: the H1 must include the wattage — a bare model code '
                    f'carries no commercial intent')
                # The run must be optional: the four wattage-free products
                # (accessories, RGB/RGBW) would otherwise render a stray space.
                self.assertRegex(
                    src,
                    r'\{%\s*if product\.power\s*%\}\s*<span class="section-title-power">',
                    f'{name}: the wattage run must be conditional on product.power')

    def test_no_template_reads_the_raw_category_enum(self):
        """``product.category_t`` is the stored enum (AREA_SITE, …).

        v1.10.19 removed it from ``banner_label``; these two templates had a
        second, less obvious read in the no-banner hero fallback.
        """
        for name in BOTH_TEMPLATES:
            src = self._template(name)
            with self.subTest(template=name):
                self.assertNotIn(
                    '{{ product.category_t }}', src,
                    f'{name}: renders the raw category enum to visitors')

    def test_h1_has_exactly_one_instance_per_branch(self):
        """Two H1s in one render is a heading-structure defect.

        The templates carry an if/else on ``banner_image``; both branches must
        have exactly one H1, and the "not found" branch must keep its own.
        """
        for name in BOTH_TEMPLATES:
            src = self._template(name)
            with self.subTest(template=name):
                count = len(re.findall(r'<h1\b', src))
                self.assertEqual(
                    count, 3,
                    f'{name}: expected 3 <h1> (banner hero, fallback hero, '
                    f'not-found), found {count}')


class ProductFaqDifferentiationTests(SimpleTestCase):
    """P1-C — the FAQ must differ per category, not be one shared list."""

    def test_every_category_has_a_faq_set(self):
        for category in sorted(EXPECTED_CATEGORIES):
            with self.subTest(category=category):
                self.assertIn(
                    category, PRODUCT_FAQ_BY_CATEGORY,
                    'a product category has no FAQ set; the page would fall '
                    'back to the shared core or raise')
        # Reserved values are allowed to be absent — nothing renders them — but
        # if one is adopted it must arrive with a set.
        for category in sorted(RESERVED_CATEGORIES):
            if category in PRODUCT_FAQ_BY_CATEGORY:
                continue
            in_use = [s for s, i in _products().items()
                      if i.get('category') == category]
            with self.subTest(reserved=category):
                self.assertEqual(
                    in_use, [],
                    f'{category} is now used by {in_use} but has no FAQ set')

    def test_every_faq_set_has_exactly_six_entries(self):
        """Six is the pre-existing contract (``tests_qa_bgroup`` counts
        ``<details>``), and six is what the layout and the JSON-LD block were
        designed around. Changing it means changing the contract deliberately.
        """
        for category, faq in sorted(PRODUCT_FAQ_BY_CATEGORY.items()):
            with self.subTest(category=category):
                self.assertEqual(
                    len(faq), 6,
                    f'{category}: expected 6 FAQ entries, got {len(faq)}')

    def test_no_duplicate_question_within_a_set(self):
        for category, faq in sorted(PRODUCT_FAQ_BY_CATEGORY.items()):
            questions = [e['question'] for e in faq]
            with self.subTest(category=category):
                self.assertEqual(
                    len(questions), len(set(questions)),
                    f'{category}: duplicate question in one FAQ set')

    def test_sets_are_not_all_identical(self):
        """The whole point of the batch: distinct sets per category.

        Compared by the frozenset of questions, so a reordering does not count
        as differentiation but a genuine content change does.
        """
        signatures = {
            category: frozenset(e['question'] for e in faq)
            for category, faq in PRODUCT_FAQ_BY_CATEGORY.items()
        }
        self.assertGreater(
            len(set(signatures.values())), 1,
            'all categories share one FAQ set — the split did not happen')
        # And specifically: the sports question must not be everywhere.
        sports = [c for c, sig in signatures.items()
                  if any(SPORTS_ONLY_QUESTION in q for q in sig)]
        self.assertEqual(
            sports, ['SPORTS_LIGHTING'],
            'the broadcast/flicker question belongs to the sports set only, '
            f'found in: {sports}')

    def test_sports_and_accessory_sets_are_clearly_distinct(self):
        """Two categories at opposite ends of the range must not overlap much.

        A weak proxy for "the sets really are different documents", and it
        fails loudly if someone merges them back.
        """
        sports = {e['question'] for e in PRODUCT_FAQ_BY_CATEGORY['SPORTS_LIGHTING']}
        accessory = {e['question'] for e in PRODUCT_FAQ_BY_CATEGORY['ACCESSORY']}
        self.assertTrue(sports and accessory, 'both sets must be non-empty')
        shared = sports & accessory
        self.assertLessEqual(
            len(shared), 2,
            'sports and accessory FAQs overlap too much to count as different '
            f'content (shared: {len(shared)} — {sorted(shared)})')

    def test_selector_falls_back_instead_of_raising(self):
        class Fake:
            def __init__(self, category):
                self.category = category

        for category in sorted(EXPECTED_CATEGORIES):
            with self.subTest(category=category):
                faq = product_faq_for(Fake(category))
                self.assertTrue(faq, 'empty FAQ for a known category')
        # Unknown category degrades to the shared core, never KeyError.
        fallback = product_faq_for(Fake('SOMETHING_NEW'))
        self.assertTrue(fallback)
        self.assertLessEqual(len(fallback), 6)

    def test_selector_is_category_driven_not_slug_driven(self):
        """Two products in one category must get the same set."""
        items = _products()
        by_category = {}
        for item in items.values():
            by_category.setdefault(item.get('category'), []).append(item)
        for category, group in sorted(by_category.items()):
            if len(group) < 2:
                continue
            sets = [
                tuple(e['question'] for e in product_faq_for(_DictProduct(item)))
                for item in group
            ]
            with self.subTest(category=category, count=len(group)):
                self.assertEqual(
                    len(set(sets)), 1,
                    f'{category}: {len(group)} products produced {len(set(sets))} '
                    f'different FAQ sets — the selector is not category-driven')


class ProductDescriptionDepthTests(TestCase):
    """P1-A — descriptions must be substantial and page-specific."""

    @classmethod
    def setUpTestData(cls):
        cls.items = _products()

    def test_build_artifact_matches_the_json(self):
        """``_load_seed()`` reads the BUILD ARTIFACT, not the JSON.

        This is the single most important line in this module. A mutation
        probe that edits ``seed_data.json`` and expects a red guard fails
        here, because ``pages/seed_data.py`` is what production and the local
        server actually load — the JSON is only the input to the next
        ``seed_sync --json`` run. Without this guard the depth and uniqueness
        checks below could pass against a stale artifact while the JSON
        (the committed source of truth) said something else entirely.
        """
        from django.conf import settings
        artifact = settings.BASE_DIR / 'pages' / 'seed_data.py'
        json_path = settings.BASE_DIR / 'seed_data.json'
        if not artifact.exists():
            self.skipTest('build artifact not generated in this checkout')

        with open(json_path, encoding='utf-8') as fh:
            from_json = {p['slug']: p.get('description') or ''
                         for p in json.load(fh).get('products', [])}
        from pages.seed_data import SEED_DATA
        from_artifact = {p['slug']: p.get('description') or ''
                         for p in SEED_DATA.get('products', [])}

        self.assertEqual(
            from_json, from_artifact,
            'pages/seed_data.py is out of sync with seed_data.json — run '
            '`python -m pages.seed_sync --json`. Until then every guard that '
            'reads _load_seed() validates the artifact, not the source of truth.')

    def test_every_description_meets_the_minimum(self):
        offenders = []
        for slug, item in sorted(self.items.items()):
            words = len((item.get('description') or '').split())
            if words < MIN_DESCRIPTION_WORDS:
                offenders.append((slug, words))
        self.assertEqual(
            offenders, [],
            f'descriptions shorter than {MIN_DESCRIPTION_WORDS} words: {offenders}')

    def test_every_description_fits_the_serp_budget(self):
        """A long description is fine for the page but the *meta* description
        is clamped separately; this catches a runaway paragraph."""
        offenders = [
            (slug, len((item.get('description') or '').split()))
            for slug, item in sorted(self.items.items())
            if len((item.get('description') or '').split()) > MAX_DESCRIPTION_WORDS
        ]
        self.assertEqual(
            offenders, [],
            f'descriptions longer than {MAX_DESCRIPTION_WORDS} words: {offenders}')

    def test_descriptions_are_not_interchangeable(self):
        """Six M-series modules once differed by exactly the model code.

        🔴 A word-set signature alone is NOT enough, and the mutation probe
        proved it: giving fl1m and fl4m the *identical* description still
        passed the first version of this check, because fl4m's text mentions
        ``FL1M`` in passing ("more output than the single-module FL1M"), so
        the two word sets differed by a single token. A doorway page is
        near-identical, not bit-identical, so the comparison is Jaccard
        similarity over word bigrams — that catches a copy with a handful of
        words changed, which is exactly how doorway networks are built.
        """
        def words_of(text):
            return [
                w.lower().strip('.,;:()"\'')
                for w in (text or '').split()
            ]

        def bigrams(text):
            words = [w for w in words_of(text) if len(w) > 2]
            return frozenset('%s %s' % (a, b) for a, b in zip(words, words[1:]))

        items = sorted(self.items.items())
        offenders = []
        for index, (slug_a, a) in enumerate(items):
            for slug_b, b in items[index + 1:]:
                text_a = a.get('description') or ''
                text_b = b.get('description') or ''
                if set(words_of(text_a)) == set(words_of(text_b)):
                    offenders.append((slug_a, slug_b, 'identical word set'))
                    continue
                ga, gb = bigrams(text_a), bigrams(text_b)
                if not ga or not gb:
                    continue
                jaccard = len(ga & gb) / float(len(ga | gb))
                if jaccard >= SIMILARITY_LIMIT:
                    offenders.append(
                        (slug_a, slug_b, 'bigram similarity %.2f' % jaccard))
        self.assertEqual(
            offenders, [],
            f'descriptions are near-identical across products (a copy with a '
            f'few words changed is still a doorway page): {offenders}')

    def test_fl_series_descriptions_differ_from_each_other(self):
        """The six modules are the worst case, so they are asserted by name."""
        modules = ['fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m']
        texts = {}
        for slug in modules:
            item = self.items.get(slug)
            self.assertIsNotNone(item, f'{slug} missing from the seed')
            texts[slug] = (item.get('description') or '')
        for i, a in enumerate(modules):
            for b in modules[i + 1:]:
                with self.subTest(pair=(a, b)):
                    self.assertNotEqual(
                        texts[a], texts[b],
                        f'{a} and {b} ship the same description')
        # Each must state its own wattage, which is the per-page fact a buyer
        # selects on. Sourced from the energy table, not hard-coded. The seed
        # writes the wattage both as "480W" (ordering table) and "480 W"
        # (prose), so the check is whitespace-insensitive.
        for slug in modules:
            energy = {e['label']: e['value']
                      for e in (self.items[slug].get('energy_data') or [])
                      if isinstance(e, dict)}
            wattage = re.search(r'(\d+)\s*[wW]', energy.get('System Wattage', '') or '')
            self.assertIsNotNone(
                wattage, f'{slug}: no wattage in its energy table to check')
            prose = re.sub(r'\s+', ' ', texts[slug])
            with self.subTest(slug=slug):
                self.assertRegex(
                    prose, r'\b%s\s*W\b' % wattage.group(1),
                    f'{slug}: description does not mention its own '
                    f'{wattage.group(0)} rating')

    def test_db_and_seed_descriptions_agree(self):
        """Local dev renders the model, production renders the seed mirror."""
        drift = []
        for slug, item in sorted(self.items.items()):
            row = Product.objects.filter(slug=slug).first()
            if row is None:
                continue
            if (row.description or '') != (item.get('description') or ''):
                drift.append(slug)
        self.assertEqual(
            drift, [],
            f'DB and seed descriptions drifted (seed_sync would overwrite one '
            f'side): {drift}')


class ProductH1RenderTests(TestCase):
    """End-to-end: the H1 on a real page must contain the wattage."""

    def test_rendered_h1_includes_the_wattage(self):
        item = _products().get('fl6m')
        self.assertIsNotNone(item)
        wattage = re.search(
            r'(\d+)\s*[wW]',
            next((e['value'] for e in (item.get('energy_data') or [])
                  if isinstance(e, dict) and e.get('label') == 'System Wattage'), ''))
        self.assertIsNotNone(wattage)

        with translation.override('en'):
            url = reverse('product_detail', args=['fl6m'])
            response = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', body, re.S)
        self.assertEqual(len(h1s), 1, f'expected exactly one H1, got {len(h1s)}')
        text = re.sub(r'<[^>]+>', ' ', h1s[0])
        self.assertIn(
            wattage.group(0), text,
            f'the rendered H1 carries no wattage: {text!r}')
        self.assertIn('FL6M', text)
