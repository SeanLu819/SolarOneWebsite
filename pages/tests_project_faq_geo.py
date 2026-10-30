"""GEO (2026-10-30, A): the quotable sentence + FAQPage on every project page.

Why this guard exists
---------------------
The GEO baseline measured on 2026-10-23 found the site had **no first-party
source an AI answer could cite**: brand intent was answered 100% of the time,
but ``spec`` intent scored 0% and ``local`` 33%, because no page stated a
complete, self-contained fact. The project pages carry the strongest facts on
the site — measured lux, uniformity, the standard met, the venue, the place —
and none of it was in a form an answer could lift.

So each project page now carries two things, both built in the view from data
the page already states:

1. one citable sentence (brand + venue + place + measured number), rendered
   visibly and mirrored into the Article's ``abstract``;
2. a FAQPage (2-3 Q&A) whose pairs drop out when their data is missing.

Four ways that can rot, which is what the four tests below pin:

* the FAQPage disappears (or is emitted twice) -> test 1;
* the structured data drifts from the visible accordion -> test 1/3;
* the frames silently fall back to English on the five non-English sites,
  which is exactly the bug the stadium-landing FAQ already had -> test 2;
* someone adds canned boilerplate that the project's own data does not
  support -> test 3 counts the pairs the data can actually justify.

Every expectation is derived from ``_load_seed()`` or from the view's own
context — nothing here is a hardcoded project count or a copied string, so the
guard cannot go green by accident after a content change.
"""
import html
import json
import re

from django.test import TestCase
from django.utils.translation import activate

from pages.views.utils import _load_seed

#: English has no language prefix; the other five do (i18n_patterns with
#: prefix_default_language=False).
LANGS = ('en', 'de', 'fr', 'es', 'ru', 'ar')

#: Rendering all 22 projects in all six languages is 132 page renders for a
#: guard that only needs to prove the *per-language* behaviour once. English
#: covers every project; the other five cover a sample.
NON_EN_SAMPLE = 3

_SCRIPT_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
_DETAILS_RE = re.compile(r'<details[^>]*>(.*?)</details>', re.S)
_SUMMARY_RE = re.compile(r'<summary[^>]*>(.*?)</summary>', re.S)
_ANSWER_RE = re.compile(r'<div class="detail-faq-a">(.*?)</div>\s*</details>', re.S)
_CITABLE_RE = re.compile(r'<p class="project-citable">(.*?)</p>', re.S)
_TAG_RE = re.compile(r'<[^>]+>')


def _text(fragment):
    """Visible text of a markup fragment: tags off, entities decoded."""
    return html.unescape(_TAG_RE.sub('', fragment)).strip()


def _blocks(page):
    """Every ld+json payload, tolerating a CSP nonce on the tag (iron law 29)."""
    out = []
    for raw in _SCRIPT_RE.findall(page):
        try:
            out.append(json.loads(raw))
        except ValueError:
            out.append({'_unparsable': raw})
    return out


def _seed_projects():
    return [p for p in _load_seed().get('projects', []) if p.get('slug')]


def _localised(project, field, lang):
    """The seed value a visitor of ``lang`` should see for ``field``."""
    if lang == 'en':
        return (project.get(field) or '').strip()
    tr = (project.get('translations') or {}).get(lang) or {}
    return (tr.get(field) or project.get(field) or '').strip()


def _frame(text, title, location=None):
    """The gettext frame of ``text``: everything that is NOT project data.

    Comparing whole sentences across languages proves nothing — the venue name
    and the place change per language too, so an untranslated frame hides
    inside a sentence that still looks different. Splitting the localised
    values out leaves only the words the translator owns, which is the thing
    that silently falls back to English.
    """
    head, _, tail = text.partition(title)
    if location:
        tail = tail.split(location, 1)[0]
    return (head.strip() + ' | ' + tail.strip()).strip()


