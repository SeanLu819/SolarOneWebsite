"""Guards for the v1.10.0 project collection pages.

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

from django.test import TestCase

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
