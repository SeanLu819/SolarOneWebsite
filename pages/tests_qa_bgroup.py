"""Independent QA verification for the B-group SEO/GEO changes (B1–B4).

These tests are written by the QA engineer to *independently* verify the
engineer's four changes — not to trust the engineer's own test classes. They
focus on the gaps the engineer's tests leave open:

* B3 — content fact-check of the 6 FAQ entries (no invented business data),
       A-group JSON-LD iron-law compliance at the template level, visible
       ``<summary>`` markup, and an encoding/XSS adversarial probe.
* B4 — RFC-822 ``pubDate`` actually parses via ``email.utils.parsedate_to_datetime``,
       the XML-escape channel proven end-to-end with adversarial ``& < "`` content,
       ``news_feed`` exported from the ``pages.views`` package, and route-order
       non-collision vs ``news/<slug>/``.
* B1 — build.sh publishes ``public/llms.txt`` after ``public/`` exists, syntax OK.
* B2 — /robots.txt exposes the 6 AI-crawler Allow blocks and keeps canonical URLs.

Every page request passes ``HTTP_HOST='localhost'`` (DEBUG=False + ALLOWED_HOSTS
would otherwise answer 400).
"""

import json
import os
import re
import subprocess
import email.utils
from unittest import mock

import xml.etree.ElementTree as ET
from django.conf import settings
from django.template import Template, Context
from django.test import TestCase
from django.urls import resolve

# Import-time check: news_feed MUST be re-exported by the views package,
# otherwise the URL route raises AttributeError at request time.
from pages.views import news_feed as _news_feed_from_pkg  # noqa: F401
from pages.views.views_other import news_feed as _news_feed_from_mod  # noqa: F401
from pages.views.views_products import PRODUCT_FAQ, build_product_faq_jsonld


JSONLD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
TEMPLATE_DIR = settings.BASE_DIR / 'templates'


def _read_template(name):
    return (TEMPLATE_DIR / name).read_text(encoding='utf-8')


def _faqpage_block(path_html):
    """Return the parsed FAQPage dict from a rendered page's HTML."""
    for raw in JSONLD_RE.finditer(path_html):
        obj = json.loads(raw.group(1))
        types = set()
        if '@graph' in obj:
            types |= {n.get('@type') for n in obj.get('@graph', [])}
        else:
            types.add(obj.get('@type'))
        if 'FAQPage' in types:
            return obj
    return None


# ---------------------------------------------------------------------------
# B1 — build.sh copies repo-root llm.txt to BOTH /llm.txt and /llms.txt
# ---------------------------------------------------------------------------
class BuildScriptLlmsTxtTests(TestCase):
    """B1: /llms.txt must ship, and only after ./public exists."""

    def test_llms_txt_copy_line_present_and_ordered(self):
        build_sh = (settings.BASE_DIR / 'build.sh').read_text(encoding='utf-8')
        lines = build_sh.splitlines()

        cp_idx = next(
            (i for i, ln in enumerate(lines) if ln.strip() == 'cp llm.txt public/llms.txt'),
            None,
        )
        self.assertIsNotNone(cp_idx, 'build.sh missing `cp llm.txt public/llms.txt`')

        # public/ must be (re)created before the copy, so the file is not lost.
        mkdir_idx = next(
            (i for i, ln in enumerate(lines) if ln.strip() == 'mkdir -p public'), None)
        rm_idx = next(
            (i for i, ln in enumerate(lines) if ln.strip() == 'rm -rf public'), None)
        self.assertIsNotNone(mkdir_idx, 'build.sh missing `mkdir -p public`')
        self.assertIsNotNone(rm_idx, 'build.sh missing `rm -rf public`')
        self.assertLess(rm_idx, cp_idx, '`rm -rf public` must precede the copy')
        self.assertLess(mkdir_idx, cp_idx, '`mkdir -p public` must precede the copy')

        # And it must live inside the `if [ -f llm.txt ]` guard so a missing
        # source never 404s silently.
        guarded = any('if [ -f llm.txt ]' in ln for ln in lines[:cp_idx])
        self.assertTrue(guarded, 'llms.txt copy is not guarded by `if [ -f llm.txt ]`')

    def test_build_sh_syntax_valid(self):
        rc = subprocess.run(
            ['bash', '-n', str(settings.BASE_DIR / 'build.sh')],
            capture_output=True, text=True,
        ).returncode
        self.assertEqual(rc, 0, 'build.sh has a bash syntax error')


