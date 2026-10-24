"""Guards for release metadata that lives outside the database.

`VERSION` (repo root), `settings.APP_VERSION` (admin header) and the version
string quoted in `llm.txt` previously drifted apart after a bump, so this
module pins all three together and keeps the AI-facing summary in sync with the
landing pages shipped in v1.9.0.
"""
import json
import os
import re

from django.conf import settings
from django.test import Client, TestCase

REPO_ROOT = settings.BASE_DIR
PROJECT_COLLECTION_PAGES = (
    '/projects/football/',
    '/projects/tennis/',
)


def _read(*parts):
    with open(os.path.join(REPO_ROOT, *parts), encoding='utf-8') as handle:
        return handle.read()


class ReleaseMetadataConsistencyTests(TestCase):
    """The three version strings must never diverge again."""

    def test_version_file_matches_app_version(self):
        # The VERSION file carries a leading "v" while APP_VERSION does not
        # (admin headers add their own "v"), so normalise before comparing.
        self.assertEqual(_read('VERSION').strip().lstrip('vV'), settings.APP_VERSION)

    def test_app_version_follows_semver(self):
        self.assertRegex(settings.APP_VERSION, r'^\d+\.\d+\.\d+$')

    def test_llm_txt_declares_the_same_version(self):
        self.assertIn(f'Site version v{settings.APP_VERSION}', _read('llm.txt'))

    def test_llm_txt_lists_the_project_collection_pages(self):
        text = _read('llm.txt')
        for path in PROJECT_COLLECTION_PAGES:
            self.assertIn(path, text)


class LlmTxtLocaleVariantTests(TestCase):
    """Per-locale `llm.txt` variants (GEO regionalisation, v1.10.36).

    A crawler that lands on `/llm.txt` only ever reads English, so an AI asked
    "أفضل إضاءة ملاعب" has no native-language SolarOne text to quote. The
    variants fix that. These guards stop the variant from silently rotting into
    an English file with an Arabic heading, or losing figures in translation.
    """

    VARIANT = 'llm.ar.txt'
    # Measured figures an Arabic reader is most likely to ask about. Derived
    # from the English "Measured results" block, not hardcoded independently.
    MEASURED_FIGURES = ('2200', '3200', '2600', '4000', '1.37', '1.56', '1.67')

    def _ar(self):
        return _read(self.VARIANT)

    def test_variant_exists_and_is_not_empty(self):
        self.assertTrue(self._ar().strip())

    def test_variant_body_is_actually_arabic(self):
        """Catches an English file shipped under an Arabic filename."""
        text = self._ar()
        arabic = sum(1 for ch in text if '\u0600' <= ch <= '\u06ff')
        letters = sum(1 for ch in text if ch.isalpha())
        self.assertGreater(letters, 0)
        # Latin stays for URLs, model codes and the brand name, so Arabic need
        # only dominate — 0.5 is the "is this really Arabic" line, not a quota.
        self.assertGreater(arabic / letters, 0.5,
                           'llm.ar.txt is not predominantly Arabic script')

    def test_no_cjk_contamination(self):
        """Two stray Chinese conjunctions shipped in the first draft once."""
        cjk = [ch for ch in self._ar() if '\u4e00' <= ch <= '\u9fff']
        self.assertEqual(cjk, [], f'CJK characters in {self.VARIANT}: {cjk}')

    def test_brand_name_is_never_transliterated(self):
        for text in (_read('llm.txt'), self._ar()):
            self.assertIn('SolarOne', text)
        self.assertNotIn('\u0633\u0648\u0644\u0627\u0631', self._ar(),
                         'brand name must stay "SolarOne", never transliterated')

    def test_disambiguation_entities_carried_over(self):
        text = self._ar()
        for entity in ('SolarOne Solutions', 'Fonroche'):
            self.assertIn(entity, text)
        # The heading must be localised too, not just the entity names.
        self.assertIn('\u0644\u0627 \u064a\u0646\u0628\u063a\u064a \u0627\u0644\u062e\u0644\u0637', text)

    def test_section_count_parity_with_english(self):
        en = len(re.findall(r'^## ', _read('llm.txt'), re.M))
        ar = len(re.findall(r'^## ', self._ar(), re.M))
        self.assertEqual(ar, en, 'variant lost (or gained) a section')

    def test_faq_count_parity_with_english(self):
        en = len(re.findall(r'\*\*[^*]+\?\*\*', _read('llm.txt')))
        ar = len(re.findall(r'\*\*[^*]+\u061f\*\*', self._ar()))
        self.assertEqual(en, ar)
        self.assertGreaterEqual(en, 1)

    def test_measured_figures_survive_translation(self):
        text = self._ar()
        for figure in self.MEASURED_FIGURES:
            self.assertIn(figure, text, f'figure {figure} missing from variant')

    def test_variant_cites_localised_urls(self):
        text = self._ar()
        for path in ('/ar/products/', '/ar/projects/', '/ar/about/'):
            self.assertIn(path, text)

    def test_variant_points_back_to_english_as_canonical(self):
        self.assertIn('/llm.txt', self._ar())

    def test_english_variant_advertises_the_locale_variant(self):
        """A crawler landing on /llm.txt must be able to discover /llm.ar.txt."""
        self.assertIn('/llm.ar.txt', _read('llm.txt'))

    def test_build_sh_publishes_locale_variants(self):
        build = _read('build.sh')
        self.assertIn('public/llm.$L.txt', build)
        self.assertIn('for L in ar; do', build)


