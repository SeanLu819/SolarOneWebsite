"""Guard: SEO batch B2 cross-links between products / projects / news.

The detail pages must vote for the related content so the three "islands"
(product catalogue, project case studies, news) pass ranking signals to each
other.

Two directions, both **manual only** since v1.10.26:

* product -> projects ("Application Cases"): the editor picks projects in the
  admin (``Product.application_cases``). The old category-based auto match was
  deleted: it fabricated venue pairings the business never audited. No pick
  means no section at all.
* project -> products ("Related Products"): the editor picks the luminaires
  (``Project.related_products``). The older heuristic was deleted: it iterated
  a ``set`` (so one project showed different products between process starts)
  and paired venues with luminaires never installed there.

News links stay keyword-matched against explicit model numbers / project slugs
so we never emit a weak generic link.
"""
import re

from django.test import TestCase


class ProjectToProductLinksTests(TestCase):
    """Manual only: an unpicked project must not claim any luminaire."""

    def _get(self, slug):
        return self.client.get('/projects/%s/' % slug, HTTP_HOST='localhost')

    def test_a_project_with_no_manual_pick_shows_no_related_products(self):
        # 铁律 7：断言不许写死内容。这里从 seed 真源派生「未手工选择」的项目列表，
        # 而不是写死两个 slug —— 一旦有人在后台给某个项目选了灯具，它**必须**显示，
        # 写死名单会让守卫反过来把正确行为判成错误（v1.10.25 就撞上过：
        # football-field-led-retrofit 被手工选了 fl9m，硬编码用例立刻变红）。
        from pages.views.utils import _load_seed
        seed = _load_seed()
        unpicked = [p['slug'] for p in seed['projects']
                    if not (p.get('related_product_slugs') or [])]
        self.assertGreater(len(unpicked), 0,
                           '所有项目都已手工选择，本用例失去意义')
        for slug in unpicked[:2]:
            with self.subTest(slug=slug):
                resp = self._get(slug)
                self.assertEqual(200, resp.status_code)
                content = resp.content.decode()
                self.assertNotIn('class="related-products"', content,
                                 '%s rendered related products with no pick'
                                 % slug)
                self.assertNotIn('related-product-card', content)


class ProductToProjectLinksTests(TestCase):
    """Manual only: an unpicked product must not claim any project."""

    def _get(self, slug):
        return self.client.get('/products/%s/' % slug, HTTP_HOST='localhost')

    def test_a_product_with_no_pick_shows_no_application_cases(self):
        # 铁律 7：断言不许写死内容。从 seed 真源派生「未手工选择」的产品列表，
        # 而不是写死两个 slug —— 一旦有人在后台给某个产品选了项目，它**必须**显示，
        # 写死名单会让守卫把正确行为判成错误。
        from pages.views.utils import _load_seed
        seed = _load_seed()
        unpicked = [p['slug'] for p in seed['products']
                    if not (p.get('application_case_slugs') or [])]
        self.assertGreater(len(unpicked), 0,
                           '所有产品都已手工选择，本用例失去意义')
        for slug in unpicked[:3]:
            with self.subTest(slug=slug):
                resp = self._get(slug)
                self.assertEqual(200, resp.status_code)
                content = resp.content.decode()
                self.assertNotIn('class="related-projects"', content,
                                 '%s rendered application cases with no pick'
                                 % slug)
                self.assertNotIn('related-project-card', content)

    def test_category_alone_never_produces_cases(self):
        # The "no auto, no fallback" law, at unit level: even a product whose
        # category sits in the old auto-match table gets NOTHING until the
        # editor picks projects. The deleted implementation would return the
        # sports venues here -- so this also works as the mutation probe
        # target for any attempt to resurrect the taxonomy match.
        from types import SimpleNamespace
        from unittest.mock import patch
        from pages.views import related_links
        product = SimpleNamespace(category='SPORTS_LIGHTING',
                                  application_case_slugs=[])
        with patch.object(related_links, 'get_projects',
                          return_value=[SimpleNamespace(slug='any-project')]):
            self.assertEqual(
                related_links.application_cases_for_product(product, 'en'),
                [],
                'category taxonomy resurrected the auto match')

    def test_the_seed_pick_is_the_only_source(self):
        # Seed/dict path (iron law 33: the slugs must be a real attribute):
        # the helper returns exactly the picked slugs, resolved through
        # get_projects -- and never consults the product category.
        from types import SimpleNamespace
        from unittest.mock import patch
        from pages.views import related_links
        product = SimpleNamespace(
            category='ACCESSORY',
            application_case_slugs=['beijing-capital-international-airport'])
        fake = SimpleNamespace(slug='beijing-capital-international-airport')
        with patch.object(related_links, 'get_projects',
                          return_value=[fake]):
            out = related_links.application_cases_for_product(product, 'en')
        self.assertEqual([p.slug for p in out],
                         ['beijing-capital-international-airport'])

    def test_the_db_m2m_is_the_only_source(self):
        # DB path: the M2M manager wins; the category stays irrelevant.
        from types import SimpleNamespace
        from unittest.mock import patch
        from pages.views import related_links
        fake = SimpleNamespace(slug='karting-track-led-retrofit')
        product = SimpleNamespace(
            category='ACCESSORY',
            application_cases=SimpleNamespace(all=lambda: [fake]))
        with patch.object(related_links, 'get_projects',
                          return_value=[fake]):
            out = related_links.application_cases_for_product(product, 'en')
        self.assertEqual([p.slug for p in out],
                         ['karting-track-led-retrofit'])


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