# ---------------------------------------------------------------------------
# B2 — robots.txt explicitly allows the major AI crawlers
# ---------------------------------------------------------------------------
class RobotsTxtAiCrawlerTests(TestCase):
    """B2: six AI-crawler UA Allow blocks + preserved canonical directives."""

    AI_UA = [
        'GPTBot', 'OAI-SearchBot', 'ClaudeBot',
        'PerplexityBot', 'Google-Extended', 'Applebot-Extended',
    ]

    def test_robots_txt_allows_six_ai_crawlers(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        for ua in self.AI_UA:
            # Each UA must have a `User-agent:` line AND a following `Allow: /`.
            self.assertIn(f'User-agent: {ua}', content,
                          f'robots.txt missing User-agent: {ua}')
            # The Allow must sit immediately after its UA (no stray Disallow).
            ua_block = content.split(f'User-agent: {ua}', 1)[1].split(
                'User-agent:', 1)[0]
            self.assertIn('Allow: /', ua_block,
                          f'{ua} block missing `Allow: /`')

    def test_robots_txt_preserves_sitemap_llmtxt_feed_and_canonical(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='localhost')
        content = resp.content.decode('utf-8')
        origin = settings.CANONICAL_ORIGIN

        self.assertIn(f'Sitemap: {origin}/sitemap.xml', content)
        self.assertIn(f'LLM-Txt: {origin}/llm.txt', content)
        self.assertIn(f'Feed: {origin}/news/feed.xml', content)
        # No leaked template placeholder.
        self.assertNotIn('{{', content)
        self.assertNotIn('localhost', content)

    def test_robots_txt_notes_cloudflare_ai_crawl_control(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='localhost')
        content = resp.content.decode('utf-8').lower()
        self.assertTrue(
            'cloudflare' in content and 'ai crawl control' in content,
            'robots.txt must note the real blocker is Cloudflare AI Crawl Control')


# ---------------------------------------------------------------------------
# B3 — product FAQPage JSON-LD + visible FAQ section
# ---------------------------------------------------------------------------
class ProductFaqQaVerificationTests(TestCase):
    """B3 independent verification: content, iron law, visible markup, encoding."""

    PATHS = ('/products/fl6m/', '/products/m-series/')

    # Confirmed product facts that MUST appear somewhere in the 6 FAQ entries.
    EXPECTED_FACTS = [
        'flicker', 'vsp',                 # #1 flicker-free broadcast, VSP drivers
        'dialux', '48 hours',             # #2 DIALux study within 48h
        '130 lm/w', 'l70', '100,000 hours',  # #3 efficacy + L70 lifespan
        'ip66', '10 kv', '°c',            # #4 IP66 / 10kV / temp range
        '50%', 'hid',                     # #5 >=50% saving vs HID/metal-halide
        'm series', '1280 w', '80 w',     # #6 M Series 80–1280W modular
    ]

    # Business data the engineer must NOT have invented (absent from repo).
    FORBIDDEN_FACTS = [
        'moq', 'lead time', 'warranty', 'certification',
        'rohs', 'iso 9001', 'ce certified',
    ]

    def _rendered(self, path):
        resp = self.client.get(path, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200, f'{path} did not render')
        return resp.content.decode('utf-8')

    def test_faq_content_matches_confirmed_facts_and_has_no_fabricated_data(self):
        for path in self.PATHS:
            html = self._rendered(path)
            faq = _faqpage_block(html)
            self.assertIsNotNone(faq, f'{path}: no FAQPage block found')

            # Concatenate every question + acceptedAnswer text.
            blob = ' '.join(
                f"{item.get('name', '')} {item.get('acceptedAnswer', {}).get('text', '')}"
                for item in faq.get('mainEntity', [])
            ).lower()

            for fact in self.EXPECTED_FACTS:
                self.assertIn(
                    fact, blob,
                    f'{path}: expected FAQ fact {fact!r} missing from JSON-LD')
            for forbidden in self.FORBIDDEN_FACTS:
                self.assertNotIn(
                    forbidden, blob,
                    f'{path}: FAQ JSON-LD contains fabricated business data '
                    f'{forbidden!r}')

    def test_faqpage_block_complies_with_jsonld_iron_law(self):
        """A-group iron law: FAQPage is built in Python and injected `|safe`;
        the template block must NOT concatenate a JSON array by hand."""
        for name in ('product_detail.html', 'product_overview.html'):
            src = _read_template(name)
            blocks = JSONLD_RE.findall(src)
            faq_blocks = [b for b in blocks if 'product_faq_json' in b]
            self.assertEqual(
                len(faq_blocks), 1,
                f'{name}: expected exactly 1 FAQPage JSON-LD script block')
            faq_block = faq_blocks[0]
            # Whole blob injected safe — no template-side JSON construction.
            self.assertIn('product_faq_json|safe', faq_block)
            # No hand-written `{% if %},` trailing-comma pattern inside the block.
            self.assertNotIn('{%', faq_block,
                             f'{name}: FAQPage block must not template-concatenate')

    def test_faq_visible_section_has_six_summaries_and_visible_answers(self):
        for path in self.PATHS:
            html = self._rendered(path)
            self.assertIn('class="detail-faq"', html)
            self.assertEqual(
                html.count('<details'), 6,
                f'{path}: expected 6 <details>, got {html.count("<details")}')
            self.assertEqual(
                html.count('<summary'), 6,
                f'{path}: expected 6 <summary>, got {html.count("<summary")}')
            # Answers are server-rendered (visible without JS): a known answer
            # fragment must appear in the page HTML.
            self.assertIn('VSP high-frequency', html,
                          f'{path}: FAQ answer text not visible in HTML')
            # Summary text must match the JSON-LD question (spot check #1).
            self.assertIn(
                'Are SolarOne stadium lights flicker-free for broadcast?', html,
                f'{path}: first FAQ <summary> does not match JSON-LD question')

    def test_faq_constants_contain_no_script_breaking_chars(self):
        """Because the FAQPage blob is injected `|safe`, the constant text must
        never contain a literal that would terminate the <script> tag."""
        for entry in PRODUCT_FAQ:
            text = (entry['question'] + entry['answer']).lower()
            self.assertNotIn('</script', text,
                             f'PRODUCT_FAQ entry contains </script: unsafe with |safe')

    def test_faq_encoding_adversarial_json_roundtrip(self):
        """If FAQ text ever held a double-quote, backslash, or ``<``/``</script>``,
        json.dumps + json.loads must still round-trip without corruption
        (the injection channel is safe)."""
        adv = [{
            'question': 'Adversarial "double" \\back <tag> &amp;',
            'answer': 'Reply </script><b> "x" \\y & z',
        }]
        blob = json.dumps(build_product_faq_jsonld(adv), ensure_ascii=False)
        parsed = json.loads(blob)  # must not raise
        got = parsed['mainEntity'][0]['acceptedAnswer']['text']
        self.assertEqual(got, adv[0]['answer'])

    def test_faq_visible_channel_autoescapes_xss(self):
        """The visible FAQ region interpolates `{{ faq.* }}` WITHOUT `|safe`,
        so Django autoescaping must neutralise injected markup."""
        out = Template('{{ x }}').render(Context(
            {'x': '<script>alert(1)</script>'}))
        self.assertNotIn('<script>alert(1)</script>', out)
        self.assertIn('&lt;script&gt;', out)


# ---------------------------------------------------------------------------
# B4 — RSS 2.0 news feed
# ---------------------------------------------------------------------------
class NewsFeedQaVerificationTests(TestCase):
    """B4 independent verification: RFC-822 parse, XML-escape, export, routes."""

    def _feed_root(self):
        resp = self.client.get('/news/feed.xml', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('rss+xml', resp['Content-Type'])
        return resp, ET.fromstring(resp.content.decode('utf-8'))

    def test_feed_pubdate_is_rfc822_and_parses(self):
        _, root = self._feed_root()
        pub = root.find('channel').find('item').find('pubDate').text
        dt = email.utils.parsedate_to_datetime(pub)  # must not raise
        self.assertIsNotNone(dt)
        self.assertEqual((dt.year, dt.month, dt.day), (2026, 9, 25))
        # Valid RFC-822 UTC timezone token: either the literal ``GMT`` emitted
        # by email.utils.format_datetime(usegmt=True) or the ``+0000`` form.
        self.assertTrue(
            pub.rstrip().endswith(('GMT', '+0000')),
            f'pubDate UTC token not GMT/+0000: {pub!r}')

    def test_feed_xml_escape_channel_with_adversarial_news(self):
        """Prove the xml.sax.saxutils.escape channel end-to-end: an item whose
        title/description carry & < " must still yield valid, parseable XML and
        round-trip back to the original text."""
        adv_seed = {
            'news': [{
                'slug': 'adv-1',
                'title': 'A & B <c> "d"',
                'summary': '<b> bold & more',
                'published_at': '2026-01-01T00:00:00+00:00',
                'is_published': True,
            }],
        }
        with mock.patch('pages.views.views_other._load_seed',
                        return_value=adv_seed):
            resp = self.client.get('/news/feed.xml', HTTP_HOST='localhost')
            content = resp.content.decode('utf-8')
            root = ET.fromstring(content)  # must parse despite special chars
            item = root.find('channel').find('item')
            self.assertEqual(item.find('title').text, 'A & B <c> "d"')
            self.assertEqual(item.find('description').text, '<b> bold & more')
            # Raw wire form must be escaped, not raw. Note: xml.sax.saxutils.escape
            # escapes &, <, > by design; a literal " in element content is valid
            # XML (ElementTree above parsed it back to the original), so we do
            # NOT require &quot; here.
            self.assertIn('&amp;', content)
            self.assertIn('&lt;', content)
            self.assertIn('&gt;', content)

    def test_news_feed_exported_and_route_order_ok(self):
        # Imported at module top; identical object proves the package re-export.
        self.assertIs(_news_feed_from_pkg, _news_feed_from_mod)

        # /news/feed.xml resolves to news_feed and does NOT collide with
        # news/<slug:slug>/ (slug converter rejects the dot in feed.xml anyway).
        self.assertIs(resolve('/news/feed.xml').func, _news_feed_from_mod)
        self.assertEqual(resolve('/news/feed.xml').url_name, 'news_feed')
        self.assertEqual(resolve('/news/some-slug/').url_name, 'news_detail')