class LlmTxtClimateSpecTests(TestCase):
    """Hot-climate ratings in llm.txt must come from the published specs.

    The Gulf/Arabic variant exists to answer "will this survive 50 °C and
    sand?", so those two numbers are the ones a buyer will hold us to. This
    pins them to `seed_data.json` — if a product spec changes, the summary must
    change with it — and blocks the inverse failure: claiming a certification
    we do not hold, which is the same class of error as mis-stating DLC.
    """

    CLIMATE_HEADING = 'High-ambient, dusty and coastal operation'
    CLIMATE_HEADING_AR = (
        '\u0627\u0644\u062a\u0634\u063a\u064a\u0644 \u0641\u064a '            # التشغيل في
        '\u062f\u0631\u062c\u0627\u062a \u0627\u0644\u062d\u0631\u0627\u0631\u0629 '  # درجات الحرارة
        '\u0627\u0644\u0645\u0631\u062a\u0641\u0639\u0629 '                    # المرتفعة
        '\u0648\u0627\u0644\u063a\u0628\u0627\u0631 '                          # والغبار
        '\u0648\u0627\u0644\u0623\u062c\u0648\u0627\u0621 '                    # والأجواء
        '\u0627\u0644\u0633\u0627\u062d\u0644\u064a\u0629')                    # الساحلية

    # Positive claims we must never make: no salt-spray hours and no SASO /
    # G-Mark certification exist in the product data (verified 2026-10-22).
    FORBIDDEN_CLAIMS = (
        'salt spray tested', 'salt-spray tested', 'passed salt spray',
        'SASO certified', 'SASO-certified', 'certified to SASO',
        'G-Mark certified', 'certified to G-Mark',
        'FIFA certified', 'FIFA-certified', 'FIFA approved',
        'FIFA compliant', 'FIFA-compliant', 'meets FIFA',
        'compliant with FIFA', 'certified to FIFA',
    )

    @staticmethod
    def _seed_products():
        with open(os.path.join(REPO_ROOT, 'seed_data.json'),
                  encoding='utf-8') as handle:
            return json.load(handle).get('products') or []

    def _spec_values(self, label):
        """Every distinct published value for one spec label."""
        values = {item.get('value')
                  for product in self._seed_products()
                  for item in (product.get('energy_data') or [])
                  if item.get('label') == label}
        values.discard(None)
        return values

    @staticmethod
    def _section(text, heading):
        """Just the body of one `##` section.

        Whole-file assertions are useless here: '55\u00b0C' and 'IP66' also
        appear in the sports-lighting summary, so a drifted climate section
        would be masked by an unrelated mention. (Found by mutation probe.)
        """
        match = re.search(r'^## %s$(.*?)(?=^## |\Z)' % re.escape(heading),
                          text, re.M | re.S)
        assert match is not None, 'section %r not found' % heading
        return match.group(1)

    def test_ambient_rating_matches_published_specs(self):
        ranges = self._spec_values('Operating Temperature Range')
        self.assertEqual(len(ranges), 1,
                         'ambiguous operating temperature in seed_data.json')
        declared = ranges.pop()                    # e.g. '-40°C to 55°C'
        upper = declared.split('to')[-1].strip()   # the hot-climate limit
        section = self._section(_read('llm.txt'), self.CLIMATE_HEADING)
        self.assertIn(upper, section,
                      'llm.txt climate section drifted from the product specs')

    def test_no_stray_temperature_in_climate_section(self):
        """Every temperature in the section must trace back to the specs.

        Two mutations were needed to get this right. Asserting "55\u00b0C appears
        somewhere" passed even after the rating was changed to 60\u00b0C,
        because a second sentence still said 55\u00b0C. Any temperature in this
        section now has to be one of: the published lower limit, the published
        upper limit, or 25\u00b0C (the L70 rating temperature).
        """
        ranges = self._spec_values('Operating Temperature Range')
        self.assertEqual(len(ranges), 1, 'ambiguous temperature in seed')
        limits = {n.lstrip('-') for n in re.findall(r'(-?\d+)\u00b0C', ranges.pop())}
        allowed = limits | {'25'}          # 25 deg C is the L70 rating basis
        section = self._section(_read('llm.txt'), self.CLIMATE_HEADING)
        found = set(re.findall(r'(\d+)\u00b0C', section))
        self.assertTrue(found, 'section quotes no temperature at all')
        self.assertEqual(found - allowed, set(),
                         'climate section quotes %s, specs allow %s'
                         % (sorted(found - allowed), sorted(allowed)))

    def test_ip_rating_matches_published_specs(self):
        ratings = self._spec_values('IP Rating')
        self.assertEqual(len(ratings), 1, 'ambiguous IP rating in seed_data.json')
        section = self._section(_read('llm.txt'), self.CLIMATE_HEADING)
        self.assertIn(ratings.pop(), section,
                      'llm.txt climate section drifted from the product specs')

    def test_climate_section_exists_in_both_languages(self):
        en = self._section(_read('llm.txt'),
                           'High-ambient, dusty and coastal operation')
        ar = self._section(_read('llm.ar.txt'), self.CLIMATE_HEADING_AR)
        for section in (en, ar):
            self.assertIn('55', section)
            self.assertIn('IP66', section)

    def test_absent_certifications_are_declared_absent(self):
        """Say what we do NOT hold — an AI must not infer we do.

        Wording was tightened from "does not currently claim" to "does not
        hold" on 2026-10-22: SolarOne decided not to pursue SASO or G-Mark at
        all, and "currently" reads as "we are working on it".
        """
        # Scoped to the sentence that names SASO, not the section: an
        # unrelated "فلا تحملها" three lines above satisfied a section-level
        # check after the real negation was deleted (mutation probe).
        en = _read('llm.txt')
        sasos_en = self._sentence(en, en.find('SASO'))
        self.assertIn('does not hold', sasos_en)
        self.assertIn('SASO', sasos_en)    # named, then explicitly disclaimed
        self.assertIn('G-Mark', sasos_en)
        ar = _read('llm.ar.txt')
        sasos_ar = self._sentence(ar, ar.find('SASO'))
        self.assertIn('SASO', sasos_ar)
        self.assertIn('\u0644\u0627 \u062a\u062f\u0651\u0639\u064a', sasos_ar)  # لا تدّعي
        self.assertIn('\u0644\u0627 \u062a\u062d\u0645\u0644', sasos_ar)        # لا تحمل

    def test_no_positive_claim_of_unheld_certification(self):
        for text in (_read('llm.txt'), _read('llm.ar.txt')):
            lowered = text.lower()
            for claim in self.FORBIDDEN_CLAIMS:
                self.assertNotIn(claim.lower(), lowered,
                                 f'llm.txt claims "{claim}" — unsupported')

    def test_salt_spray_claim_carries_no_hours_figure(self):
        """Reports exist for some models — but no published hours number.

        We hold salt-spray reports for selected models, so saying "we have
        none" would now be wrong. What is still unpublished is the hours
        figure, so that is what has to stay absent. A stray "1000 h salt
        spray" would be a spec we cannot back. The gap excludes sentence ends
        but NOT newlines — our own salt-spray sentences wrap mid-sentence, and
        excluding `\n` made this guard go green on a real hours figure
        (mutation probe, 2026-10-22). The full stop still keeps the
        L70 >100,000 h figure, two sentences away, from tripping it.
        """
        hours = r'\b\d{3,}\s*(?:h|hours|\u0633\u0627\u0639\u0629|\u0633\u0627\u0639\u0627\u062a)\b'
        gap = r'[^.\u06d4]{0,140}?'   # no full stop (ASCII or Arabic ۔),
                                      # newlines allowed — our sentences wrap
        for text in (_read('llm.txt'), _read('llm.ar.txt')):
            for salt, spray in ((r'salt[- ]spray', hours),
                                (r'\u0631\u0630\u0627\u0630 \u0627\u0644\u0645\u0644\u062d',
                                 hours)):
                for pattern in (salt + gap + spray, spray + gap + salt):
                    self.assertIsNone(
                        re.search(pattern, text, re.I),
                        'salt-spray text quotes a hours figure: %r'
                        % (re.search(pattern, text, re.I).group(0)
                           if re.search(pattern, text, re.I) else ''))

    def test_fifa_is_declared_as_not_claimed(self):
        """Only the AFC guideline may be cited; FIFA must be disclaimed.

        SolarOne has no FIFA-compliance data, so every FIFA mention outside an
        FAQ title has to be negated in its own sentence — otherwise an AI will
        happily cite "FIFA-compliant SolarOne stadium lights" for a query
        nobody gave it figures for. (Titles are exempt: a question is not a
        claim.) Scoped to the sentence, not a ±100-character window: a window
        wide enough to reach the neighbouring answer's "no" stayed green on a
        planted positive claim (mutation probe, 2026-10-22).
        """
        en = _read('llm.txt')
        self.assertIn('AFC', en)
        self.assertIn('FIFA', en, 'FIFA must be named to be disclaimed')
        for match in re.finditer(r'FIFA', en):
            line = en[en.rfind('\n', 0, match.start()) + 1:
                      en.find('\n', match.end())]
            if line.startswith('**') and line.endswith('?**'):
                continue                          # FAQ title — answer negates
            sentence = self._sentence(en, match.start()).lower()
            self.assertTrue(
                any(neg in sentence for neg in ('no ', 'not ', 'never',
                                                'does not', 'without')),
                'FIFA mentioned without a negation: %r' % sentence)
        ar = _read('llm.ar.txt')
        self.assertIn('AFC', ar)
        for match in re.finditer(r'FIFA', ar):
            line = ar[ar.rfind('\n', 0, match.start()) + 1:
                      ar.find('\n', match.end())]
            if line.startswith('**') and line.endswith(
                    '\u061f**'):                  # ؟**
                continue
            sentence = self._sentence(ar, match.start())
            self.assertIn('\u0644\u0627', sentence,   # لا
                          'FIFA mentioned without a negation: %r' % sentence)

    @staticmethod
    def _sentence(text, pos):
        """The sentence containing `pos`, so a negation in the next paragraph
        cannot green-light a claim made here."""
        ends = ('\n\n', '. ', '.\n', '\u061f\n', '\u061f ')
        start = max([text.rfind(sep, 0, pos) + len(sep)
                     for sep in ends if text.rfind(sep, 0, pos) != -1] or [0])
        stops = [text.find(sep, pos) for sep in ends]
        stops = [stop for stop in stops if stop != -1] or [len(text)]
        return text[start:min(stops)]


