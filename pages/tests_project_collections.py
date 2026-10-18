"""Guards for the /projects/football/ and /projects/tennis/ sports-landing pages.

``/projects/football/`` and ``/projects/tennis/`` replaced the three
keyword-built landing pages. They exist because pointing a keyword at
``/projects/?venue=OUTDOOR&sport=FOOTBALL_FIELD`` does not work, for three
reasons this module pins down:

1. **The enum splits one sport across two values.** Football is
   ``FOOTBALL_FIELD`` + ``SOCCER_FIELD``; tennis is ``TENNIS_COURTS`` +
   ``TENNIS``. A single-value filter silently drops real projects — including
   the only genuine stadium in the portfolio and the two INDOOR tennis courts.
2. **``request.path`` carries no query string**, so every filtered URL emits
   ``<link rel="canonical" href="…/projects/">``. Google collapses them into
   the unfiltered page and the keyword never owns a distinct indexable URL.
3. **The redirect table cannot express a query string** — its values are bare
   URL names for ``reverse()`` — so a retired landing page could not legally
   301 to a filtered URL anyway.

Every assertion here is behavioural (what the visitor and Google get), not a
check on the implementation, so the collection can be reimplemented freely.
"""
import re

from django.test import TestCase, override_settings
from django.urls import reverse

EN_TITLES = {
    'football': 'Football Stadium Lighting Projects | SolarOne',
    'tennis': 'Tennis Court Lighting Projects | SolarOne',
}

#: The real slugs each collection must list (from seed_data.json).
FOOTBALL_SLUGS = {
    # FOOTBALL_FIELD
    'football-field-led-retrofit',
    'perryville-high-school',
    'mcintosh-county-academy',
    # SOCCER_FIELD — the two a single-value filter would drop
    'yuanshen-sports-centre-stadium',
    'garrison-forest-school',
}
TENNIS_SLUGS = {
    # TENNIS_COURTS (OUTDOOR)
    'morgan-state-university-tennis-courts',
    'north-creek-community-center',
    'national-olympic-sports-center-beijing-tennis-cour',
    # TENNIS (INDOOR) — excluded by venue=OUTDOOR, which is why the collection
    # page cannot just be a filtered /projects/ URL
    'beijing-international-tennis-center',
    'pickle-n-par-club',
}


def _title_of(html):
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
    return match.group(1).strip() if match else ''


def _canonical_of(html):
    match = re.search(r'<link rel="canonical"[^>]*href="([^"]*)"', html)
    return match.group(1) if match else ''


class ProjectCollectionContentTests(TestCase):
    """A collection lists every real project of that sport — and only those."""

    def _get(self, path, lang=''):
        url = '/%s%s' % (lang, path) if lang else path
        response = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200, '%s -> %s'
                         % (url, response.status_code))
        return response.content.decode('utf-8')

    def _slugs_on(self, html):
        return set(re.findall(r'href="/projects/([a-z0-9-]+)/"', html))

    def test_football_collection_merges_both_football_enums(self):
        """FOOTBALL_FIELD alone would hide the only real stadium."""
        html = self._get('/projects/football/')
        listed = self._slugs_on(html)
        for slug in FOOTBALL_SLUGS:
            self.assertIn(slug, listed, '%s missing from /projects/football/' % slug)
        self.assertEqual(listed, FOOTBALL_SLUGS,
                         ' football collection lists the wrong set: %s' % sorted(listed))

    def test_tennis_collection_includes_the_indoor_courts(self):
        """venue=OUTDOOR would drop both INDOOR tennis projects."""
        html = self._get('/projects/tennis/')
        listed = self._slugs_on(html)
        for slug in TENNIS_SLUGS:
            self.assertIn(slug, listed, '%s missing from /projects/tennis/' % slug)
        self.assertEqual(listed, TENNIS_SLUGS,
                         'tennis collection lists the wrong set: %s' % sorted(listed))

    def test_collections_do_not_leak_unrelated_projects(self):
        tennis = self._slugs_on(self._get('/projects/tennis/'))
        football = self._slugs_on(self._get('/projects/football/'))
        self.assertFalse(tennis & football,
                         'a project appears in both collections: %s' % (tennis & football))

    def test_english_titles_carry_the_keyword(self):
        for key, title in EN_TITLES.items():
            html = self._get('/projects/%s/' % key)
            self.assertEqual(_title_of(html), title)


