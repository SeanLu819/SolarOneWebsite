"""
Project <title> keyword guards (L1 unit tests).

Context: all 22 project pages shared the static suffix
``{title} — SolarOne LED Lighting Project`` — not one of them carried a
category keyword, so ``/projects/<slug>/`` never bid on
``led football stadium lights`` / ``led tennis court lights``.

Covers:
  * The exact ad-copy strings for the football and tennis pages (case is part
    of the contract — the modifiers stay lowercase, the head nouns capitalised).
  * Every sport_type in ``Project.SPORT_TYPE_CHOICES`` resolves to a phrase.
  * The seed path (``_DictProject``, what production renders on Vercel) stays
    byte-identical to the DB model path.
  * The explicit ``seo_title`` override still wins over the formula.
  * The rendered project detail page carries the keyword in its <title>.
"""
from django.test import Client, TestCase

from pages.models import Project
from pages.utils import (
    DEFAULT_PROJECT_CATEGORY_KEYWORD,
    PROJECT_CATEGORY_KEYWORD,
    _SEO_BRAND,
    build_project_seo_title,
    get_seo_override,
    project_category_keyword,
)
from pages.views.utils import _DictProject, _load_seed


#: The three pages the campaign copy names, and what the length clamp makes of
#: them. 'Morgan State University Tennis Courts' alone is 37 characters; with a
#: 23-char keyword and the 11-char brand suffix the unclamped form would be 74,
#: so the project name takes the cut (word boundary + ellipsis) and the keyword
#: stays intact. Same for the other two — the H1, og:title, breadcrumb
#: JSON-LD and body copy still carry the full name.
EXACT_TITLES = {
    'Bohemia Manor High School': (
        'FOOTBALL_FIELD',
        'LED football Stadium Lights',
        'Bohemia Manor… — LED football Stadium Lights | SolarOne',
    ),
    'Morgan State University Tennis Courts': (
        'TENNIS_COURTS',
        'LED tennis Court Lights',
        'Morgan State… — LED tennis Court Lights | SolarOne',
    ),
    'Perryville High School': (
        'FOOTBALL_FIELD',
        'LED football Stadium Lights',
        'Perryville High… — LED football Stadium Lights | SolarOne',
    ),
}

#: Every choice in Project.SPORT_TYPE_CHOICES must map to a non-empty phrase;
#: unknown values collapse to the documented default (never an empty middle).
SPORT_TYPE_CHOICES = [
    'FOOTBALL_FIELD', 'SOCCER_FIELD', 'BASEBALL_FIELD', 'TENNIS_COURTS',
    'SKI_AREA', 'KARTING', 'BASKETBALL', 'VELODROME', 'TENNIS',
    'TRACK_FIELD', 'MULTI_SPORT', 'FENCING', 'AQUATICS_CENTRE', 'AIRPORT',
    'ICE_ARENA', 'CITY_EXPRESSWAY', 'OTHER',
]


#: Hard SERP budget — Google truncates the tail of a <title>, which would cut
#: the keyword AND the brand off the 16 longer project pages.
MAX_TITLE_LEN = 60