class LlmTxtFigureProvenanceTests(TestCase):
    """Every measured figure must name the project page it came from.

    "2200 lux, U0 0.8" is the most quotable line in llm.txt, and until
    2026-10-23 it carried no URL: an AI citing it had nothing to link to, and
    an unsourced number is exactly the kind a reader (or a retrieval model)
    discounts. Each bullet now cites the project page. These guards stop those
    citations from rotting into dead slugs, or from losing their locale prefix
    and pointing an Arabic reader at an English page.
    """

    MEASURED_HEADING = 'Measured results'
    MEASURED_HEADING_AR = '\u0646\u062a\u0627\u0626\u062c \u0645\u0642\u0627\u0633\u0629'  # نتائج مقاسة
    COMPLIANCE_MARKER = 'Compliance reference'
    COMPLIANCE_MARKER_AR = '\u0627\u0644\u0645\u0631\u062c\u0639 \u0627\u0644\u0645\u0639\u062a\u0645\u062f'  # المرجع المعتمد

    @staticmethod
    def _seed_project_slugs():
        """Real project slugs — the guard must not hardcode them.

        They live in seed_data.json (the production source of truth), so a
        renamed project makes this fail instead of quietly leaving llm.txt
        pointing at a 404.
        """
        with open(os.path.join(REPO_ROOT, 'seed_data.json'),
                  encoding='utf-8') as handle:
            projects = json.load(handle).get('projects') or []
        slugs = {project.get('slug') for project in projects}
        slugs.discard(None)
        return slugs

    @staticmethod
    def _section_containing(text, needle):
        """Body of the one `##` section whose heading contains `needle`.

        Substring match, not an exact heading: the Arabic heading carries a
        parenthesised gloss, and retyping it in escapes is how the first draft
        of llm.ar.txt picked up stray characters.
        """
        lines = text.split('\n')
        starts = [index for index, line in enumerate(lines)
                  if line.startswith('## ') and needle in line]
        assert len(starts) == 1, (
            'expected one section matching %r, found %d' % (needle, len(starts)))
        end = next((index for index in range(starts[0] + 1, len(lines))
                    if lines[index].startswith('## ')), len(lines))
        return '\n'.join(lines[starts[0] + 1:end])

    @staticmethod
    def _bullets(section):
        """Each `- ` block, keeping its wrapped continuation lines attached."""
        blocks, current = [], None
        for line in section.split('\n'):
            if line.startswith('- '):
                if current is not None:
                    blocks.append(current)
                current = line
            elif current is not None and line.startswith('  '):
                current += '\n' + line
            elif current is not None:
                blocks.append(current)
                current = None
        if current is not None:
            blocks.append(current)
        return blocks

    def _cited_slugs(self, text, heading):
        section = self._section_containing(text, heading)
        bullets = self._bullets(section)
        slugs = []
        for bullet in bullets:
            found = re.findall(r'/projects/([a-z0-9-]+)/', bullet)
            self.assertTrue(found,
                            'measured figure cites no project page: %r'
                            % bullet[:90])
            slugs.extend(found)
        self.assertTrue(slugs, 'section %r cites nothing at all' % heading)
        return slugs

    def test_every_measured_figure_cites_a_project_page(self):
        for text, heading in ((_read('llm.txt'), self.MEASURED_HEADING),
                              (_read('llm.ar.txt'), self.MEASURED_HEADING_AR)):
            self._cited_slugs(text, heading)   # asserts per bullet

    def test_cited_slugs_are_real_projects(self):
        cited = set(self._cited_slugs(_read('llm.txt'),
                                      self.MEASURED_HEADING))
        cited |= set(self._cited_slugs(_read('llm.ar.txt'),
                                       self.MEASURED_HEADING_AR))
        unknown = cited - self._seed_project_slugs()
        self.assertEqual(unknown, set(),
                         'llm.txt cites project pages that do not exist: %s'
                         % sorted(unknown))

    def test_both_languages_cite_the_same_projects(self):
        en = set(self._cited_slugs(_read('llm.txt'), self.MEASURED_HEADING))
        ar = set(self._cited_slugs(_read('llm.ar.txt'),
                                   self.MEASURED_HEADING_AR))
        self.assertEqual(ar, en, 'the Arabic variant dropped (or added) a '
                                 'cited project')

    def test_english_sources_stay_unprefixed(self):
        """English paths must stay `/projects/...` — no locale prefix.

        `/en/` is served without a prefix and redirects to it, so an English
        citation carrying `/ar/` would send the reader to the wrong language.
        """
        section = self._section_containing(_read('llm.txt'),
                                          self.MEASURED_HEADING)
        self.assertIsNone(re.search(r'/ar/projects/', section),
                          'English section cites a locale-prefixed path')

    def test_arabic_sources_carry_the_locale_prefix(self):
        section = self._section_containing(_read('llm.ar.txt'),
                                          self.MEASURED_HEADING_AR)
        self.assertIsNone(re.search(r'(?<!/ar)/projects/', section),
                          'Arabic section cites an unprefixed (English) path')

    def test_compliance_reference_cites_its_project(self):
        """The AFC paragraph names Yuanshen; that name needs its page too."""
        slugs = self._seed_project_slugs()
        for text, marker, prefix in (
                (_read('llm.txt'), self.COMPLIANCE_MARKER, '/projects/'),
                (_read('llm.ar.txt'), self.COMPLIANCE_MARKER_AR, '/ar/projects/')):
            start = text.find(marker)
            self.assertNotEqual(start, -1, '%r paragraph missing' % marker)
            block = text[start:text.find('\n## ', start)]
            found = re.findall(re.escape(prefix) + r'([a-z0-9-]+)/', block)
            self.assertTrue(found, '%r paragraph cites no project page'
                            % marker)
            self.assertEqual(set(found) - slugs, set(),
                             '%r cites unknown project: %s'
                             % (marker, sorted(set(found) - slugs)))

    def test_robots_txt_advertises_every_llm_variant(self):
        """A variant nobody declares is a variant nobody crawls.

        Derived from the files actually present, so shipping `llm.de.txt`
        without a robots.txt line fails the build instead of slipping through.
        """
        variants = sorted(name for name in os.listdir(REPO_ROOT)
                          if re.fullmatch(r'llm(\.[a-z]{2})?\.txt', name))
        self.assertIn('llm.txt', variants)
        self.assertIn('llm.ar.txt', variants)
        robots = _read('templates', 'robots.txt')
        for name in variants:
            self.assertIn('LLM-Txt: {{ canonical_origin }}/%s' % name, robots,
                          'robots.txt does not advertise %s' % name)


