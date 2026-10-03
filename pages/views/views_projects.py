from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.http import Http404
from django.utils.translation import get_language
from .common import get_common_context
from pages.redirects import redirect_target_for_project
from .i18n import (
    _get_projects_sidebar,
    _resolve_active_labels,
    _resolve_project_sidebar,
    _t,
)
from .data_loaders import get_projects, get_project_detail


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


def _projects_collection(request, key, title, intro, description):
    """Render ``projects.html`` for one fixed group of ``sport_type`` values."""
    context = get_common_context()
    lang = get_language()

    context['venue_types'] = _get_projects_sidebar(lang)
    context['collection_key'] = key
    context['active_venue_type'] = ''
    context['active_sport_type'] = ''

    context['page_title'] = title
    context['page_description'] = description
    context['page_intro'] = intro
    # `projects.html` renders the H1 from this label, so the collection page
    # gets its keyword heading without a second template.
    context['active_sport_type_label'] = title

    projects_list = get_projects(lang, '', list(PROJECT_COLLECTION_SPORTS[key]))
    paginator = Paginator(projects_list or [], 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context['projects'] = page_obj.object_list
    context['page_obj'] = page_obj
    # A head-only child of projects.html: same grid, own title/description.
    return render(request, 'projects_collection.html', context)


def projects_football(request):
    """/projects/football/ — every real football *and* soccer field project."""
    lang = get_language()
    return _projects_collection(
        request, 'football',
        _t('Football Stadium Lighting Projects | SolarOne', lang),
        _t('Football and soccer field LED lighting projects delivered worldwide — stadiums, high school fields and training pitches.', lang),
        _t('Real football and soccer field LED lighting projects by SolarOne — stadium, high school and training pitch installations with measured results.', lang),
    )


def projects_tennis(request):
    """/projects/tennis/ — indoor *and* outdoor tennis court projects."""
    lang = get_language()
    return _projects_collection(
        request, 'tennis',
        _t('Tennis Court Lighting Projects | SolarOne', lang),
        _t('Indoor and outdoor tennis court LED lighting projects delivered worldwide — club, university and competition courts.', lang),
        _t('Real indoor and outdoor tennis court LED lighting projects by SolarOne — club, university and competition courts with measured results.', lang),
    )


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