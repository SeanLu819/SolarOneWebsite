"""Guard: v1.10.26 — page-scoped CSS renders in <head>, and the series
sub-model selector grid keeps a positive minimum track.

Two regressions this locks down:

1. **First-paint flash.** The three product templates carried their page CSS
   in a body-inline ``<style>`` placed *after* the content markup. While the
   HTML streams, the browser paints the hero image before that style parses,
   so the image first rendered at natural size (huge) and snapped to its
   16:9 box a moment later. The styles now travel in a ``{% block page_css %}``
   rendered inside ``<head>`` in ``base.html``. The guard asserts the *rendered
   position* (before ``</head>``), not the template layout, so both the block
   and its head registration are covered end-to-end.

2. **Selector collapse.** ``.detail-series-children-grid`` used
   ``repeat(auto-fill, minmax(0, 1fr))`` — with ``auto-fill`` the zero minimum
   lets the track count grow without bound, so every card collapsed to a
   ~0px column and the model names wrapped one character per line.
   The fix is a real 240px floor. The guard asserts the value itself, not a
   substring of the selector.
"""
import re

from django.test import TestCase


#: marker CSS each template must carry inside its page_css block, and the
#: page that exercises it (overview hub / leaf detail / listing).
#: The marker includes the `` {`` rule brace so it can only match the CSS
#: rule, never the ``class="..."`` attribute the rule styles.
PAGES = (
    ('/products/m-series/', '.detail-series-children-grid {'),
    ('/products/fl6m/', '.detail-ordering-table {'),
    ('/products/', '.product-card-specs {'),
)


class PageCssRendersInHeadTests(TestCase):
    """The page CSS must be inside <head> at render time."""

    def _assert_style_in_head(self, url, marker):
        resp = self.client.get(url, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        head_end = body.find('</head>')
        self.assertGreater(head_end, 0, '%s: no </head> rendered' % url)
        style_at = body.find(marker)
        self.assertGreaterEqual(style_at, 0,
                                '%s: page CSS marker %r missing entirely'
                                % (url, marker))
        self.assertLess(
            style_at, head_end,
            '%s: %r renders after </head> — the style block fell back into '
            '<body> and the first-paint flash is back' % (url, marker))

    def test_product_overview_css_is_in_head(self):
        self._assert_style_in_head('/products/m-series/',
                                   '.detail-series-children-grid')

    def test_product_detail_css_is_in_head(self):
        self._assert_style_in_head('/products/fl6m/', '.detail-ordering-table')

    def test_products_listing_css_is_in_head(self):
        self._assert_style_in_head('/products/', '.products-banner')

    def test_page_css_marker_not_duplicated_in_body(self):
        """The move must be a move: no copy of the style may linger mid-body.

        Without this, a botched cut-and-paste that *duplicates* the block
        (head copy + body copy) would pass the three tests above while the
        page ships twice the CSS.
        """
        for url, marker in PAGES:
            with self.subTest(url=url):
                body = self.client.get(url, HTTP_HOST='localhost'
                                       ).content.decode()
                # the marker CSS rule may appear only once in the document
                self.assertEqual(
                    body.count(marker), 1,
                    '%s: %r appears %d times — the style block was copied, '
                    'not moved' % (url, marker, body.count(marker)))


class SeriesChildrenGridMinTrackTests(TestCase):
    """auto-fill + minmax(0, 1fr) = unbounded zero-width tracks."""

    #: The product decision: each selector card gets at least 240px, so on a
    #: ~900px content column the hub shows 3 cards per row, never a
    #: one-character-per-line sliver. Hardcoded on purpose (铁律 4b): the
    #: expected value is an independent statement, and the template must
    #: match it literally.
    MIN_TRACK = 'repeat(auto-fill, minmax(240px, 1fr))'

    def test_grid_uses_a_positive_min_track(self):
        body = self.client.get('/products/m-series/',
                               HTTP_HOST='localhost').content.decode()
        self.assertIn(self.MIN_TRACK, body,
                      'the series selector grid lost its 240px floor — '
                      'cards will collapse to one character per line')
        head_end = body.find('</head>')
        self.assertLess(body.find(self.MIN_TRACK), head_end,
                        'the grid rule escaped <head>')
        # and the broken variant must be gone, not co-present
        self.assertNotIn(
            'repeat(auto-fill, minmax(0, 1fr))', body,
            'the zero-min track still renders somewhere on the hub page')
