import os
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from .common import get_common_context
from .utils import _load_seed


def home(request):
    return render(request, 'home.html', get_common_context())


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)


def news(request):
    context = get_common_context()
    articles = []
    try:
        from pages.models import NewsArticle
        articles = list(NewsArticle.objects.filter(is_published=True).order_by('-published_at'))
    except Exception:
        import logging
        logging.getLogger(__name__).warning('DB news query failed', exc_info=True)
    context['articles'] = articles
    return render(request, 'news.html', context)


def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')


def sitemap_xml(request):
    data = _load_seed()
    products = data.get('products', [])
    projects = data.get('projects', [])

    # Fixed canonical origin (#17) — never derive URLs from request.get_host()
    origin = settings.CANONICAL_ORIGIN

    urls = []

    static_pages = [
        ('home', None, '0.9'),
        ('products', None, '0.9'),
        ('projects', None, '0.9'),
        ('news', None, '0.7'),
        ('about', None, '0.7'),
        ('contact', None, '0.7'),
    ]
    for name, _, priority in static_pages:
        path = reverse(name)
        urls.append(f'  <url><loc>{origin}{path}</loc><priority>{priority}</priority></url>')

    for p in products:
        slug = p.get('slug', '')
        if slug:
            path = reverse('product_detail', args=[slug])
            urls.append(f'  <url><loc>{origin}{path}</loc><priority>0.7</priority></url>')

    seen_series = set()
    for p in products:
        parent_slug = p.get('parent_slug', '')
        if parent_slug and parent_slug not in seen_series:
            seen_series.add(parent_slug)
            path = reverse('product_series', args=[parent_slug])
            urls.append(f'  <url><loc>{origin}{path}</loc><priority>0.7</priority></url>')

    for proj in projects:
        slug = proj.get('slug', '')
        if slug:
            path = reverse('project_detail', args=[slug])
            urls.append(f'  <url><loc>{origin}{path}</loc><priority>0.7</priority></url>')

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls)
    xml += '\n</urlset>'
    return render(request, 'sitemap.xml', {'xml': xml}, content_type='application/xml')


@staff_member_required
def diagnostic(request):
    """Diagnostic info — staff-only, minimal exposure.

    Only reachable when settings.DEBUG is True (see pages/urls.py).
    Defense-in-depth: if DEBUG is somehow False at request time, return 404.
    Removed the root directory listing and absolute filesystem paths to
    avoid leaking deployment structure.
    """
    if not settings.DEBUG:
        raise Http404
    result = {
        'debug': settings.DEBUG,
        'python_version': '{}.{}.{}'.format(*__import__('sys').version_info[:3]),
        'django_version': __import__('django').get_version(),
        'static_configured': bool(settings.STATIC_URL),
    }
    return JsonResponse(result)