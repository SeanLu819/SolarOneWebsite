"""P3 image-SEO guards — alt text vocabulary and collection-page image sitemap.

Two defects from the 2026-10-06 long-tail audit, both invisible to a syntax
check because a missing or wrong ``alt`` is perfectly valid HTML.

**P3-A — 36 gallery images carried a stale machine-written alt.** ``_gallery_alt``
had been improved to fold the product's category into the alt text, but the
improvement was invisible: ``ProductImage.alt_text`` in the database still held
the *old* generated string (``"FL6M — view 1"``), and the render path reads
``img.alt_text or _gallery_alt(...)`` — the stored value wins. The formula was
improved and nothing changed on any page. Those rows are now cleared, and a
guard keeps them clear.

**P3-C — the alt vocabulary was a navigation label, not a search phrase.**
The qualifier folded into every gallery alt was ``category_display``, i.e. the
sidebar entry ("Area and Site", "Flood Lighting"). Nobody searches for that;
they search "LED flood light". The qualifier is now the phrase the ``<title>``
bids on, so one page describes itself in one vocabulary.

**P3-B — 10 of 59 sitemap URLs carried no images at all**, including the home
page, the product index and both project collections — every page a first-time
visitor lands on.

Expectation sourcing (iron law 4b): the thresholds and word lists below are
**product decisions written out literally**. Nothing is read from the constant
it validates; the one exception is explicitly marked and cross-checked against a
literal in the same test.
"""
import unittest

import os
import re

from django.conf import settings
from django.test import TestCase, override_settings
from django.test import Client
from django.urls import reverse
from django.utils import translation

from pages.utils import CATEGORY_KEYWORD, SLUG_KEYWORD_OVERRIDE, _seo_keyword
from pages.views.enrich import _enrich_product, _enrich_project
from pages.views.utils import _DictProduct, _DictProject, _load_seed
from pages.views.views_other import (
    _COLLECTION_PAGE_IMAGES,
    _COLLECTION_PROJECT_SPORTS,
    _collection_dynamic_images,
    _collection_page_images,
)

LANGS = ('en', 'fr', 'es', 'de', 'ru', 'ar')

#: Product decisions, written literally:
#:
#: * a gallery alt shorter than this cannot name a product *and* a category;
#:   the shortest real one after P3-C is well above it.
#: * the number of stale machine-written alts that must not come back.
MIN_GALLERY_ALT_LEN = 25
FORBIDDEN_ALT_SUFFIX = '— view '

#: Every category enum. An enum in an ``alt`` attribute is the same defect the
#: v1.10.20 title batch fixed, one attribute over.
CATEGORY_ENUMS = (
    'AREA_SITE', 'SPORTS_LIGHTING', 'FLOODLIGHT', 'HIGHBAY_LOWBAY',
    'ROADWAY', 'ACCESSORY', 'MODULAR', 'OTHER',
)

#: The collection pages that must carry images. Literal, not derived from the
#: sitemap: a guard that asked the sitemap which pages it had images for would
#: be satisfied by an empty sitemap.
COLLECTION_PAGES_WITH_IMAGES = (
    'home', 'products', 'projects', 'projects_football', 'projects_tennis',
    'news', 'about', 'contact',
)

#: Legal text pages. Listed as "must have none" so that adding an entry for
#: them has to be a deliberate act rather than a side effect of a wildcard.
COLLECTION_PAGES_WITHOUT_IMAGES = ('privacy', 'terms')

LOC_RE = re.compile(r'<loc>(.*?)</loc>')
IMAGE_RE = re.compile(r'<image:image>(.*?)</image:image>', re.S)
IMAGE_LOC_RE = re.compile(r'<image:loc>(.*?)</image:loc>')


def _sitemap():
    """Fetch and parse ``/sitemap.xml`` through the real view stack."""
    client = Client()
    response = client.get('/sitemap.xml', HTTP_HOST='localhost')
    assert response.status_code == 200, response.status_code
    body = response.content.decode('utf-8')
    pages = {}
    for block in re.findall(r'<url>(.*?)</url>', body, re.S):
        loc = LOC_RE.search(block).group(1)
        pages[loc] = IMAGE_RE.findall(block)
    return pages


