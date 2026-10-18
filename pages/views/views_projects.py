import json

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import Http404
from django.utils.translation import get_language, gettext as _
from .common import get_common_context
from pages.redirects import redirect_target_for_project
from .i18n import (
    _get_projects_sidebar,
    _resolve_active_labels,
    _resolve_project_sidebar,
    _t,
)
from .data_loaders import get_projects, get_project_detail
from .related_links import related_products_for_project
# Maps a project's sport_type to the collection page it belongs on, so the
# project detail page can vote for that keyword page with keyword-rich anchor
# text. 'football' and 'tennis' resolve to /projects/football/ and
# /projects/tennis/; everything else resolves to /products/ — non-sports venues
# (AIRPORT, ROADWAY, INFRASTRUCTURE, …) rank on venue-name long-tails, not on a
# sport keyword, so they link to the product catalogue instead of being forced
# into a sports page.
SPORT_TYPE_TO_LANDING = {
    'FOOTBALL_FIELD': 'football',
    'SOCCER_FIELD': 'football',
    'TENNIS_COURTS': 'tennis',
    'TENNIS': 'tennis',
    'MULTI_SPORT': 'sports',
    'BASEBALL_FIELD': 'sports',
    'BASKETBALL': 'sports',
    'ICE_ARENA': 'sports',
    'VELODROME': 'sports',
    'AQUATICS_CENTRE': 'sports',
    'FENCING': 'sports',
    'KARTING': 'sports',
    'SKI_AREA': 'sports',
}


