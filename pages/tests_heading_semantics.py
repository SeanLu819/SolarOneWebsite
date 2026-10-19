"""Guard: heading semantics — v1.10.34 fixes from the 2026-10-19 H-tag audit.

Two rendering-level fixes landed together (report:
``docs/h_tag_audit_2026-10-19.md``):

* **Fix 3 (P2, ``/contact/``)** — the company name sat directly under H1
  "Contact Us" as an **H3**, skipping a level (H1 -> H3). It is now an H2,
  sibling of "Agents & Distributors". The inline style keeps the old pixel
  metrics: the previous H3 relied on the UA default
  ``margin-block-start: 1em`` (of its 1.05rem font); an H2's UA default is
  0.83em, so the new tag spells ``margin: 1em 0 24px`` explicitly.
* **Fix 4 (P3, ``/products/<slug>/``)** — "Request a Sample" is a CTA, not a
  document section. Its title moved from
  ``<h3 class="detail-request-sample-title">`` to a ``<p>`` carrying the same
  class (every visual comes from the class), so the outline no longer
  contains a non-section heading.

Scope note: the audit's problem 1 (H1 -> H3 skips on the /products/,
/projects/ and /news/ list pages) was fixed in v1.10.35 (plan B: card
titles promoted H3 -> H2) and is covered by
``ListPageHeadingSemanticsTests`` below. Problem 2 (/projects/ H1 copy) and
problem 5 (About privacy block) landed in the same version and are guarded
by ``ProjectsH1CopyTests`` / ``AboutPrivacyBlockRemovedTests``.

The guards parse the *rendered* HTML through the test client. Before looking
for headings, three kinds of non-body markup are stripped:

1. ``<style>`` / ``<script>`` blocks — the product template's inline CSS
   documents the v1.10.20 heading change with literal ``<h2>`` examples inside
   a CSS comment; a naive ``<h[1-6]>`` scan pairs such a fake open tag with a
   far-away real ``</h2>`` and swallows the real H1 (this exact bug made the
   first draft of this guard report "first heading must be H1, got H2").
2. HTML comments — Django ``{% comment %}`` blocks never render, but
   ``<!-- -->`` blocks do.

Heading levels are derived from the markup itself, never hardcoded (iron rule 7).
"""

import re

from django.test import TestCase
from django.urls import reverse

_HEADING_RE = re.compile(r'<(h[1-6])\b[^>]*>(.*?)</\1>', re.S | re.I)
_STYLE_RE = re.compile(r'<style\b[^>]*>.*?</style>', re.S | re.I)
_SCRIPT_RE = re.compile(r'<script\b[^>]*>.*?</script>', re.S | re.I)
_COMMENT_RE = re.compile(r'<!--.*?-->', re.S)
_TAG_RE = re.compile(r'<[^>]+>')


def _headings(html):
    """Ordered [(level, plain_text)] for every rendered heading."""
    body = _COMMENT_RE.sub('', _SCRIPT_RE.sub('', _STYLE_RE.sub('', html)))
    out = []
    for m in _HEADING_RE.finditer(body):
        text = ' '.join(_TAG_RE.sub('', m.group(2)).split())
        out.append((int(m.group(1)[1]), text))
    return out


def _assert_no_level_skips(levels):
    """First heading must be H1 and no level may jump by more than one."""
    assert levels, 'no headings rendered at all'
    assert levels[0] == 1, 'first heading must be H1, got H%d' % levels[0]
    for prev, nxt in zip(levels, levels[1:]):
        assert nxt - prev <= 1, 'heading level skip H%d -> H%d' % (prev, nxt)