class ProjectCollectionCanonicalTests(TestCase):
    """The whole point of a real path: a self-referencing canonical."""

    def test_canonical_points_at_the_collection_not_the_filtered_page(self):
        for key in ('football', 'tennis'):
            html = self.client.get('/projects/%s/' % key,
                                   HTTP_HOST='localhost').content.decode('utf-8')
            canonical = _canonical_of(html)
            self.assertTrue(
                canonical.endswith('/projects/%s/' % key),
                '%s canonical is %r — a filtered URL would collapse to '
                '/projects/ and the keyword would own no URL' % (key, canonical),
            )

    def test_filtered_projects_url_still_collapses_on_purpose(self):
        """Documents why the query-string target was rejected."""
        html = self.client.get('/projects/?venue=OUTDOOR&sport=FOOTBALL_FIELD',
                               HTTP_HOST='localhost').content.decode('utf-8')
        self.assertTrue(_canonical_of(html).endswith('/projects/'),
                        'filtered URL unexpectedly became self-canonical')


class RetiredLandingPageRedirectTests(TestCase):
    """The three keyword landing pages must 301, not 404 or soft-200."""

    CASES = {
        '/products/sports-lighting/': '/products/',
        '/products/football-stadium-lights/': '/projects/football/',
        '/products/tennis-court-lighting/': '/projects/tennis/',
    }

    def test_each_retired_page_301s_to_its_replacement(self):
        for old, new in self.CASES.items():
            response = self.client.get(old, HTTP_HOST='localhost')
            self.assertEqual(response.status_code, 301, '%s -> %s'
                             % (old, response.status_code))
            self.assertEqual(response['Location'], new,
                             '%s should land on %s' % (old, new))

    def test_redirect_keeps_the_visitor_language(self):
        """reverse() is what preserves /fr/; a hard-coded path would drop it."""
        response = self.client.get('/fr/products/football-stadium-lights/',
                                   HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/fr/projects/football/')

    def test_retired_templates_are_gone(self):
        import os
        from django.conf import settings
        for name in ('sports_lighting.html', 'football_stadium_lights.html',
                     'tennis_court_lighting.html'):
            self.assertFalse(
                os.path.exists(os.path.join(settings.BASE_DIR, 'templates', name)),
                '%s still on disk — deleting the route is not enough' % name,
            )


class ProjectCollectionSitemapTests(TestCase):
    def test_sitemap_lists_collections_and_drops_the_retired_pages(self):
        xml = self.client.get('/sitemap.xml',
                              HTTP_HOST='localhost').content.decode('utf-8')
        for path in ('/projects/football/', '/projects/tennis/'):
            self.assertIn(path, xml)
        for path in ('/products/sports-lighting/',
                     '/products/football-stadium-lights/',
                     '/products/tennis-court-lighting/'):
            self.assertNotIn(path, xml, '%s is still in the sitemap' % path)


class ProjectCollectionDescriptionBudgetTests(TestCase):
    """The collections' copy is a runtime value, so no template scan covers it.

    Django renders `'` as `&#x27;`, which inflates the raw length by 5 chars per
    apostrophe — unescape before measuring or a compliant page reads as over
    budget.
    """

    MAX = 160

    def test_rendered_description_fits_the_serp_budget_in_every_locale(self):
        import html as html_mod
        for lang in ('', 'fr', 'es', 'de', 'ru', 'ar'):
            for key in ('football', 'tennis'):
                url = ('/%s/projects/%s/' % (lang, key)) if lang else ('/projects/%s/' % key)
                response = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200, url)
                match = re.search(
                    r'<meta name="description" content="([^"]*)"',
                    response.content.decode('utf-8'),
                )
                self.assertTrue(match, '%s has no meta description' % url)
                desc = html_mod.unescape(match.group(1))
                self.assertGreater(len(desc), 40, '%s description too short' % url)
                self.assertLessEqual(
                    len(desc), self.MAX,
                    '%s description is %d chars: %r' % (url, len(desc), desc),
                )


