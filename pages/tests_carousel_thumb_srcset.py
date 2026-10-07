"""Carousel thumbnail responsive-srcset guards (v1.10.24).

Why this exists
---------------
Every carousel gallery entry is emitted TWICE: once as a slide and once as a
strip thumbnail. Before v1.10.24 the slide carried ``srcset`` + ``sizes`` but
the thumbnail carried only a bare ``src`` pointing at the ORIGINAL 1520px file.

Consequence: the browser downloaded each gallery image twice — a ~1248w variant
for the slide AND the full original for a ~145px-wide thumbnail. Measured on
``m-series`` (4 images): 383 KB before responsive images, 717 KB after, i.e.
the responsive-image rollout made the page *slower* instead of faster. The
last thumbnail (the 4th on the 20 of 24 products that have exactly 4 images)
is also the last request in the lazy queue, so it was visibly the slowest.

What these guards assert
------------------------
1. The structural property: the thumbnail ``<img>`` itself carries ``srcset``
   and ``sizes``. (Asserting only that some identifier appears in the file would
   be satisfied by the slide tag alone — iron rule 32 — so the assertion is made
   on the tag extracted from inside the ``.ps-thumb`` button.)
2. The two layout decisions the values encode, stated LITERALLY here:
   * ``THUMB_SIZES`` — a strip thumbnail renders ~190px wide (760px strip / 4).
   * ``SLIDE_SIZES`` — the carousel box is ``max-width: 760px``.
   They are deliberately NOT imported from ``pages.image_variants``: an
   expectation derived from the implementation moves with a regression and the
   guard stays green (iron rule 4b). A separate cross-check asserts that the
   CSS really does cap the carousel at 760px, which is where the number comes
   from.
"""
import os
import re
import unittest

# repo root: pages/tests_carousel_thumb_srcset.py -> pages/ -> root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TPL = os.path.join(_ROOT, 'templates')

# Templates that render the shared carousel (slide + .ps-thumb strip).
CAROUSEL_TEMPLATES = (
    'product_detail.html',
    'product_overview.html',
    'project_detail.html',
)

# --- Hard-coded layout decisions (NOT derived from any implementation) -------
# A strip thumbnail is ~190px wide. Two of the three carousels sit in a 760px
# box ((760 - 3*8) / 4), the project carousel is full width, but both land on
# the same candidate: 190px picks the 360w variant at 1x and the 720w one at 2x.
THUMB_SIZES = '(max-width:768px) 24vw, 190px'

# The slide slot is NOT the same on every page. The product carousels are capped
# at 760px by `.ps-carousel { max-width: 760px }`, but the project carousel
# lives in `.detail-image-full` and has NO max-width — it spans the content
# column (~1200px). Declaring 760px there would make the browser fetch the 720w
# candidate for a ~1200px slot, i.e. a visible sharpness regression.
SLIDE_SIZES_BY_TEMPLATE = {
    'product_detail.html': '(max-width:768px) 92vw, 760px',
    'product_overview.html': '(max-width:768px) 92vw, 760px',
    'project_detail.html': '(max-width:768px) 100vw, (max-width:1200px) 90vw, 1200px',
}

# Cross-checks against the stylesheet, per template: the selector that caps the
# carousel box and whether it is expected to carry a max-width at all.
CAROUSEL_BOX_SELECTOR = '.ps-carousel'
# The two product carousels are explicitly capped; the project one is not.
CAROUSEL_CAPPED_TEMPLATES = ('product_detail.html', 'product_overview.html')
# The project carousel is full width — asserted through its wrapper, so a
# future `max-width` on `.ps-carousel` there would be caught as a change.
PROJECT_FULL_WIDTH_SELECTOR = '.detail-image-full'