class ProjectSeoTitleKeywordTests(TestCase):
    def test_exact_campaign_strings(self):
        """The three shipped project titles match the ad copy byte for byte."""
        for title, (sport, kw, expected) in EXACT_TITLES.items():
            self.assertEqual(build_project_seo_title(title, sport), expected)
            self.assertEqual(project_category_keyword(sport), kw)
            self.assertLessEqual(len(expected), MAX_TITLE_LEN)

    def test_campaign_keywords_survive_unbroken(self):
        """The part the ad copy is about is the keyword, never the project name."""
        for title, (sport, kw, _expected) in EXACT_TITLES.items():
            out = build_project_seo_title(title, sport)
            self.assertIn(kw, out)
            self.assertTrue(out.endswith('| SolarOne'))
            # the institution's leading tokens stay readable
            self.assertEqual(out[:out.index('…')].strip().split(' ')[0],
                             title.split(' ')[0])

    def test_every_project_title_fits_the_serp_budget(self):
        """No project <title> may exceed the pixel truncation budget."""
        seed = _load_seed()
        for item in seed['projects']:
            title = _DictProject(item).seo_title('en')
            self.assertLessEqual(len(title), MAX_TITLE_LEN, f'overflow: {title!r}')

    def test_truncation_happens_on_a_word_boundary(self):
        """The clamp must never slice mid-word and must never break the keyword."""
        seed = _load_seed()
        for item in seed['projects']:
            out = _DictProject(item).seo_title('en')
            if '…' not in out:
                continue
            head = out[:out.index('…')]
            self.assertTrue(head, f'{out!r} starts with an ellipsis')
            self.assertFalse(head.endswith(' '), f'{out!r} ellipsis after a space')
            self.assertEqual(out.count('…'), 1)
        # the keyword half is never touched
        for item in seed['projects']:
            if item.get('sport_type') == 'TENNIS_COURTS':
                self.assertIn('LED tennis Court Lights', _DictProject(item).seo_title('en'))
                break

    def test_short_project_names_are_left_untouched(self):
        """Fitting inside the budget must not chop short names for fun."""
        short = 'Nanshan Ski Village — LED Ski Area Lights | SolarOne'
        self.assertEqual(build_project_seo_title('Nanshan Ski Village', 'SKI_AREA'), short)

    def test_every_sport_type_maps_to_a_phrase(self):
        for choice in SPORT_TYPE_CHOICES:
            kw = project_category_keyword(choice)
            self.assertTrue(kw, f'sport_type {choice!r} has no keyword phrase')
            self.assertIn('LED', kw)

    def test_unknown_sport_type_falls_back_to_default(self):
        self.assertEqual(
            project_category_keyword('NOT_A_SPORT'),
            DEFAULT_PROJECT_CATEGORY_KEYWORD,
        )
        self.assertEqual(project_category_keyword(''), DEFAULT_PROJECT_CATEGORY_KEYWORD)

    def test_non_english_locale_falls_back_to_english_phrase(self):
        """B8/E2 territory today: never emit an empty/English-untouched suffix."""
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            self.assertTrue(project_category_keyword('FOOTBALL_FIELD', lang))
        self.assertEqual(
            project_category_keyword('FOOTBALL_FIELD', 'fr'),
            PROJECT_CATEGORY_KEYWORD['FOOTBALL_FIELD'],
        )


class ProjectSeedPathParityTests(TestCase):
    def test_seed_project_titles_carry_keyword(self):
        seed = _load_seed()
        projects = {p.get('slug'): p for p in seed['projects']}
        checked = 0
        for slug, item in projects.items():
            obj = _DictProject(item)
            title = obj.seo_title('en')
            sport = item.get('sport_type', '')
            kw = PROJECT_CATEGORY_KEYWORD.get(sport, DEFAULT_PROJECT_CATEGORY_KEYWORD)
            # the keyword reaches the SERP intact: it is never the clamped part
            self.assertIn(kw, title, f'{slug} keyword missing: {title!r}')
            self.assertTrue(title.endswith(f'| {_SEO_BRAND}'), f'{slug} lost the brand')
            checked += 1
        self.assertEqual(checked, len(seed['projects']), 'no projects exercised')

    def test_seed_and_formula_agree_on_the_three_campaign_pages(self):
        seed = _load_seed()
        for title, (_, _, expected) in EXACT_TITLES.items():
            for item in seed['projects']:
                if item.get('title') == title:
                    self.assertEqual(_DictProject(item).seo_title('en'), expected)
                    break
            else:
                self.fail(f'seed has no project titled {title!r}')


class ProjectOverrideAndRenderTests(TestCase):
    def test_explicit_seo_title_override_wins(self):
        obj = _DictProject({
            'title': 'Bohemia Manor High School',
            'slug': 'football-field-led-retrofit',
            'sport_type': 'FOOTBALL_FIELD',
            'translations': {'en': {'seo_title': 'Custom Title | SolarOne'}},
        })
        self.assertEqual(obj.seo_title('en'), 'Custom Title | SolarOne')
        # ...and without the override the formula would have produced the
        # keyword title instead (guards against the override being dead code).
        obj.translations = {}
        self.assertIn('LED football Stadium Lights', obj.seo_title('en'))

    def test_og_title_keeps_the_full_project_name(self):
        """The shared card must not inherit the clamped <title>."""
        seed = _load_seed()
        target = None
        for item in seed['projects']:
            if len(item['title']) > 40:  # exactly the ones the clamp shortens
                target = item
                break
        self.assertIsNotNone(target)
        client = Client()
        resp = client.get(f"/projects/{target['slug']}/", HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn(f'<meta property="og:title" content="{target["title"]} | SolarOne"', content)

    def test_project_detail_page_renders_keyword_title(self):
        seed = _load_seed()
        target = None
        for item in seed['projects']:
            if item.get('sport_type') == 'TENNIS_COURTS':
                target = item
                break
        self.assertIsNotNone(target, 'seed has no tennis project')
        client = Client()
        resp = client.get(f"/projects/{target['slug']}/", HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('LED tennis Court Lights', content)
        self.assertIn('| SolarOne', content)