class ProjectCollectionLocalizationTests(TestCase):
    """A /fr/ collection page must not serve an English title."""

    LANGS = ('fr', 'es', 'de', 'ru', 'ar')

    def tearDown(self):
        # Requesting /ar/… activates Arabic for the rest of the process, and
        # resolve() under a non-English active language only tries the
        # /<code>/ prefixed resolver — which breaks unrelated tests that resolve
        # unprefixed paths. Restore the default language after every case.
        from django.utils import translation
        translation.activate('en')

    def test_no_locale_falls_back_to_the_english_title(self):
        for lang in self.LANGS:
            for key, en_title in EN_TITLES.items():
                url = '/%s/projects/%s/' % (lang, key)
                response = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200, url)
                title = _title_of(response.content.decode('utf-8'))
                self.assertNotEqual(
                    title, en_title,
                    '%s fell back to English — add the entry to _SIDEBAR_I18N'
                    % url,
                )
                self.assertIn('SolarOne', title, '%s lost the brand suffix' % url)

    def test_every_locale_renders_both_collections(self):
        for lang in self.LANGS:
            for key in ('football', 'tennis'):
                url = '/%s/projects/%s/' % (lang, key)
                self.assertEqual(
                    self.client.get(url, HTTP_HOST='localhost').status_code, 200,
                    url,
                )


class SportsLandingUnificationTests(TestCase):
    """Q1: football/tennis share the stadium sports-landing template.

    The old case-grid ``projects_collection.html`` pages have been deleted;
    these pages render the unified product + project layout driven by
    ``SPORT_LANDING_PAGES``. Every assertion here pins a product/content
    decision so a regression is a deliberate act, not a silent drift.
    """

    def _get(self, path, lang=''):
        url = ('/%s%s' % (lang, path)) if lang else path
        response = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200, '%s -> %s'
                         % (url, response.status_code))
        return response.content.decode('utf-8')

    def test_football_and_tennis_render_the_unified_template(self):
        """Both keyword pages reuse stadium_lighting.html (the shared layout)."""
        for key in ('football', 'tennis'):
            html = self._get('/projects/%s/' % key)
            self.assertIn(
                'stadium-products-grid', html,
                '%s is not on the unified sports-landing template' % key)
            self.assertIn(
                'stadium-intro', html,
                '%s is missing the stadium-intro structural hook' % key)

    def test_football_featured_products_are_m_series_and_vsp(self):
        from pages.views.views_projects import SPORT_LANDING_PAGES
        self.assertEqual(
            SPORT_LANDING_PAGES['football']['featured_slugs'],
            ('m-series', 'vsp-xxxxw-9m-yp'),
            'football featured roster changed without a product decision')
        html = self._get('/projects/football/')
        for slug in ('m-series', 'vsp-xxxxw-9m-yp'):
            self.assertIn(
                reverse('product_detail', args=[slug]), html,
                '%s must be featured on the football page' % slug)

    def test_tennis_featured_products_are_rt410_series_and_m_series(self):
        from pages.views.views_projects import SPORT_LANDING_PAGES
        self.assertEqual(
            SPORT_LANDING_PAGES['tennis']['featured_slugs'],
            ('rt410-series', 'm-series'),
            'tennis featured roster changed without a product decision')
        html = self._get('/projects/tennis/')
        for slug in ('rt410-series', 'm-series'):
            self.assertIn(
                reverse('product_detail', args=[slug]), html,
                '%s must be featured on the tennis page' % slug)

    def test_landing_pages_carry_sport_specific_h1_and_faq(self):
        checks = {
            'football': (
                'Football Field Lighting',
                'How many floodlights does a football pitch need?',
            ),
            'tennis': (
                'Tennis Court Lighting',
                'What lux level do tennis courts need?',
            ),
        }
        for key, (h1, faq_q) in checks.items():
            html = self._get('/projects/%s/' % key)
            self.assertIn(h1, html, '%s H1 is not sport-specific' % key)
            self.assertIn(faq_q, html, '%s FAQ is not sport-specific' % key)

    def test_selection_table_is_sport_specific(self):
        football = self._get('/projects/football/')
        self.assertIn('5-a-side / community pitch', football,
                      'football selection table lost its sport row')
        tennis = self._get('/projects/tennis/')
        self.assertIn('Padel / pickleball court', tennis,
                      'tennis selection table lost its sport row')

    def test_faq_jsonld_present_on_landing_pages(self):
        for key in ('football', 'tennis'):
            html = self._get('/projects/%s/' % key)
            self.assertIn('FAQPage', html,
                          '%s is missing the FAQPage JSON-LD' % key)