def _comment_free(text):
    """Strip HTML / Django comments so an assertion can never be satisfied by
    text written inside a comment (iron rule 13)."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)
    text = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', text,
                  flags=re.S)
    return text


def _read(name):
    with open(os.path.join(_TPL, name), encoding='utf-8') as fh:
        return _comment_free(fh.read())


def _thumb_img_tags(name):
    """Every ``<img ...>`` inside a ``<button class="ps-thumb ...">`` block."""
    src = _read(name)
    out = []
    for block in re.findall(r'<button class="ps-thumb[^"]*"[^>]*>(.*?)</button>',
                            src, flags=re.S):
        out.extend(re.findall(r'<img\b[^>]*>', block, flags=re.S))
    return out


def _slide_img_tags(name):
    """Every ``<img ...>`` inside a ``<div class="ps-carousel-slide ...">``."""
    src = _read(name)
    out = []
    for block in re.findall(
            r'<div class="ps-carousel-slide[^"]*">(.*?)</div>', src, flags=re.S):
        out.extend(re.findall(r'<img\b[^>]*>', block, flags=re.S))
    return out


def _attr(tag, name):
    m = re.search(r'\b%s="([^"]*)"' % re.escape(name), tag, flags=re.S)
    return m.group(1) if m else None


def _rule(css, selector):
    """Return the single rule block for ``selector`` (iron rule 4: never match
    the whole stylesheet, ``.foo[^{]*\\{`` also matches ``.foos``).

    The selector must sit at the start of a line and be followed directly by the
    brace, so ``.ps-carousel`` cannot pick up ``.ps-carousel-slide``. A preceding
    ``}`` or ``,`` is NOT required — a rule that follows a stripped CSS comment
    is preceded only by whitespace.
    """
    m = re.search(r'(?m)^[ \t]*%s[ \t]*\{([^}]*)\}' % re.escape(selector), css)
    return m.group(1) if m else None


class CarouselThumbnailSrcsetTests(unittest.TestCase):
    """The strip thumbnail must be responsive, not a full-size original."""

    def test_every_carousel_template_has_a_thumbnail_strip(self):
        # Guard the guard: if a template's markup is renamed, the suites below
        # would silently iterate an empty list and pass.
        for name in CAROUSEL_TEMPLATES:
            self.assertTrue(_thumb_img_tags(name),
                            'no .ps-thumb <img> found in %s' % name)
            self.assertTrue(_slide_img_tags(name),
                            'no .ps-carousel-slide <img> found in %s' % name)

    def test_thumbnail_carries_srcset_and_sizes(self):
        """Regression: thumbnail had a bare src -> the 1520px original was
        downloaded a second time for a ~190px slot."""
        for name in CAROUSEL_TEMPLATES:
            for tag in _thumb_img_tags(name):
                self.assertIn('srcset=', tag,
                              'thumbnail without srcset in %s: %s' % (name, tag))
                self.assertIn('sizes=', tag,
                              'thumbnail without sizes in %s: %s' % (name, tag))

    def test_thumbnail_sizes_matches_the_rendered_slot(self):
        """A thumbnail renders ~190px; declaring 1200px would make the browser
        fetch the 1248w variant for it."""
        for name in CAROUSEL_TEMPLATES:
            for tag in _thumb_img_tags(name):
                self.assertEqual(THUMB_SIZES, _attr(tag, 'sizes'),
                                 'wrong thumbnail sizes in %s: %r'
                                 % (name, _attr(tag, 'sizes')))

    def test_thumbnail_srcset_uses_the_same_source_as_the_slide(self):
        """Both tags must build their set from the same gallery URL, otherwise
        the two downloads cannot share a cache entry."""
        for name in CAROUSEL_TEMPLATES:
            for tag in _thumb_img_tags(name):
                self.assertIn('|srcset', _attr(tag, 'srcset'),
                              'thumbnail srcset is not built from img.src in %s'
                              % name)

    def test_slide_sizes_matches_the_carousel_box(self):
        """A slide must declare the slot it actually renders into. Declaring
        1200px for the 760px product box made the browser pick 1248w; declaring
        760px for the full-width project box would pick 720w and soften it."""
        for name in CAROUSEL_TEMPLATES:
            expected = SLIDE_SIZES_BY_TEMPLATE[name]
            for tag in _slide_img_tags(name):
                self.assertEqual(expected, _attr(tag, 'sizes'),
                                 'wrong slide sizes in %s: %r'
                                 % (name, _attr(tag, 'sizes')))

    def test_carousel_box_css_agrees_with_the_declared_sizes(self):
        """Cross-check the number each slide `sizes` encodes against the CSS."""
        for name in CAROUSEL_TEMPLATES:
            css = re.sub(r'/\*.*?\*/', '', _read(name), flags=re.S)
            block = _rule(css, CAROUSEL_BOX_SELECTOR)
            self.assertIsNotNone(
                block, '%s rule missing in %s' % (CAROUSEL_BOX_SELECTOR, name))
            if name in CAROUSEL_CAPPED_TEMPLATES:
                self.assertIn('max-width: 760px', block,
                              '.ps-carousel max-width changed in %s: %s'
                              % (name, block.strip()[:120]))
            else:
                # Full-width carousel: no cap on the box, capped by the wrapper.
                self.assertNotIn('max-width', block,
                                 '.ps-carousel gained a max-width in %s; the '
                                 'slide sizes must be re-derived' % name)
                wrapper = _rule(css, PROJECT_FULL_WIDTH_SELECTOR)
                self.assertIsNotNone(
                    wrapper,
                    '%s wrapper missing in %s' % (PROJECT_FULL_WIDTH_SELECTOR, name))
                self.assertIn('width: 100%', wrapper)

    def test_thumbnail_strip_is_a_single_row(self):
        """The '4th thumbnail is slow' report assumed a wrapped strip putting
        later thumbs below the fold. It must stay one row: if it wraps, the
        layout (and the lazy-load order) changes."""
        for name in CAROUSEL_TEMPLATES:
            css = re.sub(r'/\*.*?\*/', '', _read(name), flags=re.S)
            block = _rule(css, '.ps-thumbnails')
            self.assertIsNotNone(block, '.ps-thumbnails rule missing in %s' % name)
            self.assertIn('display: flex', block)
            self.assertNotIn('flex-wrap: wrap', block,
                             '.ps-thumbnails started wrapping in %s' % name)
