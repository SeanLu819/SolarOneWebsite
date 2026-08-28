from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.translation import get_language
from .common import get_common_context
from .i18n import _get_projects_sidebar, _resolve_project_sidebar
from .data_loaders import (
    _get_projects_from_db, _get_projects_from_json,
    _get_project_detail_from_db, _get_project_detail_from_json,
)


def projects(request):
    context = get_common_context()
    lang = get_language()

    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    active_venue_type = request.GET.get('venue', '')
    active_sport_type = request.GET.get('sport', '')
    context['active_venue_type'] = active_venue_type
    context['active_sport_type'] = active_sport_type

    active_venue_type_label = ''
    active_sport_type_label = ''
    for vt in venue_types:
        if vt['key'] == active_venue_type:
            active_venue_type_label = vt['label']
            for s in vt['sports']:
                if s['key'] == active_sport_type:
                    active_sport_type_label = s['label']
                    break
            break
    context['active_venue_type_label'] = active_venue_type_label
    context['active_sport_type_label'] = active_sport_type_label

    projects_list = _get_projects_from_db(lang, active_venue_type, active_sport_type)
    if not projects_list:
        projects_list = _get_projects_from_json(lang, active_venue_type, active_sport_type)

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

    project = _get_project_detail_from_db(slug, lang)
    if project is None:
        project = _get_project_detail_from_json(slug, lang)

    if project:
        context['project'] = project
        context['gallery'] = project.gallery
        active_venue_type, active_sport_type = _resolve_project_sidebar(
            getattr(project, 'sport_type', ''), lang,
            db_venue_type=getattr(project, 'venue_type', ''),
        )
        context['active_venue_type'] = active_venue_type
        context['active_sport_type'] = active_sport_type

        active_venue_type_label = ''
        active_sport_type_label = ''
        for vt in venue_types:
            if vt['key'] == active_venue_type:
                active_venue_type_label = vt['label']
                for s in vt['sports']:
                    if s['key'] == active_sport_type:
                        active_sport_type_label = s['label']
                        break
                break
        context['active_venue_type_label'] = active_venue_type_label
        context['active_sport_type_label'] = active_sport_type_label
    else:
        context['active_venue_type'] = ''
        context['active_sport_type'] = ''

    return render(request, 'project_detail.html', context)