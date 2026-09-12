import os
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils.translation import get_language, override
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
    """Multi-language sitemap.

    The site has 6 languages served from one origin (`/` for English, `/{code}/`
    for the rest) and already emits <link rel="alternate" hreflang> in the HTML
    head (see pages/templatetags/seo_tags.py). This sitemap mirrors that: each
    canonical path gets one <url> entry carrying xhtml:link alternates for all
    languages plus x-default -> English, so translated URLs are discoverable even
    though the sitemap is fetched from the unprefixed (English) origin.

    Paths are reversed with the language forced to 'en' so they stay
    language-neutral even when requested via a prefixed URL (/fr/sitemap.xml).
    """
    data = _load_seed()
    products = data.get('products', [])
    projects = data.get('projects', [])

    # Fixed canonical origin (#17) — never derive URLs from request.get_host()
    origin = settings.CANONICAL_ORIGIN
    langs = [code for code, _ in settings.LANGUAGES]

    def _loc(path, code):
        return f'{origin}{path}' if code == 'en' else f'{origin}/{code}{path}'

    def _entry(path, priority):
        en_loc = _loc(path, 'en')
        parts = [f'<loc>{en_loc}</loc>']
        for code in langs:
            parts.append(
                f'<xhtml:link rel="alternate" hreflang="{code}" href="{_loc(path, code)}"/>'
            )
        parts.append(
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{en_loc}"/>'
        )
        parts.append(f'<priority>{priority}</priority>')
        return '  <url>' + ''.join(parts) + '</url>'

    urls = []

    with override('en'):
        static_pages = [
            ('home', '0.9'),
            ('products', '0.9'),
            ('projects', '0.9'),
            ('news', '0.7'),
            ('about', '0.7'),
            ('contact', '0.7'),
        ]
        for name, priority in static_pages:
            urls.append(_entry(reverse(name), priority))

        for p in products:
            slug = p.get('slug', '')
            if slug:
                urls.append(_entry(reverse('product_detail', args=[slug]), '0.7'))

        seen_series = set()
        for p in products:
            parent_slug = p.get('parent_slug', '')
            if parent_slug and parent_slug not in seen_series:
                seen_series.add(parent_slug)
                urls.append(_entry(reverse('product_series', args=[parent_slug]), '0.7'))

        for proj in projects:
            slug = proj.get('slug', '')
            if slug:
                urls.append(_entry(reverse('project_detail', args=[slug]), '0.7'))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    )
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