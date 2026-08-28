import os
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
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

    scheme = 'https'
    host = request.get_host()

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
        urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>{priority}</priority></url>')

    for p in products:
        slug = p.get('slug', '')
        if slug:
            path = reverse('product_detail', args=[slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.7</priority></url>')

    seen_series = set()
    for p in products:
        parent_slug = p.get('parent_slug', '')
        if parent_slug and parent_slug not in seen_series:
            seen_series.add(parent_slug)
            path = reverse('product_series', args=[parent_slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.7</priority></url>')

    for proj in projects:
        slug = proj.get('slug', '')
        if slug:
            path = reverse('project_detail', args=[slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.7</priority></url>')

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls)
    xml += '\n</urlset>'
    return render(request, 'sitemap.xml', {'xml': xml}, content_type='application/xml')


def diagnostic(request):
    base_dir = str(settings.BASE_DIR)
    static_root = str(settings.STATIC_ROOT)
    static_dirs = [str(d) for d in settings.STATICFILES_DIRS]

    result = {
        'BASE_DIR': base_dir,
        'STATIC_ROOT': static_root,
        'STATIC_ROOT_exists': os.path.isdir(static_root),
        'STATICFILES_DIRS': static_dirs,
        'STATICFILES_DIRS_exist': {d: os.path.isdir(d) for d in static_dirs},
        'root_listing': sorted(os.listdir(base_dir)) if os.path.isdir(base_dir) else 'NOT FOUND',
    }

    if os.path.isdir(static_root):
        subdirs = [d for d in os.listdir(static_root) if os.path.isdir(os.path.join(static_root, d))]
        result['STATIC_ROOT_subdirs'] = sorted(subdirs)
        result['STATIC_ROOT_file_count'] = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])

    for d in static_dirs:
        if os.path.isdir(d):
            subdirs = [s for s in os.listdir(d) if os.path.isdir(os.path.join(d, s))]
            result[f'{d}_subdirs'] = sorted(subdirs)

    return JsonResponse(result)