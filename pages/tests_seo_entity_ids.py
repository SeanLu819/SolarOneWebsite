"""v1.10.24 — JSON-LD entity anchors (``@id``) and NewsArticle authorship.

Audit finding A6, lower tier. Two gaps, both about how a consumer connects the
entities on a page to each other:

1. **No ``@id`` anywhere on the site.** Every entity was identified only by its
   ``name``. That means a crawler cannot tell that the ``Organization`` in
   ``base.html`` and the ``publisher`` inside a news article are the same real
   world company — it has to match them on string equality. ``@id`` is the
   schema.org mechanism for saying "same entity", and it is what knowledge
   graphs key on.

2. **NewsArticle had no ``author``.** It carried a ``publisher`` (added
   earlier), so the article had an organisation attached but nobody credited
   with writing it. Google treats a missing author on an Article as an
   incomplete rich result. The project Article already carries one
   (``tests_jsonld_author.py``); news did not.

Deliberately NOT added: ``WebSite.potentialAction``/``SearchAction``. The site
has no search — there is no search route, no search template, no search form.
Declaring a SearchAction that points nowhere is a structured-data claim the
site cannot honour, and Google flags it. The audit recommended it as optional;
it is not optional here, it is wrong.
"""
import json
import re

from django.test import TestCase

ORIGIN = 'https://www.solaronelighting.com'
ORG_ID = f'{ORIGIN}/#organization'


def _blocks(content):
    """Every ld+json payload, tolerating a CSP nonce on the tag (iron law 29)."""
    out = []
    for raw in re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            content, re.DOTALL):
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def _by_type(content, type_name):
    return [b for b in _blocks(content) if b.get('@type') == type_name]