class LlmTxtEntityIdentityAndHighMastTests(TestCase):
    """Round-0 GEO failures, pinned so the copy cannot drift back.

    The 2026-10-23/24 baseline produced two opposite failures:

    * Perplexity (B1) and Grok (B2) split "SolarOne Lighting" (the brand)
      from "Beijing Solarone Energy Technology Co., Ltd." (the registered
      name) into two "related companies". Every fact was right; the identity
      was halved. The old copy only said the brand "is the ... brand of" the
      company, which an assistant reads as an affiliation, not an identity.
    * Perplexity (C3) told a buyer the site shows "no dedicated high-mast
      product line" and dropped SolarOne from the shortlist. FL6M/FL9M/
      FL12M/FL16M are sold as exactly that, but the Products block never
      used the words "high-mast" at all.

    Wattages are derived from `seed_data.json`, never hardcoded: seed is the
    production source of truth and `llm.txt` is the copy, so a spec change
    has to fail here instead of shipping a summary that contradicts the
    published specs. (Iron rule: no expected value invented inside a guard.)
    """

    USCC = '91110116663729775X'
    HIGH_MAST_SLUGS = ('fl6m', 'fl9m', 'fl12m', 'fl16m')
    # "كيان واحد" — spelled in escapes: typing Arabic literals inline is how
    # the first draft of llm.ar.txt picked up stray characters.
    AR_ONE_ENTITY = '\u0643\u064a\u0627\u0646 \u0648\u0627\u062d\u062f'

    @staticmethod
    def _section(text, heading):
        """Body of the one `##` section whose heading begins with `heading`."""
        match = re.search(r'^## %s.*?$(.*?)(?=^## |\Z)' % re.escape(heading),
                          text, re.M | re.S)
        assert match is not None, 'section %r not found' % heading
        return match.group(1)

    @staticmethod
    def _section_containing(text, needle):
        """The one `##` section that mentions `needle`.

        Used for the Arabic file, whose heading is Arabic: a Latin needle
        inside the section locates it without retyping the heading.
        """
        lines = text.split('\n')
        starts = [index for index, line in enumerate(lines)
                  if line.startswith('## ')]
        hits = []
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            body = '\n'.join(lines[start:end])
            if needle in body:
                hits.append(body)
        assert len(hits) == 1, (
            'expected exactly one section mentioning %r, found %d'
            % (needle, len(hits)))
        return hits[0]

    @staticmethod
    def _seed_products():
        with open(os.path.join(REPO_ROOT, 'seed_data.json'),
                  encoding='utf-8') as handle:
            return json.load(handle).get('products') or []

    def test_who_section_declares_one_entity(self):
        who = self._section(_read('llm.txt'), 'Who')
        self.assertIn(self.USCC, who)
        self.assertIn('ONE entity', who)

    def test_disambiguation_carries_uscc_and_both_namesakes(self):
        block = self._section(_read('llm.txt'), 'Not to be confused with')
        self.assertIn(self.USCC, block)
        self.assertEqual(
            block.count('Xinnengyang'), 2,
            'both 信能阳光 namesakes must be named, not just one')
        # The long-standing namesakes must survive every rewrite of this block.
        for entity in ('SolarOne Solutions', 'Solar One', 'Fonroche'):
            self.assertIn(entity, block)

    def test_arabic_variant_mirrors_the_identity_claim(self):
        block = re.sub(r'\s+', ' ',
                       self._section_containing(_read('llm.ar.txt'),
                                                'SolarOne Solutions'))
        self.assertIn(self.USCC, block)
        self.assertIn(self.AR_ONE_ENTITY, block)
        self.assertEqual(block.count('Xinnengyang'), 2,
                         'Arabic variant names only one 信能阳光 namesake')

    def test_products_section_states_high_mast_duty(self):
        products = re.sub(r'\s+', ' ',
                          self._section(_read('llm.txt'), 'Products'))
        self.assertIn('High-mast duty', products)

    def test_high_mast_wattages_match_seed(self):
        products = re.sub(r'\s+', ' ',
                          self._section(_read('llm.txt'), 'Products'))
        by_slug = {product.get('slug'): product
                   for product in self._seed_products()}
        for slug in self.HIGH_MAST_SLUGS:
            product = by_slug.get(slug)
            self.assertIsNotNone(product, 'seed lost product %r' % slug)
            wattage = str(product.get('wattage') or product.get('power') or '')
            self.assertRegex(wattage, r'^\d+W$',
                             'unexpected wattage for %s: %r' % (slug, wattage))
            self.assertIn(
                '%s (%s)' % (slug.upper(), wattage), products,
                'llm.txt quotes a %s wattage that no longer matches seed'
                % slug.upper())

    def test_jsonld_declares_the_single_entity(self):
        """Rendered, not source-level.

        A JSON-LD line carrying a stray quote stays legal template syntax
        while vanishing from the page, so the assertion runs against the
        rendered home page. HTTP_HOST is set because ALLOWED_HOSTS does not
        contain `testserver`.
        """
        body = Client(HTTP_HOST='localhost').get('/').content.decode(
            'utf-8', errors='replace')
        match = re.search(r'"disambiguatingDescription":\s*"(.*?)",', body, re.S)
        self.assertIsNotNone(
            match, 'Organization JSON-LD lost its disambiguatingDescription')
        desc = match.group(1)
        self.assertIn(self.USCC, desc)
        self.assertIn('one entity', desc)
        self.assertIn('SolarOne Solutions', desc)