class ProjectSocialVideoSlotTests(TestCase):
    """The reserved social-video slot on the project detail page (2026-10-18).

    The admin's Social Video field feeds a link entry on the right of the
    "Related Lighting Solutions" block. Empty URL renders no slot at all —
    the same "no pick means no section" philosophy as related_products.
    """

    def setUp(self):
        # Creating a Project fires models.sync_project_on_save, which writes
        # under BASE_DIR/static/images/projects/<slug>/. Iron law 23 pattern:
        # isolate the case in a tmp BASE_DIR, and flush the process-global
        # enrichment caches afterwards (the guard-product leak of 2026-10-18).
        import shutil
        import tempfile

        from pages.models import Project
        self._tmp = tempfile.mkdtemp(prefix='svslot_')
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.enterContext(override_settings(BASE_DIR=self._tmp))
        self.project = Project.objects.create(
            slug='sv-slot-project', title='SV Slot Project', location='Beijing',
            venue_type='OUTDOOR', sport_type='FOOTBALL_FIELD',
            description='Guard fixture for the social video slot.')

    def tearDown(self):
        from pages.views.enrich import invalidate_enrichment_cache
        invalidate_enrichment_cache()
        super().tearDown()

    def _get_detail(self):
        resp = self.client.get('/projects/sv-slot-project/')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode('utf-8')

    def test_empty_url_renders_no_slot(self):
        self.assertEqual(self.project.social_video_url, '')
        html = self._get_detail()
        # Assert on the anchor structure, not the bare class substring: the
        # page-level <style> block always carries the .related-solutions-video
        # rules (iron law 32 — condition/structure, not identifier substring).
        self.assertNotIn('<a class="related-solutions-video"', html,
                         'an empty social_video_url must not render a slot')

    def test_url_renders_the_slot_with_safe_attrs(self):
        url = 'https://www.youtube.com/watch?v=svslot'
        from pages.models import Project
        Project.objects.filter(pk=self.project.pk).update(social_video_url=url)
        html = self._get_detail()
        self.assertIn('related-solutions-video', html)
        m = re.search(r'<a class="related-solutions-video" href="([^"]+)"'
                      r' target="_blank" rel="noopener noreferrer">', html)
        self.assertIsNotNone(m, 'slot anchor lost its safe attrs')
        self.assertEqual(m.group(1), url)
        self.assertIn('Watch the Video', html)

    def test_seed_path_exposes_the_field(self):
        """Iron law 1: the seed path (_DictProject) must carry the field."""
        from pages.views.utils import _DictProject
        dp = _DictProject({'slug': 'x', 'social_video_url': 'https://v.example/'})
        self.assertEqual(dp.social_video_url, 'https://v.example/')
        # missing key must degrade to empty, not AttributeError
        dp2 = _DictProject({'slug': 'y'})
        self.assertEqual(dp2.social_video_url, '')

    def test_export_carries_the_field(self):
        from pages.seed_sync import _project_to_dict
        from pages.models import Project
        Project.objects.filter(pk=self.project.pk).update(
            social_video_url='https://www.tiktok.com/@solarone')
        out = _project_to_dict(Project.objects.get(pk=self.project.pk))
        self.assertEqual(out['social_video_url'],
                         'https://www.tiktok.com/@solarone')

    def test_every_seed_project_carries_the_key(self):
        """The key exists on all 22 seed rows so a future sync is a no-op."""
        from pages.views.utils import _load_seed
        for p in _load_seed()['projects']:
            with self.subTest(slug=p.get('slug')):
                self.assertIn('social_video_url', p)
                self.assertIsInstance(p['social_video_url'], str)