class ProjectFaqGeoTests(TestCase):
    """The FAQPage and the citable sentence exist, match, and are localised."""

    def _page(self, slug, lang):
        activate(lang)
        path = '/projects/%s/' % slug if lang == 'en' else '/%s/projects/%s/' % (lang, slug)
        resp = self.client.get(path, HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code, '%s %s did not render' % (lang, slug))
        return resp

    def test_every_project_emits_one_faqpage_matching_the_visible_accordion(self):
        """A FAQPage describing answers the visitor cannot read is a
        structured-data lie — so every pair is checked against the accordion."""
        checked = 0
        for project in _seed_projects():
            resp = self._page(project['slug'], 'en')
            page = resp.content.decode('utf-8')

            faqs = [b for b in _blocks(page) if b.get('@type') == 'FAQPage']
            self.assertEqual(1, len(faqs),
                             '%s: expected exactly 1 FAQPage, found %d'
                             % (project['slug'], len(faqs)))
            self.assertTrue(
                faqs[0].get('@id', '').endswith('#faq'),
                '%s: FAQPage has no page-level @id' % project['slug'])

            pairs = [(q['name'], q['acceptedAnswer']['text'])
                     for q in faqs[0]['mainEntity']]
            self.assertGreaterEqual(
                len(pairs), 2, '%s: FAQPage has too few pairs' % project['slug'])
            for question, answer in pairs:
                self.assertTrue(question.strip(), '%s: empty question' % project['slug'])
                self.assertTrue(answer.strip(), '%s: empty answer' % project['slug'])

            # The visible accordion must carry the same pairs, in order.
            visible = []
            for block in _DETAILS_RE.findall(page):
                q = _SUMMARY_RE.search(block)
                a = _ANSWER_RE.search(block) or re.search(
                    r'<div class="detail-faq-a">(.*?)</div>', block, re.S)
                self.assertIsNotNone(q, '%s: a <details> has no <summary>' % project['slug'])
                visible.append((_text(q.group(1)), _text(a.group(1)) if a else ''))
            self.assertEqual(
                len(pairs), len(visible),
                '%s: %d pairs in JSON-LD, %d visible' % (project['slug'], len(pairs), len(visible)))
            for (jq, ja), (vq, va) in zip(pairs, visible):
                self.assertEqual(jq, vq, '%s: question drifted: %r' % (project['slug'], jq))
                self.assertIn(ja[:40], va,
                              '%s: answer %r is not visible' % (project['slug'], ja[:40]))
            checked += 1
        self.assertGreaterEqual(checked, 10, 'guard is vacuous: no project checked')

    def test_citable_sentence_is_visible_and_mirrored_into_the_article(self):
        """The sentence is the unit an AI answer lifts: it must be readable on
        the page (not JSON-LD only) and must carry the venue and the place."""
        for project in _seed_projects()[:8]:
            resp = self._page(project['slug'], 'en')
            page = resp.content.decode('utf-8')

            rendered = _CITABLE_RE.findall(page)
            self.assertEqual(1, len(rendered),
                             '%s: expected exactly one citable sentence' % project['slug'])
            sentence = _text(rendered[0])
            self.assertTrue(sentence.endswith('.'),
                            '%s: lead sentence does not read as a sentence: %r'
                            % (project['slug'], sentence))

            title = (project.get('title') or '').strip()
            location = (project.get('location') or '').strip()
            self.assertIn(title, sentence, '%s: lead omits the venue name' % project['slug'])
            self.assertIn(location, sentence, '%s: lead omits the place' % project['slug'])
            self.assertIn('SolarOne', sentence, '%s: lead omits the brand' % project['slug'])

            articles = [b for b in _blocks(page) if b.get('@type') == 'Article']
            self.assertEqual(1, len(articles), '%s: no Article block' % project['slug'])
            self.assertEqual(
                sentence, (articles[0].get('abstract') or '').strip(),
                '%s: Article.abstract drifted from the visible sentence' % project['slug'])

    def test_pairs_are_justified_by_the_project_data(self):
        """Boilerplate guard: the pair count must equal what this project's own
        data can support — venue always, results when measured, luminaires when
        linked. A canned fourth pair fails here."""
        for project in _seed_projects()[:8]:
            resp = self._page(project['slug'], 'en')
            faq_items = resp.context['faq_items']
            related = resp.context['related_products'] or []
            names = [p for p in related if (getattr(p, 'name_t', '') or '').strip()]

            expected = 1 + (1 if (project.get('results') or '').strip() else 0) + (1 if names else 0)
            self.assertEqual(
                expected, len(faq_items),
                '%s: %d FAQ pairs for %d justified ones' % (project['slug'], len(faq_items), expected))

            blocks = [b for b in _blocks(resp.content.decode('utf-8'))
                      if b.get('@type') == 'FAQPage']
            self.assertEqual(
                len(faq_items), len(blocks[0]['mainEntity']),
                '%s: JSON-LD and visible FAQ disagree' % project['slug'])

    def test_frames_are_localised_not_english_fallbacks(self):
        """The stadium-landing bug, pinned here: a frame that gettext cannot
        resolve comes back as English and every non-English project page reads
        as a translation gap. Proves the localiser ran, per language."""
        sample = [p['slug'] for p in _seed_projects()[:NON_EN_SAMPLE]]
        for slug in sample:
            project = next(p for p in _seed_projects() if p['slug'] == slug)
            en = self._page(slug, 'en')
            en_title = (project.get('title') or '').strip()
            en_location = (project.get('location') or '').strip()
            en_sentence = _text(_CITABLE_RE.findall(en.content.decode('utf-8'))[0])
            en_faq = [(q['question'], q['answer']) for q in en.context['faq_items']]

            for lang in LANGS[1:]:
                title = _localised(project, 'title', lang)
                location = _localised(project, 'location', lang)
                other = self._page(slug, lang)
                sentence = _text(_CITABLE_RE.findall(other.content.decode('utf-8'))[0])

                # The venue name and place must be the visitor's language too —
                # an English venue name inside a translated frame is the same
                # gap one level down.
                self.assertIn(title, sentence,
                              '%s/%s: venue name not localised in the lead' % (lang, slug))

                self.assertNotEqual(
                    _frame(en_sentence, en_title, en_location),
                    _frame(sentence, title, location),
                    '%s/%s: citable sentence frame is still English' % (lang, slug))

                faq = [(q['question'], q['answer']) for q in other.context['faq_items']]
                self.assertEqual(len(en_faq), len(faq),
                                 '%s/%s: FAQ length differs from English' % (lang, slug))
                for i, ((en_q, en_a), (q, a)) in enumerate(zip(en_faq, faq)):
                    self.assertNotEqual(
                        _frame(en_q, en_title), _frame(q, title),
                        '%s/%s: FAQ question %d is still English' % (lang, slug, i))
                    self.assertNotEqual(
                        _frame(en_a, en_title, en_location), _frame(a, title, location),
                        '%s/%s: FAQ answer %d is still English' % (lang, slug, i))

    def test_faqpage_is_built_in_python_not_concatenated_in_the_template(self):
        """JSON-LD iron law: the blob is dumped in the view and injected whole.
        A template-built block is one stray comma away from invalid JSON that
        Google and every AI crawler read as nothing."""
        from django.conf import settings

        template = (settings.BASE_DIR / 'templates' / 'project_detail.html').read_text(
            encoding='utf-8')
        self.assertIn('{{ faq_json|safe }}', template)
        self.assertEqual(1, template.count('{{ faq_json|safe }}'))

        script = re.search(
            r'<script[^>]*application/ld\+json[^>]*>\s*\{\{ faq_json\|safe \}\}\s*</script>',
            template)
        self.assertIsNotNone(script, 'FAQPage script tag changed shape')
        self.assertNotIn('{% for', script.group(0),
                         'FAQPage must not be assembled inside the template')

        view = (settings.BASE_DIR / 'pages' / 'views' / 'views_projects.py').read_text(
            encoding='utf-8')
        self.assertIn('build_product_faq_jsonld(', view)
        self.assertIn('json.dumps(', view)