class StaleGalleryAltTests(TestCase):
    """P3-A — the improved formula must actually reach the page."""

    @classmethod
    def setUpTestData(cls):
        cls.items = {p['slug']: p for p in _load_seed().get('products', [])}

    @classmethod
    def setUpClass(cls):
        """Read the *real* ``db.sqlite3``, read-only.

        🔴 A ``TestCase`` gets its own empty database, so ``ProductImage.objects``
        returns 0 rows and every assertion below is vacuous. The first version of
        this class did exactly that and the mutation probe caught it: writing a
        stale alt back into ``db.sqlite3`` left the suite green. Same pattern as
        ``tests_cert_images.CertDatabasePathTests``.
        """
        super().setUpClass()
        import sqlite3
        db = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if not os.path.exists(db):
            raise unittest.SkipTest(
                'db.sqlite3 missing (stateless deploy) — this guard needs a '
                'local database to have anything to check')
        cls._con = sqlite3.connect(
            'file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
        # Every row, not only the non-empty ones: the fix emptied 36 of them and
        # "zero non-empty alts" is the desired end state, so filtering here
        # would make the anti-vacuity check below assert the opposite of what
        # it is meant to prove.
        cls.db_image_rows = cls._con.execute(
            'select p.slug, i.image, i.alt_text '
            'from pages_productimage i '
            'join pages_product p on p.id = i.product_id'
        ).fetchall()
        cls.db_alts = [r for r in cls.db_image_rows if (r[2] or '').strip()]

    @classmethod
    def tearDownClass(cls):
        try:
            cls._con.close()
        finally:
            super().tearDownClass()

    def test_the_real_database_actually_has_image_rows(self):
        """Anti-vacuity: prove the subject exists before asserting on it.

        The subject is the *image rows*, not the non-empty alts — after the
        P3-A cleanup the correct state is that no product image carries a
        stored alt at all, so an anti-vacuity check on the alt column would
        fail precisely when the fix is in place.
        """
        self.assertGreater(
            len(self.db_image_rows), 0,
            'db.sqlite3 has no product image rows — this guard has no subject')
        self.assertEqual(
            self.db_alts, [],
            'every product image alt must be empty so the formula renders; '
            'a non-empty value here shadows it (P3-A): %r' % (self.db_alts[:5],))

    def test_no_stored_alt_matches_the_old_generated_shape(self):
        """A stored ``"<name> — view N"`` shadows the formula forever.

        ``_enrich_product`` reads ``img.alt_text or _gallery_alt(...)``, so a
        non-empty stored value wins outright. Re-introducing one would silently
        revert every gallery alt on the site, which is exactly what happened
        between the formula's introduction and v1.10.22.
        """
        offenders = [
            (slug, image, alt)
            for slug, image, alt in self.db_alts
            if FORBIDDEN_ALT_SUFFIX in alt
        ]
        self.assertEqual(
            offenders, [],
            'stored gallery alts shadow _gallery_alt (P3-A regression): %r'
            % (offenders[:5],),
        )

    def test_a_stored_alt_would_actually_win_over_the_formula(self):
        """The shadowing is a fact about the code, not an assumption.

        If ``img.alt_text`` were ever given second place in that ``or``, the
        guard above would still pass while the site went back to the old copy.
        """
        import inspect
        from pages.views import enrich

        source = inspect.getsource(enrich._enrich_product)
        self.assertIn(
            'img.alt_text or _gallery_alt(',
            source,
            'the stored alt must keep priority over the generated one — '
            'otherwise P3-A is not a shadowing bug at all and this class '
            'guards the wrong mechanism')

    def test_generated_alts_carry_the_search_phrase(self):
        """Not just "longer" — must contain the phrase the title bids on."""
        offenders = []
        for slug, item in sorted(self.items.items()):
            product = _DictProduct(item)
            _enrich_product(product, 'en')
            expected = _seo_keyword(product, 'en')
            if not expected:
                # No keyword for this category is a separate concern; the
                # category-coverage test in tests_seo_p2 pins that.
                continue
            for entry in product.gallery:
                alt = entry.get('alt', '')
                if expected not in alt:
                    offenders.append((slug, expected, alt))
        self.assertEqual(
            offenders, [],
            'gallery alt missing the page keyword (P3-C regression): %r'
            % (offenders[:5],),
        )

    def test_no_generated_alt_contains_a_category_enum(self):
        offenders = []
        for slug, item in sorted(self.items.items()):
            product = _DictProduct(item)
            _enrich_product(product, 'en')
            for entry in product.gallery:
                alt = entry.get('alt', '')
                hit = [e for e in CATEGORY_ENUMS if e in alt]
                if hit:
                    offenders.append((slug, hit, alt))
        self.assertEqual(
            offenders, [],
            'a category enum reached an alt attribute: %r' % (offenders[:5],),
        )


class ProductGalleryAltTests(TestCase):
    """P3-C — product gallery alt, in every locale."""

    @classmethod
    def setUpTestData(cls):
        cls.items = {p['slug']: p for p in _load_seed().get('products', [])}

    def test_every_gallery_alt_is_long_enough_in_every_locale(self):
        for lang in LANGS:
            offenders = []
            for slug, item in sorted(self.items.items()):
                product = _DictProduct(item)
                with translation.override(lang):
                    _enrich_product(product, lang)
                for entry in product.gallery:
                    alt = entry.get('alt', '')
                    if len(alt) < MIN_GALLERY_ALT_LEN:
                        offenders.append((slug, lang, alt))
            with self.subTest(lang=lang):
                self.assertEqual(
                    offenders, [],
                    'gallery alt shorter than %d chars (P3-C): %r'
                    % (MIN_GALLERY_ALT_LEN, offenders[:5]))

    def test_alt_is_unique_within_a_product(self):
        """Two identical alts on one page is an accessibility defect."""
        for slug, item in sorted(self.items.items()):
            product = _DictProduct(item)
            _enrich_product(product, 'en')
            alts = [e.get('alt', '') for e in product.gallery]
            with self.subTest(slug=slug):
                self.assertEqual(
                    len(alts), len(set(alts)),
                    'duplicate gallery alt within one product: %r' % (alts,))

    def test_project_gallery_alt_names_the_venue_type(self):
        """A project photo's alt must say what kind of venue it shows."""
        from pages.utils import project_category_keyword

        offenders = []
        for item in _load_seed().get('projects', []):
            project = _DictProject(item)
            _enrich_project(project, 'en')
            expected = project_category_keyword(item.get('sport_type', ''), 'en')
            for entry in project.gallery:
                alt = entry.get('alt', '')
                if expected and expected not in alt:
                    offenders.append((project.slug, expected, alt))
        self.assertEqual(
            offenders, [],
            'project gallery alt missing the venue type: %r' % (offenders[:5],))


class DbAndSeedAltParityTests(TestCase):
    """Iron law 1 — the DB path and the seed path must render one alt.

    The audit found them diverged: the DB rows carried the old stored alt while
    the seed path ran the current formula, so local previews and production
    showed different alt text for the same image.

    🔴 Same trap as ``StaleGalleryAltParityTests``: the ORM runs against the
    empty test database, so every ``.get()`` below raised ``DoesNotExist`` and
    the loop body never executed. The DB side is therefore read straight from
    ``db.sqlite3`` with a read-only connection, and the *stored* alt is what
    gets compared — not a re-derived one, which would compare the formula with
    itself and prove nothing.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import sqlite3
        db = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if not os.path.exists(db):
            raise unittest.SkipTest('db.sqlite3 missing (stateless deploy)')
        cls._con = sqlite3.connect(
            'file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
        cls.product_alts = cls._con.execute(
            'select p.slug, i.image, i.alt_text '
            'from pages_productimage i '
            'join pages_product p on p.id = i.product_id'
        ).fetchall()
        cls.project_alts = cls._con.execute(
            'select p.slug, i.image, i.alt_text '
            'from pages_projectimage i '
            'join pages_project p on p.id = i.project_id'
        ).fetchall()

    @classmethod
    def tearDownClass(cls):
        try:
            cls._con.close()
        finally:
            super().tearDownClass()

    def test_the_real_database_has_image_rows_to_compare(self):
        self.assertGreater(
            len(self.product_alts), 0,
            'no product image rows in db.sqlite3 — parity guard has no subject')
        self.assertGreater(
            len(self.project_alts), 0,
            'no project image rows in db.sqlite3 — parity guard has no subject')

    def test_stored_product_alts_match_the_seed_rendered_alts(self):
        """A stored alt replaces the generated one, so it must equal it."""
        mismatches = []
        by_slug = {}
        for slug, image, alt in self.product_alts:
            by_slug.setdefault(slug, {})[image] = alt or ''
        for item in _load_seed().get('products', []):
            slug = item.get('slug')
            stored = by_slug.get(slug)
            if not stored:
                continue
            seed_obj = _DictProduct(item)
            _enrich_product(seed_obj, 'en')
            for entry in seed_obj.gallery:
                image = entry.get('src', '').rsplit('/', 1)[-1]
                # Compare on the file name: the DB column and the seed path can
                # legitimately differ on the directory prefix (seed_sync rewrites
                # ``products/gallery/x.webp`` to ``images/products/<slug>/x.webp``)
                # but never on the file the visitor is shown.
                if image in stored and stored[image] != entry.get('alt', ''):
                    mismatches.append(
                        (slug, image, stored[image], entry.get('alt', '')))
        self.assertEqual(
            mismatches, [],
            'DB and seed render different gallery alts (iron law 1): %r'
            % (mismatches[:5],),
        )

    def test_stored_project_alts_match_the_seed_rendered_alts(self):
        mismatches = []
        by_slug = {}
        for slug, image, alt in self.project_alts:
            by_slug.setdefault(slug, {})[image] = alt or ''
        for item in _load_seed().get('projects', []):
            slug = item.get('slug')
            stored = by_slug.get(slug)
            if not stored:
                continue
            seed_obj = _DictProject(item)
            _enrich_project(seed_obj, 'en')
            for entry in seed_obj.gallery:
                image = entry.get('src', '').rsplit('/', 1)[-1]
                if image in stored and stored[image] != entry.get('alt', ''):
                    mismatches.append(
                        (slug, image, stored[image], entry.get('alt', '')))
        self.assertEqual(
            mismatches, [],
            'DB and seed render different project gallery alts: %r'
            % (mismatches[:5],),
        )


class RenderedAltTests(TestCase):
    """P3-C — assert the rendered attribute value, not the template source.

    A missing ``alt`` is syntactically valid HTML, so a template-source check
    cannot see it. These go through the view.
    """

    def _get(self, path):
        return Client().get(path, HTTP_HOST='localhost').content.decode('utf-8')

    #: The rendered certification badge. Matched on the *resolved file*, not
    #: on the template variable name — ``cert_image_url`` is a context key and
    #: never appears in the HTML, so a regex written against it silently finds
    #: nothing. That is how the first version of the next two tests "passed"
    #: while asserting on an empty list.
    CERT_IMG_RE = re.compile(
        r'<img[^>]*certifications-ul-dlc-gs-ce-ip66\.webp"[^>]*alt="([^"]*)"')

    @staticmethod
    def _img_tags(body):
        """Real ``<img>`` tags only.

        ``<img[^>]*>`` also matches the bare ``<img>`` literals inside the
        inline JavaScript (the theme toggle creates one), so the scan is
        anchored to a tag that actually carries a ``src``.
        """
        return [t for t in re.findall(r'<img[^>]*>', body) if ' src=' in t]

    def test_product_page_images_all_carry_an_alt(self):
        for path in ('/products/fl6m/', '/products/m-series/',
                     '/products/rt410-series/'):
            body = self._get(path)
            tags = self._img_tags(body)
            with self.subTest(path=path):
                self.assertTrue(tags, 'no images rendered at all')
                missing = [t for t in tags if 'alt=' not in t]
                self.assertEqual(missing, [], 'img without alt: %r' % missing)

    def test_cert_alt_names_the_product(self):
        """Was one trans string on all 24 pages; now it must differ per page."""
        client = Client()
        alts = {}
        for slug in ('fl6m', 'rt410-series', 'rt600sl-t'):
            body = client.get('/products/%s/' % slug,
                              HTTP_HOST='localhost').content.decode('utf-8')
            found = self.CERT_IMG_RE.findall(body)
            alts[slug] = found[0] if found else ''
        self.assertTrue(all(alts.values()),
                        'cert image rendered without an alt: %r' % alts)
        self.assertEqual(
            len(set(alts.values())), len(alts),
            'cert alt is identical across products again: %r' % alts)
        # Each alt must name its own product, not merely "a product".
        for slug, alt in alts.items():
            token = slug.split('-')[0].upper()
            with self.subTest(slug=slug):
                self.assertIn(token, alt.upper(),
                              'cert alt does not name %s: %r' % (slug, alt))

    def test_cert_alt_is_translated_in_every_locale(self):
        """The cert alt is the one image alt that goes through gettext."""
        client = Client()
        seen = {}
        for lang in LANGS:
            prefix = '' if lang == 'en' else '/%s' % lang
            body = client.get('%s/products/fl6m/' % prefix,
                              HTTP_HOST='localhost').content.decode('utf-8')
            found = self.CERT_IMG_RE.findall(body)
            self.assertTrue(found, '%s: no cert alt rendered' % lang)
            seen[lang] = found[0]
        # The certification names are proper nouns and stay; the sentence
        # around them must not be English on a translated page.
        for lang in ('fr', 'de', 'ru', 'ar', 'es'):
            with self.subTest(lang=lang):
                self.assertNotEqual(
                    seen[lang], seen['en'],
                    'cert alt is English on the %s page' % lang)
                self.assertIn('UL', seen[lang])


class CollectionPageImageSitemapTests(TestCase):
    """P3-B — the ten collection pages."""

    @classmethod
    def setUpTestData(cls):
        import pages.views.utils as _vu
        from pages.views import enrich as _enrich
        # 🔴 Sitemap is a build artifact that reads the seed; production runs
        # IS_VERCEL=True and never the DB. Under IS_VERCEL=False the loaders
        # fall back to the (empty) test DB, and a prior test class that creates
        # Project fixtures can poison the process-global
        # ``_enriched_projects_cache[('en','','')]`` key with cover-less rows,
        # so ``get_projects('en')`` returns [] and /projects/ ships no images.
        # Force the production path and clear the poisoned caches so the guard
        # reflects what Vercel actually serves (iron law: test the real branch).
        _vu._seed_cache = None
        _enrich._enriched_projects_cache.clear()
        _enrich._enriched_products_cache.clear()
        with override_settings(IS_VERCEL=True):
            cls.pages = _sitemap()
        cls.origin = settings.CANONICAL_ORIGIN

    def _loc(self, name):
        path = reverse(name)
        return self.origin + path

    def test_every_collection_page_with_images_has_images(self):
        missing = []
        for name in COLLECTION_PAGES_WITH_IMAGES:
            with self.subTest(page=name):
                block = self.pages.get(self._loc(name))
                self.assertIsNotNone(block, '%s absent from the sitemap' % name)
                if not block:
                    missing.append(name)
        self.assertEqual(
            missing, [],
            'collection pages with no <image:image> (P3-B regression): %r'
            % (missing,),
        )

    def test_legal_pages_carry_no_images(self):
        """Listed so adding one has to be deliberate, not a wildcard side effect."""
        for name in COLLECTION_PAGES_WITHOUT_IMAGES:
            with self.subTest(page=name):
                block = self.pages.get(self._loc(name))
                self.assertIsNotNone(block, '%s absent from the sitemap' % name)
                self.assertEqual(
                    block, [],
                    '%s is legal text; an image entry there is invented' % name)

    def test_every_listed_image_url_exists_on_disk(self):
        """A sitemap image that 404s is worse than no entry."""
        from pages.views.utils import _first_static

        offenders = []
        for loc, blocks in sorted(self.pages.items()):
            for block in blocks:
                url = IMAGE_LOC_RE.search(block)
                if not url:
                    offenders.append((loc, 'no <image:loc>'))
                    continue
                full = url.group(1)
                if not full.startswith(self.origin + '/static/'):
                    continue  # /media/ URLs are not covered by the manifest
                rel = full[len(self.origin + '/static/'):]
                if not _first_static([rel]):
                    offenders.append((loc, rel))
        self.assertEqual(
            offenders, [],
            'sitemap lists an image that is not in static/ (online 404): %r'
            % (offenders[:5],),
        )

    def test_collection_static_table_paths_exist(self):
        """Fail at the table, not at the rendered sitemap."""
        from pages.views.utils import _first_static

        missing = [
            (page, rel)
            for page, items in sorted(_COLLECTION_PAGE_IMAGES.items())
            for rel, _t, _c in items
            if not _first_static([rel])
        ]
        self.assertEqual(
            missing, [],
            '_COLLECTION_PAGE_IMAGES points at a file that is not on disk: %r'
            % (missing,),
        )

    def test_collection_table_has_a_title_for_every_image(self):
        """``<image:title>`` is the only descriptive text these files have."""
        offenders = [
            (page, rel)
            for page, items in sorted(_COLLECTION_PAGE_IMAGES.items())
            for rel, title, _c in items
            if not (title or '').strip()
        ]
        self.assertEqual(
            offenders, [],
            'collection image without a title: %r' % (offenders,))

    def test_project_collection_images_match_the_sport_filter(self):
        """The set must come from the same filter the page renders.

        🔴 The expected sport membership is written out **literally** here.
        The first version iterated ``_COLLECTION_PROJECT_SPORTS`` and called
        that "the product decision" — which is iron law 4b exactly: pointing
        the tennis collection at football's sports makes both the
        implementation and the expectation move together, so the guard stayed
        green (the mutation probe proved it). An expectation has to be a
        statement about the world that the implementation cannot edit.
        """
        from pages.views.data_loaders import get_projects

        expected_sports = {
            'projects_football': ('FOOTBALL_FIELD', 'SOCCER_FIELD'),
            'projects_tennis': ('TENNIS_COURTS', 'TENNIS'),
        }
        # The implementation must not have grown or lost a collection.
        self.assertEqual(
            set(_COLLECTION_PROJECT_SPORTS), set(expected_sports),
            'the set of project collections changed; update this test only if '
            'the change is intended')

        for name, sports in sorted(expected_sports.items()):
            expected = [p.image_url for p in
                        (get_projects('en', '', list(sports)) or [])
                        if getattr(p, 'image_url', '')]
            found = _collection_dynamic_images(name)
            with self.subTest(page=name):
                self.assertTrue(
                    expected,
                    'no %s project has a cover image — the guard lost its '
                    'subject' % name)
                self.assertEqual(
                    [u for u, _t, _c in found],
                    expected[:len(found)],
                    '%s images do not match the project list it renders '
                    '(expected sport types %r)' % (name, sports))

    def test_the_two_collections_do_not_overlap(self):
        """A football project must never appear in the tennis sitemap entry.

        The strongest available check on the mapping, and it needs no literal:
        the two sport sets are disjoint in the seed, so any overlap means one
        collection is reading the other's filter.
        """
        football = {u for u, _t, _c in _collection_dynamic_images(
            'projects_football')}
        tennis = {u for u, _t, _c in _collection_dynamic_images(
            'projects_tennis')}
        self.assertTrue(football, 'the football collection has no images')
        self.assertTrue(tennis, 'the tennis collection has no images')
        self.assertEqual(
            football & tennis, set(),
            'a project is listed in both sport collections: %r'
            % sorted(football & tennis))

    def test_no_duplicate_image_within_one_collection_entry(self):
        offenders = []
        for loc, blocks in sorted(self.pages.items()):
            locs = [IMAGE_LOC_RE.search(b).group(1) for b in blocks
                    if IMAGE_LOC_RE.search(b)]
            if len(locs) != len(set(locs)):
                offenders.append(loc)
        self.assertEqual(
            offenders, [],
            'duplicate <image:loc> inside one <url>: %r' % (offenders[:5],))

    def test_collection_cap_is_a_product_decision(self):
        """Cross-check: the cap must not exceed what the sitemap documents."""
        from pages.views.views_other import _COLLECTION_IMAGE_CAP

        # A collection listing 50 projects must not ship 50 sitemap images;
        # the leaf pages carry those. Pinned so raising the cap is deliberate.
        self.assertEqual(_COLLECTION_IMAGE_CAP, 10)
        for name in ('projects', 'news'):
            with self.subTest(page=name):
                self.assertLessEqual(
                    len(_collection_dynamic_images(name)), _COLLECTION_IMAGE_CAP)

    def test_keyword_table_still_backs_the_alt_qualifier(self):
        """P3-C's qualifier is P2's keyword table — the two must not drift.

        If someone replaces the sidebar wording with a proper SEO phrase in
        ``CATEGORY_KEYWORD``, the alt text changes too. That is intended, so
        this test only asserts the two are wired to the same source rather than
        pinning the wording (which a native reviewer may legitimately change).
        """
        for category in CATEGORY_KEYWORD:
            if category not in {p.get('category') for p in _load_seed()['products']}:
                continue
            with self.subTest(category=category):
                product = _DictProduct({
                    'slug': 'probe', 'name': 'Probe',
                    'category': category, 'gallery': [],
                })
                self.assertEqual(_seo_keyword(product, 'en'),
                                 CATEGORY_KEYWORD[category])

    def test_slug_override_reaches_the_alt_text(self):
        """The override is a per-slug search phrase; alt must use it too."""
        self.assertTrue(SLUG_KEYWORD_OVERRIDE,
                        'the override table went empty again')
        item = next(p for p in _load_seed()['products']
                    if p['slug'] in SLUG_KEYWORD_OVERRIDE
                    and (p.get('gallery') or []))
        product = _DictProduct(item)
        _enrich_product(product, 'en')
        expected = SLUG_KEYWORD_OVERRIDE[item['slug']]
        with self.subTest(slug=item['slug']):
            self.assertIn(expected, product.gallery[0]['alt'])