class ContactHeadingSemanticsTests(TestCase):
    """``/contact/``: company name is H2; the whole outline has no skips."""

    def _get(self):
        resp = self.client.get('/contact/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_company_name_is_h2(self):
        heads = _headings(self._get())
        company = [h for h in heads if 'BEIJING SOLARONE' in h[1]]
        self.assertEqual(
            len(company), 1,
            'company name heading must appear exactly once')
        self.assertEqual(
            company[0][0], 2,
            'company name must be H2 under H1 "Contact Us" '
            '(audit problem 3: it was an H3, skipping a level)')

    def test_heading_order_has_no_level_skips(self):
        _assert_no_level_skips([lvl for lvl, _ in _headings(self._get())])


class ProductDetailHeadingSemanticsTests(TestCase):
    """``/products/<slug>/``: the sample CTA title is not a heading.

    Products come in two layouts (``Product.page_layout``, picked in the
    admin): ``detail`` renders ``product_detail.html`` (full spec + sample
    CTA), ``overview`` renders ``product_overview.html`` (series landing
    page, no CTA). The CTA assertions therefore run on ``detail`` products
    only; the no-skip invariant covers every product, both layouts.
    """

    def _seed_products(self):
        from pages.views.utils import _load_seed
        products = _load_seed()['products']
        self.assertTrue(products, 'seed carries no products — guard would no-op')
        return products

    def _detail_slugs(self):
        slugs = [p['slug'] for p in self._seed_products()
                 if p.get('page_layout', 'detail') == 'detail']
        self.assertTrue(slugs, 'seed has no detail-layout products')
        return slugs

    def test_request_sample_title_is_not_a_heading(self):
        for slug in self._detail_slugs():
            with self.subTest(slug=slug):
                resp = self.client.get('/products/%s/' % slug,
                                       HTTP_HOST='localhost')
                self.assertEqual(resp.status_code, 200)
                html = resp.content.decode()
                self.assertNotIn(
                    '<h3 class="detail-request-sample-title"', html,
                    'CTA title must not be a heading (audit problem 4)')
                self.assertIn(
                    '<p class="detail-request-sample-title"', html,
                    'CTA title must keep its class-driven visuals on a <p>')
                self.assertIn(
                    'Request a Sample', html,
                    'CTA copy must stay visible after the tag change')

    def test_heading_order_has_no_level_skips(self):
        for p in self._seed_products():
            with self.subTest(slug=p['slug']):
                resp = self.client.get('/products/%s/' % p['slug'],
                                       HTTP_HOST='localhost')
                self.assertEqual(resp.status_code, 200)
                _assert_no_level_skips(
                    [lvl for lvl, _ in _headings(resp.content.decode())])


class ListPageHeadingSemanticsTests(TestCase):
    """v1.10.35 (audit problem 1, plan B): the three list pages promoted
    their card titles H3 -> H2, so H1 -> H2 is the new floor. Each card
    title keeps its class (all visuals live in the class) and each class
    now spells the old UA top margin explicitly — an H3's UA default is
    1em, an H2's is 0.83em, and base.css has no global reset, so without
    the explicit ``margin: 1em 0 …`` every card would shift ~3px.

    /products/ and /projects/ fall back to the seed JSON when the DB is
    empty (data_loaders), but ``get_news`` is deliberately DB-only with no
    silent seed fallback — an empty test DB would render zero news cards
    and the /news/ half of this guard would pass vacuously. So the test
    seeds one article first (same pattern as tests_related_links' Project
    probe) and every URL additionally asserts its card class rendered.
    """

    CARD_MARKERS = {
        '/products/': 'product-card-title',
        '/projects/': 'project-card-title',
        '/news/': 'news-card-title',
    }

    def _seed_one_news_article(self):
        from unittest.mock import patch
        from django.utils import timezone
        from pages.models import NewsArticle
        with patch('pages.models._sync_news_media_to_static'):
            NewsArticle.objects.create(
                slug='zz-heading-probe',
                title='Heading Probe Article',
                content='probe body',
                category='Product News',
                published_at=timezone.now())

    def test_list_pages_have_no_level_skips(self):
        self._seed_one_news_article()
        try:
            for url, marker in self.CARD_MARKERS.items():
                with self.subTest(url=url):
                    resp = self.client.get(url, HTTP_HOST='localhost')
                    self.assertEqual(resp.status_code, 200)
                    html = resp.content.decode()
                    self.assertIn(
                        marker, html,
                        'no cards rendered on %s — guard would be vacuous'
                        % url)
                    _assert_no_level_skips(
                        [lvl for lvl, _ in _headings(html)])
        finally:
            from pages.models import NewsArticle
            NewsArticle.objects.filter(slug='zz-heading-probe').delete()


class ProjectsH1CopyTests(TestCase):
    """v1.10.35 (audit problem 2): /projects/ lost its keyword-free
    "Trusted Worldwide" (a near-duplicate of /about/'s H1) for
    "Our Lighting Projects", translated in all five non-English locales.
    """

    EN_COPY = 'Our Lighting Projects'

    def _h1(self, url):
        resp = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, url)
        heads = _headings(resp.content.decode())
        self.assertTrue(heads, 'no headings on %s' % url)
        self.assertEqual(heads[0][0], 1,
                         'first heading on %s is not H1' % url)
        return heads[0][1]

    def test_h1_is_the_keyword_copy(self):
        self.assertEqual(self._h1('/projects/'), self.EN_COPY)

    def test_h1_is_translated_in_every_locale(self):
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            with self.subTest(lang=lang):
                text = self._h1('/%s/projects/' % lang)
                self.assertTrue(text, '%s H1 rendered empty' % lang)
                self.assertNotEqual(
                    text, self.EN_COPY,
                    '%s fell back to the English H1 (translation missing)'
                    % lang)


class AboutPrivacyBlockRemovedTests(TestCase):
    """v1.10.35 (audit problem 5): the duplicated privacy block is gone from
    /about/ (the full six-section version lives on /privacy/), and the
    cookie-banner link that used to target the block's #privacy anchor now
    points at /privacy/ itself.
    """

    def test_about_has_no_privacy_heading(self):
        resp = self.client.get('/about/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        heads = _headings(resp.content.decode())
        privacy = [h for h in heads if 'Privacy Policy' in h[1]]
        self.assertEqual(
            privacy, [],
            'About must not carry the privacy block headings (the cookie '
            'banner link text is not a heading, so this is section-only)')

    def test_about_has_no_dead_privacy_anchor(self):
        resp = self.client.get('/about/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn('/about/#privacy', html,
                         'cookie banner still links to the removed anchor')
        self.assertNotIn('id="privacy"', html,
                         'the #privacy section anchor still exists')

    def test_cookie_banner_links_to_privacy_page(self):
        resp = self.client.get('/about/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'href="%s"' % reverse('privacy'))

    def test_privacy_page_keeps_its_own_h1(self):
        resp = self.client.get('/privacy/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        heads = _headings(resp.content.decode())
        self.assertTrue(heads, '/privacy/ lost its headings')
        self.assertEqual(heads[0][0], 1, '/privacy/ first heading is not H1')
        self.assertIn('Privacy Policy', heads[0][1])