class EntityAnchorTests(TestCase):
    """``@id`` presence and cross-references."""

    def test_the_site_organization_carries_a_stable_id(self):
        """The anchor is the whole point: it must be identical on every page
        and every language, or it identifies nothing."""
        for url in ('/', '/fr/', '/ar/', '/products/', '/news/'):
            with self.subTest(url=url):
                html = self.client.get(
                    url, HTTP_HOST='localhost').content.decode()
                orgs = _by_type(html, 'Organization')
                self.assertTrue(orgs, f'{url} 没有 Organization JSON-LD')
                for org in orgs:
                    self.assertEqual(
                        ORG_ID, org.get('@id'),
                        f'{url} 的 Organization @id 不对：{org.get("@id")!r}')

    def test_the_website_node_carries_an_id_and_names_its_publisher(self):
        """WebSite.publisher must be a reference to the same ``@id`` the
        Organization block declares — a duplicated inline Organization would
        create two nodes instead of linking them, which is the opposite of the
        intent."""
        html = self.client.get('/', HTTP_HOST='localhost').content.decode()
        sites = _by_type(html, 'WebSite')
        self.assertEqual(1, len(sites), f'期望 1 个 WebSite，实际 {len(sites)}')
        site = sites[0]
        self.assertEqual(f'{ORIGIN}/#website', site.get('@id'))
        self.assertEqual(
            {'@id': ORG_ID}, site.get('publisher'),
            'WebSite.publisher 必须是 Organization @id 的引用，不能内联展开')

    def test_no_search_action_is_declared(self):
        """The site has no search. If a SearchAction ever appears, it is
        pointing at something that does not exist.

        This is a guard against a well-meaning future addition: SearchAction is
        routinely copy-pasted from an SEO checklist, and on a site with no
        search endpoint it produces a rich result that 404s.
        """
        for url in ('/', '/products/'):
            with self.subTest(url=url):
                html = self.client.get(
                    url, HTTP_HOST='localhost').content.decode()
                self.assertNotIn(
                    'SearchAction', html,
                    f'{url} 声明了 SearchAction，但站点没有搜索功能')
                self.assertNotIn(
                    'potentialAction', html,
                    f'{url} 声明了 potentialAction，但站点没有搜索功能')

    def test_news_articles_credit_an_author(self):
        """The regression: NewsArticle had a publisher but no author."""
        from pages.views.utils import _load_seed

        slug = _load_seed()['news'][0]['slug']
        html = self.client.get(
            f'/news/{slug}/', HTTP_HOST='localhost').content.decode()
        articles = _by_type(html, 'NewsArticle')
        self.assertEqual(1, len(articles))
        article = articles[0]
        author = article.get('author')
        self.assertIsNotNone(
            author, f'news/{slug} 的 NewsArticle 没有 author')
        self.assertEqual('Organization', author.get('@type'))
        self.assertTrue(
            author.get('name', '').strip(),
            f'news/{slug} 的 author.name 为空')
        self.assertEqual(
            ORG_ID, author.get('@id'),
            'author 必须指向站点 Organization 的同一个 @id，否则无法与base '
            '里的 Organization 关联')

    def test_the_news_publisher_and_author_resolve_to_the_same_entity(self):
        """One company, not two. If publisher and author carried different
        names or different @ids, a knowledge graph would read them as two
        distinct organisations that happen to co-author an article."""
        from pages.views.utils import _load_seed

        slug = _load_seed()['news'][0]['slug']
        html = self.client.get(
            f'/news/{slug}/', HTTP_HOST='localhost').content.decode()
        article = _by_type(html, 'NewsArticle')[0]
        self.assertEqual(
            article['author'].get('@id'), article['publisher'].get('@id'),
            'author 与 publisher 指向不同实体')
        self.assertEqual(
            article['author'].get('name'), article['publisher'].get('name'),
            'author 与 publisher 名称不一致')

    def test_every_entity_id_on_a_page_is_unique_and_absolute(self):
        """Two nodes sharing an ``@id`` on one page is a contradiction the
        consumer cannot resolve; a relative ``@id`` cannot be resolved at all
        outside the page it was scraped from."""
        for url in ('/', '/fr/', '/products/', '/projects/', '/news/',
                    '/stadium-lighting/'):
            with self.subTest(url=url):
                html = self.client.get(
                    url, HTTP_HOST='localhost').content.decode()
                ids = []
                for block in _blocks(html):
                    self.assertIn(
                        '@id', block,
                        f'{url} 有一个 {block.get("@type")} 缺 @id')
                    ids.append(block['@id'])
                    self.assertTrue(
                        block['@id'].startswith('https://'),
                        f'{url} 的 @id 不是绝对 URL：{block["@id"]!r}')
                self.assertEqual(
                    len(ids), len(set(ids)),
                    f'{url} 上有重复的 @id：{ids}')

    def test_a_product_id_lands_on_the_product_and_brand_points_at_us(self):
        """The Product node gets its own anchor, and its brand is a reference to
        the site Organization rather than a second inline copy — otherwise the
        brand becomes a separate knowledge-graph node on all 25 product pages."""
        from pages.views.utils import _load_seed

        slug = _load_seed()['products'][0]['slug']
        html = self.client.get(
            f'/products/{slug}/', HTTP_HOST='localhost').content.decode()
        products = _by_type(html, 'Product')
        self.assertEqual(1, len(products))
        product = products[0]
        self.assertIn(
            slug, product['@id'],
            f'Product @id 没有指向自己的 URL：{product["@id"]!r}')
        self.assertEqual(
            ORG_ID, (product.get('brand') or {}).get('@id'),
            'Product.brand 必须引用 Organization @id，而不是内联展开')

    def test_faq_pages_on_different_pages_get_different_ids(self):
        """Both the product FAQ and the stadium FAQ are FAQPage nodes. Without
        distinct anchors a consumer is free to merge them into one entity,
        which would attach the stadium answers to every product.

        Asserted in both directions: the two ids must differ, AND each must
        point at its OWN page. A mutation probe that repointed the stadium FAQ
        at ``/products/#faq`` left the "must differ" check green — no product
        sits at that exact URL — which is why the ownership check is here.
        """
        from pages.views.utils import _load_seed

        slug = _load_seed()['products'][0]['slug']
        product_html = self.client.get(
            f'/products/{slug}/', HTTP_HOST='localhost').content.decode()
        stadium_html = self.client.get(
            '/stadium-lighting/', HTTP_HOST='localhost').content.decode()
        product_faq = _by_type(product_html, 'FAQPage')
        stadium_faq = _by_type(stadium_html, 'FAQPage')
        self.assertEqual(1, len(product_faq), '产品页应有 1 个 FAQPage')
        self.assertEqual(1, len(stadium_faq), '落地页应有 1 个 FAQPage')
        self.assertNotEqual(
            product_faq[0]['@id'], stadium_faq[0]['@id'],
            '产品页与落地页的 FAQPage 共用了 @id，会被合并成同一实体')
        for node, owner in ((product_faq[0], slug), (stadium_faq[0],
                                                     'stadium-lighting')):
            with self.subTest(owner=owner):
                self.assertTrue(
                    node['@id'].endswith('#faq'),
                    f'{owner} 的 FAQPage @id 应以 #faq 结尾：{node["@id"]!r}')
                self.assertIn(
                    f'/{owner}/', node['@id'],
                    f'{owner} 的 FAQPage @id 没有指向自己的页面：'
                    f'{node["@id"]!r}')

    def test_breadcrumb_trails_are_anchored_per_page(self):
        """BreadcrumbList describes one page's trail, so its anchor is the page
        URL. The shared include is the right place for it — all six callers
        emit it through the same template."""
        from pages.views.utils import _load_seed

        project_slug = _load_seed()['projects'][0]['slug']
        for url in ('/products/', '/projects/', f'/projects/{project_slug}/'):
            with self.subTest(url=url):
                html = self.client.get(
                    url, HTTP_HOST='localhost').content.decode()
                crumbs = _by_type(html, 'BreadcrumbList')
                self.assertEqual(1, len(crumbs), f'{url} 应有 1 个 BreadcrumbList')
                self.assertTrue(
                    crumbs[0]['@id'].startswith(ORIGIN),
                    f'{url} 的 BreadcrumbList @id 必须是绝对 URL：'
                    f'{crumbs[0]["@id"]!r}')
                self.assertTrue(
                    crumbs[0]['@id'].endswith('#breadcrumb'),
                    f'{url} 的 BreadcrumbList @id 应以 #breadcrumb 结尾：'
                    f'{crumbs[0]["@id"]!r}')

    def test_the_article_id_is_its_own_page_not_the_site_root(self):
        """An entity's ``@id`` must identify *that* entity. Pointing a news
        article at the site root would collapse every article into one node —
        the precise failure ``@id`` is meant to prevent."""
        from pages.views.utils import _load_seed

        news = _load_seed()['news']
        first, second = news[0], news[1]
        ids = []
        for item in (first, second):
            html = self.client.get(
                f'/news/{item["slug"]}/',
                HTTP_HOST='localhost').content.decode()
            article = _by_type(html, 'NewsArticle')[0]
            ids.append(article['@id'])
            self.assertIn(
                item['slug'], article['@id'],
                f'news/{item["slug"]} 的 @id 没有指向自己的 URL：'
                f'{article["@id"]!r}')
        self.assertNotEqual(
            ids[0], ids[1], '两篇不同的新闻共用了一个 @id')
