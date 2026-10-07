"""v1.10.24 — site-wide ``og:image`` fallback (audit finding A8).

Found by reading the deployed pages, not by a failing test. ``base.html``
emitted ``og:image`` only when ``SiteConfig.og_image`` was set, and that field
is empty in production. Every page without its own override therefore shipped a
``twitter:card=summary_large_image`` declaration with no picture behind it.
Facebook, WhatsApp, Telegram and Slack render such a link as bare text.

Affected at the time of the audit: the home page in every language and the
``/stadium-lighting/`` keyword hub — the two most shared URLs on the site.

The fix is a generated 1200x630 brand card at ``static/images/og-default.webp``
used as the site-wide fallback. The file is deliberately committed rather than
generated at build time: the v1.10.18 image-variant hotfix proved a build-time
generator can silently produce zero files, and an og:image that 404s is worse
than one that is merely generic.

These guards assert the **rendered value** (iron law 8/22): a missing meta tag
is syntactically valid, so only the value proves the fallback fired.
"""
import re

from django.conf import settings
from django.test import TestCase


class DefaultOgImageTests(TestCase):
    """The regression itself, pinned by URL rather than by template type."""

    ORIGIN = 'https://www.solaronelighting.com'
    FALLBACK = '/static/images/og-default.webp'

    #: Product decision: Open Graph renders reliably at 1.91:1 and Facebook and
    #: WhatsApp crop anything else. Written as a literal rather than read from
    #: the file, so regenerating the card at the wrong ratio fails here.
    EXPECTED_SIZE = (1200, 630)

    def _meta(self, html, prop):
        found = re.search(
            r'<meta property="%s" content="([^"]+)"' % re.escape(prop), html)
        return found.group(1) if found else ''

    def test_the_fallback_card_exists_and_has_the_open_graph_ratio(self):
        """The fallback must be a real committed file, not a hopeful path.

        Iron law 6: a path that 404s in production is worse than no tag at all,
        because consumers cache the failure. Assert the file on disk and its
        pixel size here so a rename or a bad regeneration is caught locally.
        """
        from PIL import Image

        path = settings.BASE_DIR / 'static' / 'images' / 'og-default.webp'
        self.assertTrue(
            path.exists(),
            f'default og card missing: {path} — every page without an override '
            'would point at a 404')
        with Image.open(path) as im:
            self.assertEqual(
                self.EXPECTED_SIZE, im.size,
                f'og card is {im.size}, Open Graph wants {self.EXPECTED_SIZE}')

    def test_every_page_without_an_override_advertises_the_fallback(self):
        """Home in four languages, the keyword hub, a filtered feed, about.

        ``?category=`` on /news/ is included because a filtered feed is the one
        most likely to be shared from a campaign.
        """
        for url in ('/', '/fr/', '/es/', '/ar/', '/stadium-lighting/',
                    '/news/?category=Industry+Insights', '/about/'):
            with self.subTest(url=url):
                resp = self.client.get(url, HTTP_HOST='localhost')
                self.assertEqual(200, resp.status_code)
                html = resp.content.decode('utf-8')
                image = self._meta(html, 'og:image')
                self.assertTrue(
                    image,
                    f'{url} has no og:image but declares '
                    'twitter:card=summary_large_image — it shares as bare text')
                self.assertEqual(
                    f'{self.ORIGIN}{self.FALLBACK}', image,
                    f'{url} og:image is not the site fallback card: {image!r}')

    def test_twitter_image_tracks_og_image_on_the_fallback_path(self):
        """``base.html`` documents that OG is the single source of truth and
        only the image hint is mirrored to twitter:*. If the fallback were added
        to one block and not the other, X would use the page's first in-body
        image while Facebook used the card."""
        html = self.client.get('/', HTTP_HOST='localhost').content.decode()
        twitter = re.search(
            r'<meta name="twitter:image" content="([^"]+)"', html)
        self.assertIsNotNone(twitter, 'home page has no twitter:image')
        self.assertEqual(
            self._meta(html, 'og:image'), twitter.group(1),
            'twitter:image and og:image must agree on the fallback path')

    def test_a_page_specific_override_still_wins_over_the_fallback(self):
        """The fallback must not become the only source of truth.

        A product page points at its own gallery shot. If the fallback ever
        shadowed that, every share on the site would show the same stadium
        card — technically non-zero, and a silent regression no "is there an
        og:image" check would catch.
        """
        from pages.views.utils import _load_seed

        slug = _load_seed()['products'][0]['slug']
        html = self.client.get(
            f'/products/{slug}/', HTTP_HOST='localhost').content.decode()
        image = self._meta(html, 'og:image')
        self.assertTrue(image, f'product page {slug} has no og:image')
        self.assertNotEqual(
            f'{self.ORIGIN}{self.FALLBACK}', image,
            f'product page {slug} og:image is shadowed by the fallback: '
            f'{image!r}')

    def test_the_template_keeps_both_arms_of_the_conditional(self):
        """Source level: ``{% if config.og_image %}`` must keep its true branch.

        The admin-configured image is the editor-controlled option. Dropping
        the true arm would leave the generator in ``scripts/make_og_default.py``
        as the only path — every assertion above would still pass and the
        ability to change the card from the admin would be gone with nothing
        failing.
        """
        src = (settings.BASE_DIR / 'templates' / 'base.html').read_text(
            encoding='utf-8')
        for block in ('og_image', 'twitter_image'):
            with self.subTest(block=block):
                # Concatenated, not %-formatted: the pattern contains `%}`
                # which %-formatting reads as a conversion specifier.
                arm = re.search(
                    r'\{% block ' + block + r' %\}(.*?)\{% endblock %\}', src,
                    re.S)
                self.assertIsNotNone(arm, f'base.html lost the {block} block')
                body = arm.group(1)
                # Assert the CONDITION itself, not merely the string
                # "config.og_image" somewhere in the block: the true arm reads
                # `{{ config.og_image.url }}`, so a substring check stays green
                # with the `{% if %}` deleted — which is exactly what mutation
                # probe E caught.
                self.assertIn(
                    '{% if config.og_image %}', body,
                    f'{block} no longer gates on config.og_image, so the '
                    'admin-configured share image is bypassed')
                self.assertIn(
                    '{% else %}', body,
                    f'{block} has no else fallback branch')
                self.assertIn(
                    'og-default.webp', body,
                    f'{block} else branch does not point at og-default.webp')