def projects(request):
    context = get_common_context()
    lang = get_language()

    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    active_venue_type = request.GET.get('venue', '')
    active_sport_type = request.GET.get('sport', '')
    context['active_venue_type'] = active_venue_type
    context['active_sport_type'] = active_sport_type

    # A2: label lookup收口到 i18n._resolve_active_labels
    active_venue_type_label, active_sport_type_label = _resolve_active_labels(
        venue_types, active_venue_type, active_sport_type, child_key='sports',
    )
    context['active_venue_type_label'] = active_venue_type_label
    context['active_sport_type_label'] = active_sport_type_label

    projects_list = get_projects(lang, active_venue_type, active_sport_type)

    paginator = Paginator(projects_list or [], 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['projects'] = page_obj.object_list
    context['page_obj'] = page_obj
    return render(request, 'projects.html', context)


#: Static keyword collection pages: one URL per keyword, listing only projects
#: that actually exist.
#:
#: These exist because the obvious alternative — pointing the keyword at
#: ``/projects/?venue=OUTDOOR&sport=FOOTBALL_FIELD`` — does not work:
#:   * the enum splits a single sport across two values, so a one-value filter
#:     silently drops real projects (``SOCCER_FIELD``, and ``TENNIS`` which is
#:     INDOOR and therefore excluded by ``venue=OUTDOOR``);
#:   * ``request.path`` carries no query string, so every filtered URL renders
#:     ``<link rel="canonical" href="…/projects/">`` — Google collapses them into
#:     the unfiltered page and the keyword never owns a distinct URL.
#: A real path fixes both: indexable, self-canonical, and honest about which
#: projects belong to the keyword.
PROJECT_COLLECTION_SPORTS = {
    'football': ('FOOTBALL_FIELD', 'SOCCER_FIELD'),
    'tennis': ('TENNIS_COURTS', 'TENNIS'),
}


#: Per-sport copy + content for the unified sports-landing template
#: (``stadium_lighting.html``). Every string here is English; the builder runs
#: each through gettext so the six locales resolve (new strings fall back to
#: English until the ``.po`` files are updated — same arrangement as STADIUM_FAQ).
#: Product rosters and selection rows are written out literally, not derived:
#: they are the product decisions each keyword page exists to express, and the
#: guards in tests_project_collections.py pin them so a change is deliberate.
FOOTBALL_FAQ = [
    {
        'question': 'How many floodlights does a football pitch need?',
        'answer': (
            'It follows from the target illuminance on the pitch and the number '
            'of masts the structure allows, not a fixed fixture count. The VSP '
            'series is rated 4200 W per system, so a pitch reaches its target '
            'from fewer masts than the high-pressure scheme it replaces. Send '
            'the pitch drawing and mast height and we return a photometric layout.'
        ),
    },
    {
        'question': 'Are these lights suitable for live TV and super-slow-motion?',
        'answer': (
            'Yes. Vision Strobe Protection on the VSP series keeps the output '
            'free of the low-frequency flicker that shows up as banding in '
            'super-slow-motion replay, and the asymmetric optics keep glare out '
            'of the camera-side seating.'
        ),
    },
    {
        'question': 'What beam angles suit a football pitch?',
        'answer': (
            '12°, 18°, 30° and 50° from the same optical platform — narrow '
            'angles for the seating bowl, wider ones for the playing surface.'
        ),
    },
    {
        'question': 'How high should football floodlight masts be?',
        'answer': (
            'Professional stadiums mount on the roof rim at 30–45 m; training '
            'grounds use poles at 8–20 m depending on the lux target and the '
            'surround.'
        ),
    },
    {
        'question': 'Are the luminaires flicker-free for broadcast?',
        'answer': (
            'Yes — the VSP series is built for broadcast, and the FL/M modular '
            'floods are flicker-free for training and club coverage.'
        ),
    },
    {
        'question': 'Do you supply a photometric study for our pitch?',
        'answer': (
            'Yes. Our engineering team delivers a full photometric proposal — '
            'layout, illuminance and uniformity — within 48 hours of receiving '
            'your pitch drawing.'
        ),
    },
    {
        # v1.10.29: see pages.utils.UL_DLC_SLUGS. Scoped to the VSP series,
        # which is what this page features.
        'question': 'Are your football floodlights UL listed and DLC qualified?',
        'answer': (
            'Yes. The VSP series is UL Listed and DLC Standard qualified: UL '
            'for electrical compliance on North American sites, and DLC '
            'Standard for utility rebate programmes. Certification '
            'documentation ships with the quotation.'
        ),
    },
]

TENNIS_FAQ = [
    {
        'question': 'What lux level do tennis courts need?',
        'answer': (
            'Recreational courts run around 200–300 lux, competition 500–750 '
            'lux, and broadcast shows 1000 lux and above. We model the exact '
            'figure for your court and level of play.'
        ),
    },
    {
        'question': 'How many light poles does a tennis court need?',
        'answer': (
            'A standard singles court is lit from four corner poles or a pair '
            'of high masts; doubles and show courts vary with the surround and '
            'the broadcast requirement.'
        ),
    },
    {
        'question': 'Can these be used for indoor tennis centres?',
        'answer': (
            'Yes. The RT and RT410 high-bay models mount to the ceiling for '
            'indoor centres, while the FL and M series light the surrounding '
            'areas and covered courts.'
        ),
    },
    {
        'question': 'Are they glare-free for players?',
        'answer': (
            'Asymmetric, low-glare optics aim the light onto the court surface, '
            'not into the players’ eyes, so the ball stays readable from '
            'baseline to net.'
        ),
    },
    {
        'question': 'Are they suitable for broadcast and slow-motion?',
        'answer': (
            'The VSP series carries Vision Strobe Protection for flicker-free '
            'super-slow-motion; the modular floods cover training and club '
            'coverage without flicker.'
        ),
    },
    {
        'question': 'Do you supply a photometric study for our court?',
        'answer': (
            'Yes. Our engineering team delivers a full photometric proposal — '
            'layout, illuminance and uniformity — within 48 hours of receiving '
            'your court drawing.'
        ),
    },
    {
        # v1.10.29: this roster mixes certified and uncertified models, so
        # the answer names the series that hold the listing rather than
        # claiming it for the whole range. See pages.utils.UL_DLC_SLUGS.
        'question': 'Are the tennis court lights UL listed and DLC qualified?',
        'answer': (
            'The M Series, RT410 and VSP models are UL Listed and DLC Standard '
            'qualified; some other models in the range are not. Tell us the '
            'fixture you are specifying and we confirm the listing for that '
            'exact model before you order.'
        ),
    },
]

SPORT_LANDING_PAGES = {
    'football': {
        'title': 'Football Stadium Lighting Projects | SolarOne',
        'description': (
            'Real football and soccer field LED lighting projects by SolarOne — '
            'stadium, high school and training pitch installations with measured '
            'results.'
        ),
        'accent': 'Football Lighting',
        'h1': 'Football Field Lighting',
        'intro': (
            'A football pitch is lit for two crowds at once — the one in the '
            'stands and the one on the broadcast feed. SolarOne builds both: '
            'broadcast-grade VSP floodlights for televised matches, and modular '
            'LED floods from 80 W to 1280 W for training grounds, club venues '
            'and school fields.'
        ),
        'product_heading': 'Football Floodlights',
        'product_lead': (
            'Pick by level of play: professional and televised stadiums run '
            'the VSP-XXXXW series with asymmetric 12 / 18 / 30 / 50 degree '
            'optics, while training grounds, academies and club pitches run '
            'the M Series modular flood.'
        ),
        'featured_slugs': ('m-series', 'vsp-xxxxw-9m-yp'),
        'selection_heading': 'Choosing the Right Output',
        'selection_lead': (
            'Two numbers decide a football package: the target illuminance on '
            'the pitch and the number of masts the structure allows. This is '
            'the range our delivered football projects actually use.'
        ),
        'selection_rows': [
            {'venue_type': 'Professional stadium, televised',
             'fixture': 'VSP-XXXXW-12M-YP, 1000 W+',
             'distribution': '12 / 18 / 30 / 50°', 'mounting': 'Roof rim, 30–45 m'},
            {'venue_type': 'Training ground, club venue',
             'fixture': 'FL6M–FL9M, 480–720 W',
             'distribution': '12 / 18 / 30 / 50°', 'mounting': 'Pole, 8–20 m'},
            {'venue_type': 'Multi-sport / school hall',
             'fixture': 'RT410-RGBW or RT400HB, 400–600 W',
             'distribution': '60 / 90 / 120°', 'mounting': 'Roof truss, 12–20 m'},
            {'venue_type': '5-a-side / community pitch',
             'fixture': 'FL4M–FL6M, 320–480 W',
             'distribution': 'Asymmetric, low glare', 'mounting': 'Pole, 6–10 m'},
        ],
        'selection_note': (
            'Full photometric data, IES files and DIALux reports are supplied '
            'on request — send the pitch drawing and mast height.'
        ),
        'venue_heading': 'Delivered Football Venue Projects',
        'venue_lead': (
            'Real football and soccer field LED lighting projects delivered '
            'worldwide — stadiums, high schools and training pitches.'
        ),
        'faq_heading': 'Football Lighting FAQ',
        'faq': FOOTBALL_FAQ,
    },
    'tennis': {
        'title': 'Tennis Court Lighting Projects | SolarOne',
        'description': (
            'Real indoor and outdoor tennis court LED lighting projects by '
            'SolarOne — club, university and competition courts with measured '
            'results.'
        ),
        'accent': 'Tennis Court Lighting',
        'h1': 'Tennis Court Lighting',
        'intro': (
            'A tennis court needs even light without glare in the players’ eyes '
            '— the ball moves fast and low. SolarOne builds for both: '
            'broadcast-grade VSP floodlights for competition show courts, and '
            'modular LED floods from 80 W to 1280 W for club, university and '
            'community courts.'
        ),
        'product_heading': 'Tennis Court Floodlights',
        'product_lead': (
            'Two platforms cover the court: the RT410 series — tunable white '
            'and RGBW for show courts and club venues — and the M Series '
            'modular flood for training and community courts.'
        ),
        'featured_slugs': ('rt410-series', 'm-series'),
        'selection_heading': 'Choosing the Right Output',
        'selection_lead': (
            'Three numbers decide a tennis package: the target lux on the court, '
            'the pole height, and whether the court is indoor or outdoor. This '
            'is the range our delivered tennis projects actually use.'
        ),
        'selection_rows': [
            {'venue_type': 'Competition court, televised',
             'fixture': 'VSP-XXXXW-9M-YP, 4200 W',
             'distribution': '12 / 18 / 30 / 50°', 'mounting': 'Pole, 12–18 m'},
            {'venue_type': 'Club / training court',
             'fixture': 'FL6M, 480 W',
             'distribution': '12 / 18 / 30 / 50°', 'mounting': 'Pole, 8–12 m'},
            {'venue_type': 'Indoor tennis centre',
             'fixture': 'RT400HB / RT410, 130–260 W',
             'distribution': '60 / 90 / 120°', 'mounting': 'Ceiling, 8–12 m'},
            {'venue_type': 'Padel / pickleball court',
             'fixture': 'FL4M, 320 W',
             'distribution': 'Asymmetric, low glare', 'mounting': 'Pole, 6–8 m'},
        ],
        'selection_note': (
            'Full photometric data, IES files and DIALux reports are supplied '
            'on request — send the court drawing and pole positions.'
        ),
        'venue_heading': 'Delivered Tennis Court Projects',
        'venue_lead': (
            'Real indoor and outdoor tennis court LED lighting projects '
            'delivered worldwide — club, university and competition courts.'
        ),
        'faq_heading': 'Tennis Court Lighting FAQ',
        'faq': TENNIS_FAQ,
    },
}


def projects_landing(request, key):
    """Render the unified sports-landing template for one keyword (football/tennis).

    Same template as ``/stadium-lighting/`` (``stadium_lighting.html``), driven by
    the per-sport config in ``SPORT_LANDING_PAGES``. Replaces the old case-grid
    ``projects_collection.html`` pages (now deleted).
    """
    from .views_stadium import (
        _localised_faq, build_landing_faq_jsonld, get_featured_landing_products,
    )

    cfg = SPORT_LANDING_PAGES[key]
    lang = get_language() or 'en'
    context = get_common_context()

    sport_types = list(PROJECT_COLLECTION_SPORTS[key])
    # No image filter and no limit: the project-collection guard asserts the page
    # lists exactly the sport's real projects, so the venues shown must be the
    # full set returned by the loader.
    venues = list(get_projects(lang, '', sport_types) or [])

    featured = get_featured_landing_products(cfg['featured_slugs'], lang)
    faq = _localised_faq(cfg['faq'], lang)
    faq_json = json.dumps(
        build_landing_faq_jsonld(
            faq, entity_id=f'{settings.CANONICAL_ORIGIN}{request.path}#faq'),
        ensure_ascii=False,
    )
    selection_rows = [
        {
            'venue_type': _(r['venue_type']),
            'fixture': _(r['fixture']),
            'distribution': _(r['distribution']),
            'mounting': _(r['mounting']),
        }
        for r in cfg['selection_rows']
    ]

    context.update({
        'page_title': _t(cfg['title'], lang),
        'page_description': _t(cfg['description'], lang),
        'landing_accent': _(cfg['accent']),
        'landing_h1': _(cfg['h1']),
        'landing_intro': _(cfg['intro']),
        'product_heading': _(cfg['product_heading']),
        'product_lead': _(cfg['product_lead']),
        'landing_products': featured,
        'landing_product_count': len(featured),
        'selection_heading': _(cfg['selection_heading']),
        'selection_lead': _(cfg['selection_lead']),
        'selection_rows': selection_rows,
        'selection_note': _(cfg['selection_note']),
        'venue_heading': _(cfg['venue_heading']),
        'venue_lead': _(cfg['venue_lead']),
        'landing_venues': venues,
        # SEO internal link: the keyword pages point back to the stadium hub so
        # /stadium-lighting/ is never an orphan. The hub page itself does not set
        # this, so it never links to itself.
        'hub_link_url': reverse('stadium_lighting'),
        'faq_items': faq,
        'faq_json': faq_json,
        'faq_heading': _(cfg['faq_heading']),
    })
    return render(request, 'stadium_lighting.html', context)



def projects_football(request):
    """/projects/football/ — football + soccer field landing (product + project)."""
    return projects_landing(request, 'football')


def projects_tennis(request):
    """/projects/tennis/ — tennis court landing (product + project)."""
    return projects_landing(request, 'tennis')


def project_detail(request, slug):
    """Project detail page with backend-managed text and image carousel."""
    context = get_common_context()
    lang = get_language()

    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    project = get_project_detail(slug, lang)

    if project:
        context['project'] = project
        context['gallery'] = project.gallery
        active_venue_type, active_sport_type = _resolve_project_sidebar(
            getattr(project, 'sport_type', ''), lang,
            db_venue_type=getattr(project, 'venue_type', ''),
        )
        context['active_venue_type'] = active_venue_type
        context['active_sport_type'] = active_sport_type

        # A2: label lookup收口到 i18n._resolve_active_labels
        active_venue_type_label, active_sport_type_label = _resolve_active_labels(
            venue_types, active_venue_type, active_sport_type, child_key='sports',
        )
        context['active_venue_type_label'] = active_venue_type_label
        context['active_sport_type_label'] = active_sport_type_label

        # Internal anchor-text vote for the Tier-1/2 keyword landing pages.
        context['related_landing'] = SPORT_TYPE_TO_LANDING.get(
            getattr(project, 'sport_type', ''))

        # B2: cross-link to products whose category matches this
        # project's sport/venue type (breaks the content islands).
        context['related_products'] = related_products_for_project(project, lang)

    else:
        # S2: an unresolvable slug may simply be a page that was renamed. Only
        # consulted on a miss, so a registered redirect can never shadow a live
        # page. `redirect()` reverses, which keeps the visitor's language
        # prefix — building the path by hand would drop /fr/ back to English.
        moved = redirect_target_for_project(slug)
        if moved:
            return redirect('project_detail', moved, permanent=True)

        # v1.9.7: unknown slug with no redirect entry must be a REAL 404, the
        # same contract the product side got in v1.8.2. Previously this fell
        # through to `render(request, 'project_detail.html')` with no project
        # in context, which produced a 200 "Project Not Found" page carrying a
        # self-referencing canonical — a soft 404. That lets Google index any
        # fabricated /projects/<garbage>/ URL and judge the site low quality.
        # Verified live 2026-10-03 before the fix:
        #   /projects/does-not-exist-xyz/ -> 200 + <title>Project Not Found.
        # Raising here keeps the redirect table above authoritative: a renamed
        # page still 301s, only genuinely unknown slugs 404.
        raise Http404('No project matches the given slug.')

    return render(request, 'project_detail.html', context)