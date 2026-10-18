"""v1.10.29 — the UL / DLC claim, pinned per product.

Why this file exists: a certification claim is a compliance statement, not
copy. UL is what a North American electrical inspection asks for; DLC is what
a utility rebate programme asks for. Advertising either on a product that does
not hold it misstates rebate eligibility, which is the expensive kind of wrong.

The tier membership below is written out literally — it is the product
decision itself, NOT imported from ``pages.utils.UL_DLC_SLUGS``. Deriving the
expectation from the implementation would make these assertions unfalsifiable.

Two tiers, because the RGBW branch holds a UL listing but is NOT DLC
qualified: claiming DLC there is the specific failure this guards against.

Assertions are scoped to the certification line element and the meta
description rather than the whole body, because the shared badge image's alt
carries the words "UL" and "DLC" on every product page regardless of what that
product actually holds (a pre-existing inaccuracy, tracked separately).
"""

import html
import json
import re

from django.test import TestCase, Client

#: Holds UL Listed AND DLC Standard.
UL_DLC_PRODUCTS = (
    'm-series', 'fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m',
    'rt410-series',
    'vsp-xxxxw-9m-yp', 'vsp-xxxxw-12m-yp',
)

#: Holds UL Listed, NOT DLC qualified.
UL_ONLY_PRODUCTS = (
    'rgb-rgbw', 'fl9m-rgbw', 'rt410-rgbw',
)

#: Holds neither.
NO_CLAIM_PRODUCTS = (
    'rt590fl-s', 'rt390fl', 'rt220ub', 'rt420fs-s',
    'rt400hb', 'rt500hb',
    'rt600sl-t', 'rt820sl-t',
    'accessory', 'mseries-gs', 'glare-shield-for-rt410',
)

CERT_LINE_RE = re.compile(r'class="detail-cert-line-value">([^<]*)<')
META_RE = re.compile(r'<meta name="description" content="([^"]*)"')
#: Iron law 29: the ld+json tag carries a CSP nonce, so the attribute scan
#: must not assume the tag looks exactly like a bare ``<script type=...>``.
LD_JSON_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


class ProductCertificationClaimTests(TestCase):
    """The visible + meta + structured-data claim, per tier."""

    def _get(self, path):
        return Client().get(path, HTTP_HOST='localhost').content.decode('utf-8')

    @staticmethod
    def _cert_line(body):
        m = CERT_LINE_RE.search(body)
        return m.group(1).strip() if m else None

    @staticmethod
    def _meta(body):
        m = META_RE.search(body)
        return html.unescape(m.group(1)) if m else ''

    @staticmethod
    def _cert_property(body):
        for block in LD_JSON_RE.findall(body):
            if '"Product"' not in block:
                continue
            try:
                data = json.loads(block)
            except ValueError:
                continue
            for prop in data.get('additionalProperty') or []:
                if prop.get('name') == 'Certification':
                    return prop.get('value')
        return None

    def test_ul_dlc_products_claim_both_listings(self):
        """The ten certified products must say so in copy, meta and JSON-LD."""
        for slug in UL_DLC_PRODUCTS:
            body = self._get('/products/%s/' % slug)
            with self.subTest(slug=slug):
                self.assertEqual(
                    self._cert_line(body),
                    'UL Listed · DLC Standard · CE · GS · IP66',
                    '%s: certification line missing or wrong' % slug)
                self.assertIn('UL Listed, DLC Standard', self._meta(body),
                              '%s: meta description drops the claim' % slug)
                self.assertEqual(
                    self._cert_property(body), 'UL Listed, DLC Standard',
                    '%s: JSON-LD Certification wrong' % slug)

    def test_rgbw_claims_ul_but_never_dlc(self):
        """The compliance-critical one: DLC is a rebate-eligibility claim.

        These three hold a UL listing and nothing else, so the word "DLC" must
        not reach the visible line, the meta description or the structured
        data.
        """
        for slug in UL_ONLY_PRODUCTS:
            body = self._get('/products/%s/' % slug)
            line = self._cert_line(body)
            meta = self._meta(body)
            with self.subTest(slug=slug):
                self.assertEqual(
                    line, 'UL Listed · CE · GS · IP66',
                    '%s: expected the UL-only line, got %r' % (slug, line))
                self.assertNotIn('DLC', line,
                                 '%s claims DLC it does not hold' % slug)
                self.assertIn('UL Listed', meta, '%s: meta drops UL' % slug)
                self.assertNotIn('DLC', meta,
                                 '%s: meta claims DLC it does not hold' % slug)
                self.assertEqual(self._cert_property(body), 'UL Listed')

    def test_products_without_a_listing_claim_none(self):
        """Eleven products hold neither listing and must not say otherwise."""
        for slug in NO_CLAIM_PRODUCTS:
            body = self._get('/products/%s/' % slug)
            meta = self._meta(body)
            with self.subTest(slug=slug):
                self.assertIsNone(
                    self._cert_line(body),
                    '%s renders a certification line it has not earned' % slug)
                self.assertNotIn('UL Listed', meta, '%s: meta claims UL' % slug)
                self.assertNotIn('DLC', meta, '%s: meta claims DLC' % slug)
                self.assertIsNone(
                    self._cert_property(body),
                    '%s advertises a Certification property' % slug)

    def test_the_claim_is_english_only(self):
        """UL and DLC are North American; the other five locales must not carry them."""
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            body = self._get('/%s/products/fl6m/' % lang)
            with self.subTest(lang=lang):
                self.assertIsNone(
                    self._cert_line(body),
                    '%s page carries the English-only certification line' % lang)
                self.assertIsNone(
                    self._cert_property(body),
                    '%s JSON-LD carries a Certification property' % lang)


class LandingFaqCertificationQuestionTests(TestCase):
    """The three North American keyword hubs answer the certification question."""

    def test_each_landing_faq_asks_about_ul_and_dlc(self):
        from pages.views.views_projects import FOOTBALL_FAQ, TENNIS_FAQ
        from pages.views.views_stadium import STADIUM_FAQ

        for name, faq in (('stadium', STADIUM_FAQ),
                          ('football', FOOTBALL_FAQ),
                          ('tennis', TENNIS_FAQ)):
            with self.subTest(page=name):
                joined = ' '.join(
                    (item.get('question', '') + ' ' + item.get('answer', ''))
                    for item in faq)
                self.assertIn('UL', joined, '%s FAQ never mentions UL' % name)
                self.assertIn('DLC', joined, '%s FAQ never mentions DLC' % name)
                # Every entry must still be a well-formed pair: an earlier
                # patch left an orphan ``{}`` in these lists and silently
                # dropped a question.
                for item in faq:
                    self.assertTrue(item.get('question'), '%s: empty Q' % name)
                    self.assertTrue(item.get('answer'), '%s: empty A' % name)
