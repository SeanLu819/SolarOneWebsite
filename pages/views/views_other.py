import os
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils.translation import get_language, override
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from .common import get_common_context
from .data_loaders import get_news, get_product_detail, get_project_detail
from .utils import _load_seed


def home(request):
    return render(request, 'home.html', get_common_context())


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)


def news(request):
    context = get_common_context()
    lang = get_language()
    context['articles'] = get_news(lang)
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

    Product/project <url> entries additionally carry the Google *image sitemap*
    extension (``<image:image>``): the source filenames carry no keywords, so
    the descriptive text lives in ``<image:title>``/``<image:caption>`` built
    from the enriched detail objects. Because the whole block runs under
    ``override('en')`` the images are emitted once, in English — the sitemap is
    a single language-neutral file, so there is deliberately no per-language
    image entry.
    """
    data = _load_seed()
    products = data.get('products', [])
    projects = data.get('projects', [])

    # Fixed canonical origin (#17) — never derive URLs from request.get_host()
    origin = settings.CANONICAL_ORIGIN
    langs = [code for code, _ in settings.LANGUAGES]

    # Google truncates image captions well before this; 200 chars keeps the
    # descriptive text meaningful without bloating a 42-URL sitemap.
    _CAPTION_MAX = 200

    def _loc(path, code):
        return f'{origin}{path}' if code == 'en' else f'{origin}/{code}{path}'

    def _abs_url(url):
        """Prefix a relative /static|/media path with the canonical origin.

        ``image_url``/``src`` come back relative (e.g. ``/static/images/...``);
        a fully-qualified URL (CDN/absolute) is left untouched.
        """
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        return f'{origin}{url}'

    def _image_entries(images):
        """Render one ``<image:image>`` line per unique, non-empty image.

        ``images`` is an iterable of ``(url, title, caption)`` tuples. The
        title/caption are the *only* descriptive text we have — the source
        filenames carry no keywords — so they are XML-escaped (captions are
        long prose containing ``&``, quotes and non-ASCII) and the caption is
        truncated. Duplicates are dropped because the same file legitimately
        appears both as the cover ``image_url`` and inside ``gallery``.
        """
        seen = set()
        lines = []
        for url, title, caption in images:
            if not url or url in seen:
                continue
            seen.add(url)
            parts = [f'<image:loc>{_xml_escape(_abs_url(url))}</image:loc>']
            if title:
                parts.append(f'<image:title>{_xml_escape(title)}</image:title>')
            if caption:
                parts.append(
                    '<image:caption>'
                    f'{_xml_escape(caption[:_CAPTION_MAX])}'
                    '</image:caption>'
                )
            lines.append('<image:image>' + ''.join(parts) + '</image:image>')
        return lines

    def _detail_images(detail, title_attr, caption_attrs):
        """Build ``(url, title, caption)`` tuples from an enriched detail obj.

        Returns ``[]`` when the detail could not be resolved (``None``) so the
        caller still emits the plain ``<url>`` entry. ``image_url`` may be ''
        and is filtered by ``_image_entries``.
        """
        if detail is None:
            return []
        raw = [getattr(detail, 'image_url', '')]
        raw += [
            g.get('src', '')
            for g in (getattr(detail, 'gallery', None) or [])
        ]
        title = getattr(detail, title_attr, '') or ''
        caption = ''
        for attr in caption_attrs:
            caption = getattr(detail, attr, '') or ''
            if caption:
                break
        return [(url, title, caption) for url in raw]

    def _entry(path, priority, lastmod='', images=None):
        en_loc = _loc(path, 'en')
        parts = [f'<loc>{en_loc}</loc>']
        if images:
            parts.extend(_image_entries(images))
        if lastmod:
            parts.append(f'<lastmod>{lastmod}</lastmod>')
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

    # <lastmod> (SEO P2): products/projects carry no updated_at in the seed
    # snapshot, so a per-URL timestamp is unavailable. Use the seed snapshot's
    # own mtime — stable across requests within a deploy (Google distrusts a
    # lastmod that changes on every fetch) and honest as "content published".
    try:
        _lastmod = datetime.fromtimestamp(os.path.getmtime(
            os.path.join(str(settings.BASE_DIR), 'seed_data.json')
        )).date().isoformat()
    except Exception:
        _lastmod = ''

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
            urls.append(_entry(reverse(name), priority, _lastmod))

        for p in products:
            slug = p.get('slug', '')
            if slug:
                images = _detail_images(
                    get_product_detail(slug, 'en'),
                    'name_t',
                    ('description_t',),
                )
                urls.append(_entry(
                    reverse('product_detail', args=[slug]), '0.7', _lastmod, images))

        for proj in projects:
            slug = proj.get('slug', '')
            if slug:
                images = _detail_images(
                    get_project_detail(slug, 'en'),
                    'title_t',
                    ('location_t', 'description_t'),
                )
                urls.append(_entry(
                    reverse('project_detail', args=[slug]), '0.7', _lastmod, images))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
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