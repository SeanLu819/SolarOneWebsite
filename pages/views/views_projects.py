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
)
from .data_loaders import get_projects, get_project_detail


# Maps a project's sport_type to a related landing page so the project detail
# page can vote for the Tier-1/2 SEMrush keyword pages via keyword-rich anchor
# text. Non-sports venues (AIRPORT, ROADWAY, INFRASTRUCTURE, etc.) map to None
# so no irrelevant link is injected — those pages rank on venue-name long-tails.
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