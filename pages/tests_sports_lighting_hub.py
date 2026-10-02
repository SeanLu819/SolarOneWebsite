"""SEMrush keyword landing pages — hub (Tier-1) + football/tennis (Tier-2).

Shared contract (``SportsLandingPageContract``): each landing page must render,
carry its target keyword verbatim in <title> (≤60 chars for SERP display),
cover its keyword family in body copy, list the matching products, emit a valid
ItemList JSON-LD, and be present in the sitemap. One keyword family, one page —
the tests pin that mapping against the docs/keyword-inventory.csv decisions.
"""
import json
import re

from django.test import TestCase

from pages.views import invalidate_enrichment_cache


class SportsLandingPageContract:
    """Shared contract for the sports keyword landing pages."""

    path = ''
    #: Verbatim head keyword that MUST appear in <title>.
    title_keyword = ''
    #: Keyword family that MUST appear in rendered body copy (lowercased match).
    body_keywords = ()
    #: Product slugs that MUST appear in the grid.
    expected_slugs = ('vsp-xxxxw-9m-yp', 'rt590fl-s')
    #: Minimum ItemList elements (all sports-relevant products).
    min_items = 6

    def setUp(self):
        # The product loader relies on module-global caches that persist across
        # the test process. Reset them so this page always renders against the
        # real seed, mirroring a clean production startup. (The root-cause for
        # the empty-DB poisoning was fixed in data_loaders: the DB loader no
        # longer caches an empty list that would block the seed-JSON fallback.)
        invalidate_enrichment_cache()

    def _get(self):
        return self.client.get(self.path, HTTP_HOST='localhost')

    def _title(self, content):
        match = re.search(r'<title>(.*?)</title>', content, re.S)
        self.assertIsNotNone(match, f'{self.path}: no <title> found')
        return match.group(1)

    def test_returns_200(self):
        self.assertEqual(self._get().status_code, 200)

    def test_title_contains_target_keyword(self):
        # The primary head keyword must be verbatim in <title>.
        title = self._title(self._get().content.decode())
        self.assertIn(self.title_keyword, title,
                      f'{self.path}: <title> missing target keyword')

    def test_title_fits_serp_display(self):
        # Google truncates around 60 chars — a longer title wastes the tail.
        title = self._title(self._get().content.decode())
        self.assertLessEqual(len(title), 60, f'{self.path}: <title> too long')

    def test_body_covers_keyword_family(self):
        content = self._get().content.decode().lower()
        for kw in self.body_keywords:
            self.assertIn(kw, content, f'{self.path} body missing keyword: {kw!r}')

    def test_lists_products(self):
        content = self._get().content.decode()
        for slug in self.expected_slugs:
            self.assertIn(slug, content, f'{self.path} grid missing {slug}')

    def test_jsonld_itemlist_is_valid(self):
        content = self._get().content.decode()
        blocks = re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            content, re.S)
        self.assertTrue(blocks, f'{self.path} has no JSON-LD block')
        # Find the ItemList (each page emits exactly one).
        itemlist = None
        for raw in blocks:
            data = json.loads(raw)
            if data.get('@type') == 'ItemList':
                itemlist = data
                break
        self.assertIsNotNone(itemlist, f'{self.path} missing ItemList JSON-LD')
        elements = itemlist.get('itemListElement', [])
        self.assertGreaterEqual(
            len(elements), self.min_items, f'{self.path} ItemList too short')
        for el in elements:
            item = el.get('item', {})
            self.assertTrue(item.get('url', '').startswith('http'))

    def test_in_sitemap(self):
        resp = self.client.get('/sitemap.xml', HTTP_HOST='localhost')
        self.assertContains(resp, self.path)


class SportsLightingHubTests(SportsLandingPageContract, TestCase):
    """Tier-1 hub — owns the four head terms (stadium lights 2,900 / led
    stadium lights 1,000 / stadium light 720 / led sports lighting 390)."""

    path = '/products/sports-lighting/'
    title_keyword = 'LED Stadium Lights'
    body_keywords = ('stadium lights', 'led stadium lights',
                     'stadium light', 'led sports lighting')
    expected_slugs = ('vsp-xxxxw-9m-yp', 'vsp-xxxxw-12m-yp', 'rt590fl-s', 'rt390fl')


class FootballStadiumLightsPageTests(SportsLandingPageContract, TestCase):
    """Tier-2 — ``football stadium lights`` (480/mo) gets its own URL."""

    path = '/products/football-stadium-lights/'
    title_keyword = 'Football Stadium Lights'
    body_keywords = ('football stadium lights', 'football field lighting')


class TennisCourtLightingPageTests(SportsLandingPageContract, TestCase):
    """Tier-2 — ``tennis court lighting`` (590/mo); one page must cover BOTH
    the indoor and the outdoor intent or it ranks for neither long-tail."""

    path = '/products/tennis-court-lighting/'
    title_keyword = 'Tennis Court Lighting'
    body_keywords = ('tennis court lighting',
                     'outdoor tennis court lighting',
                     'indoor tennis court lighting')


class SportsLandingRoutingTests(TestCase):
    """The landing URLs must NOT be swallowed by the product_detail catch-all."""

    def test_hub_url_resolves_to_sports_lighting_view(self):
        from django.urls import resolve
        self.assertEqual(
            resolve('/products/sports-lighting/').url_name, 'sports_lighting')

    def test_football_url_resolves_to_football_view(self):
        from django.urls import resolve
        self.assertEqual(
            resolve('/products/football-stadium-lights/').url_name,
            'football_stadium_lights')

    def test_tennis_url_resolves_to_tennis_view(self):
        from django.urls import resolve
        self.assertEqual(
            resolve('/products/tennis-court-lighting/').url_name,
            'tennis_court_lighting')
