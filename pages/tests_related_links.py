"""Guard: SEO batch B2 cross-links between products / projects / news.

The detail pages must vote for the related content so the three "islands"
(product catalogue, project case studies, news) pass ranking signals to each
other. Links are derived deterministically from the category <-> sport/venue
taxonomy (project -> products, product -> projects) and from explicit keyword
matches in the news copy (never a weak generic link).
"""
import re

from django.test import TestCase


class ProjectToProductLinksTests(TestCase):
    def _get(self, slug):
        return self.client.get('/projects/%s/' % slug, HTTP_HOST='localhost')

    def test_sports_project_links_related_products(self):
        # FOOTBALL_FIELD -> SPORTS_LIGHTING products.
        resp = self._get('football-field-led-retrofit')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Related Products', content)
        self.assertIn('class="related-products"', content)
        self.assertIn('related-product-card', content)
        # at least one real product card links to a product detail page
        self.assertRegex(
            content, r'href="/products/[a-z0-9-]+/"',
            'project detail should render at least one related product link')

    def test_airport_project_links_area_or_flood_products(self):
        # AIRPORT -> AREA_SITE / FLOODLIGHT products (not sports).
        resp = self._get('beijing-capital-international-airport')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('class="related-products"', content)
        self.assertRegex(
            content, r'href="/products/[a-z0-9-]+/"')


class ProductToProjectLinksTests(TestCase):
    def _get(self, slug):
        return self.client.get('/products/%s/' % slug, HTTP_HOST='localhost')

    def test_sports_product_links_application_cases(self):
        # SPORTS_LIGHTING product -> sports venue projects.
        resp = self._get('vsp-xxxxw-9m-yp')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Application Cases', content)
        self.assertIn('class="related-projects"', content)
        self.assertRegex(
            content, r'href="/projects/[a-z0-9-]+/"',
            'product detail should render at least one application-case link')


class NewsCrossLinksTests(TestCase):
    def _get(self, slug):
        return self.client.get('/news/%s/' % slug, HTTP_HOST='localhost')

    def test_case_study_links_named_product_not_fabricated_project(self):
        # The FL6M retrofit case study names the FL6M-480W product (a sub-series
        # whose page is /products/fl6m/) -> must cross-link it. It also mentions
        # "Tianjin Binhai International Airport", but the catalogue only has a
        # *Beijing* airport project, so we must NOT fabricate a generic airport
        # link. This guards the "no weak link" rule.
        resp = self._get('low-cct-high-cri-high-mast-led-retrofit')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Related Products &amp; Projects', content)
        self.assertIn('href="/products/fl6m/"', content)
        # No weak/fabricated project link: the article names Tianjin, not Beijing.
        self.assertNotIn(
            'href="/projects/beijing-capital-international-airport/"', content)

    def test_news_naming_project_links_it(self):
        # Unit-level proof that the project branch of related_items_for_news
        # fires on an exact slug/title match. No seed article happens to name a
        # project by its exact title, so we synthesise one.
        from pages.views.data_loaders import get_projects
        from pages.views.related_links import related_items_for_news
        proj = next(
            (p for p in get_projects('en')
             if p.slug == 'football-field-led-retrofit'),
            None)
        self.assertIsNotNone(proj, 'football project fixture missing')
        article = {'title': proj.title, 'content': 'reference %s here' % proj.slug}
        _products, rel_projects = related_items_for_news(article, 'en')
        self.assertTrue(
            any(p.slug == proj.slug for p in rel_projects),
            'news naming a project by exact slug/title must link it')

    def test_generic_news_has_no_invented_cross_links(self):
        # Market/industry news names no specific product or project -> no
        # fabricated cross-link block.
        resp = self._get('global-led-lighting-market-2034')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('Related Products &amp; Projects', content)
