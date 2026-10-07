"""v1.10.24 — the /stadium-lighting/ page-level FAQ + FAQPage JSON-LD.

Audit finding A6: every product page carries a FAQPage, but the keyword hub did
not. That is backwards for GEO — the hub is the page an AI engine reaches for
when it is asked "how many stadium lights do I need" or "are stadium lights OK
for broadcast", and it had no structured answer to give. The product pages only
answer the questions a buyer asks *after* choosing a product.

Two things are asserted here, and the second is the one that matters:

1. the page has a valid FAQPage whose Q&A pairs are non-empty;
2. **the JSON-LD and the visible accordion say the same thing.**

(2) is the guard that catches the realistic failure. A hand-maintained copy of
the FAQ in the template would drift from the Python constant within a week, and
a FAQPage describing answers the visitor cannot see is a structured-data lie —
the exact pattern iron law 8 exists to prevent.

Expectation sourcing (iron law 4b): the numbers checked in
``test_every_claimed_number_appears_in_the_seed`` are hardcoded product
statements, then compared against the seed. They are never read out of the FAQ
text itself.
"""
import json
import re

from django.conf import settings
from django.test import TestCase

from pages.views.views_stadium import STADIUM_FAQ


class StadiumFaqTests(TestCase):
    """The page-level FAQ exists, is valid, and matches what is rendered."""

    URL = '/stadium-lighting/'

    #: Numbers that are service promises, not product specifications, so they
    #: cannot appear in the seed's energy tables. Each entry must be traceable
    #: to copy the business already publishes: "48" is the photometric-proposal
    #: turnaround stated on every product page (``_SHARED_FAQ`` in
    #: views_products.py). Adding a figure here means pointing at where the
    #: business states it — the list is not a place to park invented numbers.
    SERVICE_PROMISE_NUMBERS = {'48'}

    def _page(self, url=None):
        resp = self.client.get(url or self.URL, HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code)
        return resp.content.decode('utf-8')

    def _jsonld_blocks(self, html):
        """All ld+json payloads, tolerating a CSP nonce on the tag (iron law 29)."""
        return re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.S)

    def _faq_page(self, html):
        for blob in self._jsonld_blocks(html):
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                continue
            if data.get('@type') == 'FAQPage':
                return data
        return None

    def test_the_page_emits_a_faqpage(self):
        """Before v1.10.24 this page had only BreadcrumbList + Organization."""
        html = self._page()
        faq = self._faq_page(html)
        self.assertIsNotNone(
            faq, '/stadium-lighting/ 没有 FAQPage JSON-LD，AI 引擎无从抽取问答')
        self.assertEqual('https://schema.org', faq['@context'])
        entities = faq.get('mainEntity') or []
        self.assertTrue(entities, 'FAQPage.mainEntity 为空')
        for item in entities:
            self.assertEqual('Question', item['@type'])
            self.assertTrue(item.get('name', '').strip(),
                            'FAQPage 里有空 question')
            answer = item.get('acceptedAnswer') or {}
            self.assertEqual('Answer', answer.get('@type'))
            self.assertTrue(answer.get('text', '').strip(),
                            f'问题 {item.get("name")!r} 没有答案文本')

    def test_the_jsonld_and_the_visible_accordion_say_the_same_thing(self):
        """The drift guard.

        The accordion is rendered from the same Python list the JSON-LD is
        built from, so the only way they can disagree is if someone hand-writes
        one of them, or removes the visible copy while leaving the structured
        data behind. That second case is the one that matters for GEO: a
        FAQPage describing answers the visitor cannot see is a structured-data
        lie, and it is invisible to any check that searches the whole page for
        a string.

        So the question is located **inside its ``<summary>``** and the answer
        **inside its ``.detail-faq-a``**, never anywhere on the page. A
        mutation probe that strips the ``<details>`` wrapper must turn this red
        even though every sentence is still present in the HTML.
        """
        html = self._page()
        faq = self._faq_page(html)
        self.assertIsNotNone(faq, 'no FAQPage to compare against')
        pairs = [
            (item['name'], item['acceptedAnswer']['text'])
            for item in faq['mainEntity']
        ]
        self.assertEqual(
            len(STADIUM_FAQ), len(pairs),
            f'FAQPage 有 {len(pairs)} 条，视图常量有 {len(STADIUM_FAQ)} 条')

        # One pass over the rendered accordion, keeping each Q&A inside its own
        # element. `<bdi>` is stripped: a tag inside the element breaks a
        # "pure text" match (iron law 13).
        rendered = [
            (
                re.sub(r'<[^>]+>', '', q).strip(),
                re.sub(r'<[^>]+>', ' ', a).strip(),
            )
            for q, a in re.findall(
                r'<summary class="detail-faq-q">(.*?)</summary>\s*'
                r'<div class="detail-faq-a">(.*?)</div>',
                html, re.S)
        ]
        self.assertEqual(
            len(pairs), len(rendered),
            f'页面上有 {len(rendered)} 组可见问答，FAQPage 有 {len(pairs)} 组')

        for question, answer in pairs:
            with self.subTest(question=question):
                visible_q = [q for q, _a in rendered if q == question]
                self.assertEqual(
                    1, len(visible_q),
                    f'FAQPage 的问题没有出现在任何一个可见 <summary> 里：'
                    f'{question!r}')
                # The answer renders through |linebreaks, so compare on a
                # distinctive leading fragment.
                head = ' '.join(answer.split()[:6])
                match = [a for _q, a in rendered
                         if ' '.join(a.split()[:6]) == head]
                self.assertEqual(
                    1, len(match),
                    f'FAQPage 的答案没有出现在对应的可见折叠块里：{head!r}')

    def test_the_accordion_is_no_js_accessible(self):
        """`<details>`/`<summary>` is the mechanism; a JS-only accordion would
        hide the answers from crawlers and from users with JS disabled."""
        html = self._page()
        count = html.count('<details class="detail-faq-item">')
        self.assertEqual(
            len(STADIUM_FAQ), count,
            f'页面渲染了 {count} 个 <details>，常量有 {len(STADIUM_FAQ)} 条')
        self.assertNotIn('faq-toggle', html,
                         'FAQ 折叠似乎改用了 JS 开关')

    def test_every_claimed_number_appears_in_the_seed(self):
        """No invented specifications, in BOTH directions.

        Direction 1 (seed → expectations): the rows the FAQ relies on must
        exist in ``energy_data`` with the values stated above.

        Direction 2 (expectations → FAQ text): every quantity the FAQ text
        itself puts a unit on must be traceable to the seed. Direction 1 alone
        is a false green — a mutation probe that changed "4200 W" to
        "99000 W" in the FAQ copy left direction 1 passing, because the seed
        was untouched. The claim lives in the prose, so the prose has to be the
        thing checked (iron law 4b: the value under test must not be the source
        of the expectation).
        """
        from pages.views.utils import _load_seed

        products = {
            p['slug']: p for p in _load_seed()['products']
            if p.get('category') == 'SPORTS_LIGHTING'
        }
        self.assertTrue(products, 'seed 里没有 SPORTS_LIGHTING 产品')

        rows = {}
        for product in products.values():
            for row in product.get('energy_data') or []:
                rows.setdefault(row['label'], set()).add(row['value'])

        expected = {
            'System Wattage': '4200W',
            'CRI': '70~95',
            'L70 Hours': '100,000',
            'IP Rating': 'IP66',
            'Surge (Common Mode / Differential Mode)': '10kV',
        }
        for label, value in expected.items():
            with self.subTest(direction='seed', label=label):
                self.assertIn(
                    label, rows,
                    f'seed energy_data 没有 {label} 这一行，FAQ 数字无从核对')
                self.assertTrue(
                    any(value in v for v in rows[label]),
                    f'{label} 在 seed 里是 {rows[label]}，FAQ 声称 {value}')

        # Direction 2. Normalise the seed into one searchable blob, then pull
        # every "<number><unit>" the FAQ asserts and require the NUMBER to
        # appear there. Units are deliberately not matched: the seed writes
        # "100,000 at 25 °C" where the FAQ writes "100,000 hours", and a unit
        # mismatch is a phrasing difference, not a false claim. The number is
        # the falsifiable part.
        seed_blob = ' '.join(
            [f'{label} {value}' for label, values in rows.items()
             for value in values]
            + [str(item) for product in products.values()
               for item in (product.get('ordering_info') or [])]
        ).replace(' ', '')

        quantity = re.compile(
            r'(\d[\d,\.]*)\s*'
            r'(kV|W|VA|°C|hours|lm/W|mm|K|Hz)\b',
            re.I)
        seen = set()
        for item in STADIUM_FAQ:
            for raw_value, unit in quantity.findall(
                    f"{item['question']} {item['answer']}"):
                number = raw_value.rstrip('.,')
                token = f'{number}{unit}'
                if token in seen:
                    continue
                seen.add(token)
                with self.subTest(direction='faq', token=token):
                    if number in self.SERVICE_PROMISE_NUMBERS:
                        continue
                    self.assertIn(
                        number, seed_blob,
                        f'FAQ 声称 {token}，但 seed 的 energy_data / '
                        'ordering_info 里找不到这个数值')

    def test_no_business_claims_we_cannot_source(self):
        """MOQ, lead time, warranty years and certification numbers are absent
        from the repo. A FAQ that invents them is worse than no FAQ: it is a
        commitment a buyer can hold us to. Same constraint the product FAQ
        documents in views_products.py."""
        banned = (
            'MOQ', 'minimum order', 'lead time', 'warranty', 'years warranty',
            'ISO 9001', 'CE certificate', 'certified', 'guarantee',
        )
        for item in STADIUM_FAQ:
            blob = f"{item['question']} {item['answer']}".lower()
            for phrase in banned:
                with self.subTest(question=item['question'], phrase=phrase):
                    self.assertNotIn(
                        phrase.lower(), blob,
                        f'FAQ 声称了仓库里没有的数据：{phrase!r}')

    def test_the_faq_answers_are_plain_strings_with_no_markup(self):
        """The blob is injected `|safe` with no escaping. A `<` in the text
        would let the constant close the script tag. Same invariant the product
        FAQ guards assert."""
        for item in STADIUM_FAQ:
            for key in ('question', 'answer'):
                with self.subTest(question=item['question'], key=key):
                    value = item[key]
                    self.assertNotIn('</script', value.lower())
                    self.assertNotIn('<', value)
                    self.assertNotIn('>', value)

    def test_the_page_still_carries_its_other_structured_data(self):
        """Adding FAQPage must not have displaced the breadcrumb chain or the
        site-wide Organization, which live in the same body."""
        html = self._page()
        types = set()
        for blob in self._jsonld_blocks(html):
            try:
                types.add(json.loads(blob).get('@type'))
            except json.JSONDecodeError:
                continue
        self.assertIn('FAQPage', types)
        self.assertIn('BreadcrumbList', types)
        self.assertIn('Organization', types)

    def test_the_css_is_scoped_to_this_page(self):
        """The FAQ rules are duplicated from product_detail.html. They must
        stay under `.stadium-faq` so no other page inherits an accordion it
        never asked for."""
        css = (settings.BASE_DIR / 'static' / 'css' / 'base.css').read_text(
            encoding='utf-8')
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        for selector in ('.detail-faq-q', '.detail-faq-a', '.detail-faq-item'):
            with self.subTest(selector=selector):
                # Every occurrence must be prefixed by the stadium scope.
                for match in re.finditer(
                        re.escape(selector) + r'\s*[,{]', css):
                    start = css.rfind('\n', 0, match.start()) + 1
                    line = css[start:match.start()]
                    self.assertIn(
                        '.stadium-faq', line,
                        f'{selector} 出现在 stadium-faq 作用域之外：{line.strip()}')
