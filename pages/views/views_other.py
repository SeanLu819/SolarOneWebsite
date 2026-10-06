import email.utils
import os
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape
from django.shortcuts import render
from django.http import JsonResponse, Http404, HttpResponse
from django.urls import reverse
from django.utils.translation import get_language, override
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.templatetags.static import static
from pages.utils import project_category_keyword
from .common import get_common_context
from .data_loaders import (
    get_news, get_news_detail, get_product_detail, get_products,
    get_projects, get_project_detail,
)
from .related_links import related_items_for_news
from .i18n import _t
from .data_loaders import get_news, get_product_detail, get_project_detail
from .utils import _first_static, _load_seed


def home(request):
    return render(request, 'home.html', get_common_context())


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)


def privacy(request):
    """Static legal page (B1/F1). English base copy; section headings go
    through ``{% trans %}`` so they can be localised later via gettext."""
    return render(request, 'privacy.html', get_common_context())


def terms(request):
    """Static legal page (B1/F1). See privacy() for the i18n note."""
    return render(request, 'terms.html', get_common_context())


def news(request):
    context = get_common_context()
    lang = get_language()
    articles = get_news(lang)

    # Sidebar directory: every category in the feed, its translated label and
    # how many articles it holds. Labels go through `_t()` on purpose — the
    # template cannot run `{% trans %}`, which only accepts *literal* strings,
    # so the earlier `{% trans cat.name %}` silently rendered an empty label.
    counts = {}
    for a in articles:
        cat = a.get('category') or 'Exhibition Information'
        counts[cat] = counts.get(cat, 0) + 1
        # Per-article badge label. `get_news()` builds fresh dicts per request
        # (there is no news-level cache), so writing the key here is safe.
        a['category_label'] = _t(cat, lang)
    context['news_categories'] = sorted(
        (
            {'key': cat, 'label': _t(cat, lang), 'count': cnt}
            for cat, cnt in counts.items()
        ),
        key=lambda c: c['key'],
    )
    context['news_total_count'] = sum(counts.values())

    # Category filter. An unknown key falls back to "everything" instead of
    # rendering an empty page — a stale bookmark should not read as "no news".
    requested = (request.GET.get('category') or '').strip()
    if requested and requested not in counts:
        requested = ''
    if requested:
        articles = [
            a for a in articles
            if (a.get('category') or 'Exhibition Information') == requested
        ]
    context['articles'] = articles
    context['news_active_category'] = requested
    return render(request, 'news.html', context)


def news_detail(request, slug):
    """One news article. Cards on the list page link here (industry standard:
    the listing never carries the body copy). Unknown/unpublished slug -> 404,
    on both the seed path and the DB path."""
    context = get_common_context()
    lang = get_language()
    article = get_news_detail(slug, lang)
    if article is None:
        raise Http404('No published news article with that slug.')
    context['article'] = article

    # Sidebar-style category labels come from `_t()` — see news() above.
    cat = article.get('category') or 'Exhibition Information'
    context['category_label'] = _t(cat, lang)

    # "More news": the latest other articles, same shape as the list cards.
    related = [a for a in get_news(lang) if a.get('slug') != slug]
    for a in related:
        a['category_label'] = _t(a.get('category') or 'Exhibition Information', lang)
    context['related_articles'] = related[:3]
    # B2: only link products/projects explicitly named in the article
    # (keyword match) so we never invent a weak generic cross-link.
    rel_products, rel_projects = related_items_for_news(article, lang)
    context['related_products'] = rel_products
    context['related_projects'] = rel_projects

    return render(request, 'news_detail.html', context)


def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')


def _site_last_modified():
    """Date string for sitemap ``<lastmod>``.

    Vercel's serverless checkout rewrites file mtimes, so on production
    ``os.path.getmtime()`` on seed_data.json returned a stale 2018 date for
    every URL. build.sh therefore stamps an explicit build date into the
    git-ignored build artifact ``pages/build_meta.py`` (same pattern as
    ``pages/seed_data.py``). Locally that file does not exist, so fall back
    to the seed snapshot mtime.
    """
    try:
        from pages.build_meta import SITE_LAST_MODIFIED
    except Exception:
        SITE_LAST_MODIFIED = ''
    if SITE_LAST_MODIFIED:
        return SITE_LAST_MODIFIED
    try:
        return datetime.fromtimestamp(os.path.getmtime(
            os.path.join(str(settings.BASE_DIR), 'seed_data.json')
        )).date().isoformat()
    except Exception:
        return ''

def indexnow_key(request):
    """Serve the IndexNow key file (Bing / Yandex push protocol).

    IndexNow requires ``https://<host>/<key>.txt`` to return the key as plain
    text. Without it, Bing can only discover new URLs by crawling on its own
    schedule; with it we can push changed URLs the moment we deploy.
    """
    key = getattr(settings, 'INDEXNOW_KEY', '')
    if not key:
        raise Http404
    return HttpResponse(key, content_type='text/plain; charset=utf-8')

#: v1.10.22 (P3-B) — images for the ten *collection* pages.
#:
#: Google accepts ``<image:image>`` on any ``<url>``, not only leaf pages, and
#: a collection page's own banner is exactly the image a shopper searching
#: that category sees at the top of the result. Before this, 10 of the 59
#: sitemap URLs carried zero images: the home page, the product index, both
#: project collections, the news index, about and contact — every page a
#: first-time visitor lands on.
#:
#: 🔴 Two rules keep this honest, and ``tests_image_seo_p3`` enforces both:
#:
#: 1. **Only images the page actually renders.** The hero has three slides on
#:    desktop but a ``<source media="(max-width:767px)">`` portrait variant per
#:    slide; the portrait files are not listed because on mobile the page
#:    renders one of them *instead of* the landscape file, and a sitemap entry
#:    for an image a crawler will never see is a dead reference. The light-theme
#:    product banner is likewise excluded — it is a CSS alternate of the dark
#:    one, not a second picture.
#: 2. **The file must exist.** A path here that is not on disk ships a 404 to
#:    the crawler, which is worse than no entry at all. Every path is resolved
#:    through ``_find_static`` and dropped when missing.
#:
#: ``privacy`` and ``terms`` are absent on purpose: legal text with no
#: imagery, and inventing an entry for them would be the very "image for the
#: sake of an entry" mistake this table exists to avoid.
#:
#: Titles and captions are the same strings the templates already put in
#: ``alt`` / ``og:description``, so the sitemap and the page describe one image
#: the same way. Nothing here is new copy.
_COLLECTION_PAGE_IMAGES = {
    'home': (
        ('images/hero-main-1.webp', 'LED sports stadium lighting', ''),
        ('images/hero-main-2.webp', 'Football field LED lighting', ''),
        ('images/hero-main-3.webp', 'Industrial LED high bay lighting', ''),
        ('images/home-products.webp',
         'SolarOne LED product lineup including stadium and industrial luminaires',
         ''),
        ('images/home-project.webp',
         'SolarOne LED lighting reference projects — sports venues, airports, '
         'and industrial facilities',
         ''),
    ),
    'products': (
        ('images/products-bar-dark.webp',
         'SolarOne LED lighting product categories overview',
         'Modular flood lights, stadium lighting, high bay and roadway '
         'luminaires from one manufacturer.'),
    ),
    'about': (
        ('images/about-main.webp',
         'SolarOne LED lighting engineering and manufacturing headquarters in '
         'Beijing, China',
         ''),
    ),
    'contact': (
        ('images/agent-usa.webp', 'SolarOne USA agent', ''),
        ('images/agent-germany.webp', 'SolarOne Germany agent', ''),
        ('images/agent-france.webp', 'SolarOne France agent', ''),
    ),
}

#: Project collections take their images from the project list they render, not
#: from a literal: membership is decided by the sport filter the collection
#: view applies plus the seed, so a hard-coded list would rot the moment a
#: project joins a sport group. Keys are the ``reverse()`` names in urls.py.
_COLLECTION_PROJECT_SPORTS = {
    'projects_football': ('FOOTBALL_FIELD', 'SOCCER_FIELD'),
    'projects_tennis': ('TENNIS_COURTS', 'TENNIS'),
}

#: A collection page with 50 projects does not need 50 sitemap images — the
#: leaf project pages carry those, and Google reads a 50-image entry as noise.
_COLLECTION_IMAGE_CAP = 10


def _static_image_tuple(rel_path, title, caption, cap=200):
    """Resolve a ``static/``-relative path to an image tuple, or ``None``.

    ``None`` is the caller's cue to drop the entry: shipping a known-404 to
    the crawler is worse than shipping nothing. ``_first_static`` is the
    project's single existence-checked resolver — it consults the
    same cached manifest that serves the page, hash-suffix stripping included,
    so the sitemap can never list a file the page itself would 404 on.
    """
    resolved = _first_static([rel_path])
    if not resolved:
        return None
    return (resolved, title, (caption or '')[:cap])


def _collection_page_images(name):
    """``(url, title, caption)`` tuples for one static collection page."""
    out = []
    for rel_path, title, caption in _COLLECTION_PAGE_IMAGES.get(name, ()):
        entry = _static_image_tuple(rel_path, title, caption)
        if entry:
            out.append(entry)
    return out


def _project_covers(projects, lang='en'):
    """Cover-image tuples for a list of enriched projects.

    The caption is venue type + location: the venue type is the phrase the
    project's own ``<title>`` bids on, and the location supplies the "where"
    that a bare venue type cannot express. Matches what P3-C puts in the
    project gallery alt, so one project is described in one vocabulary.
    """
    out = []
    for proj in projects:
        url = getattr(proj, 'image_url', '') or ''
        if not url:
            continue
        kw = project_category_keyword(getattr(proj, 'sport_type', ''), lang)
        caption = ' — '.join(
            p for p in (kw, getattr(proj, 'location_t', '') or '') if p)
        out.append((url, getattr(proj, 'title_t', '') or '', caption))
    return out


def _collection_dynamic_images(name, lang='en'):
    """Images for the collection pages whose content comes from the loaders."""
    if name in _COLLECTION_PROJECT_SPORTS:
        sports = list(_COLLECTION_PROJECT_SPORTS[name])
        return _project_covers(
            (get_projects(lang, '', sports) or [])[:_COLLECTION_IMAGE_CAP], lang)
    if name == 'stadium_lighting':
        # The page renders one product cover per stadium luminaire plus a
        # venue cover per project, so the sitemap entry lists the same
        # pictures the visitor sees. Drawn from the loaders rather than a
        # literal for the same reason as the other collections.
        from .views_stadium import (
            FEATURED_PRODUCT_SLUGS, STADIUM_CATEGORY, VENUE_PROJECT_LIMIT,
        )
        from .related_links import PRODUCT_CATEGORY_TO_PROJECT_SPORTS

        sports = PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(STADIUM_CATEGORY, [])
        out = []
        category_products = [p for p in (get_products(lang) or [])
                             if getattr(p, 'category', '') == STADIUM_CATEGORY]
        by_slug = {p.slug: p for p in category_products}
        for product in [by_slug[s] for s in FEATURED_PRODUCT_SLUGS if s in by_slug]:
            url = getattr(product, 'image_url', '') or ''
            if url:
                out.append((url, getattr(product, 'name_t', '') or '', ''))
        for proj in [p for p in (get_projects(lang) or [])
                      if getattr(p, 'sport_type', '') in sports
                      and getattr(p, 'image_url', '')][:VENUE_PROJECT_LIMIT]:
            kw = project_category_keyword(getattr(proj, 'sport_type', ''), lang)
            caption = ' — '.join(
                p for p in (kw, getattr(proj, 'location_t', '') or '') if p)
            out.append((
                proj.image_url, getattr(proj, 'title_t', '') or '', caption))
        return out
    if name == 'projects':
        return _project_covers(
            (get_projects(lang) or [])[:_COLLECTION_IMAGE_CAP], lang)
    if name == 'news':
        # Deliberately NOT ``get_news()``: that helper has no seed
        # fallback by design (a DB failure degrades /news/ to an empty
        # list rather than serving stale content), so using it here made
        # the sitemap's /news/ entry lose its images whenever the DB was
        # unavailable. The seed snapshot is what the detail loop below
        # already trusts, and a sitemap is a build artefact, so it reads
        # the same source. Same ``is_published`` gate, same
        # ``get_news_detail`` resolution, so an unpublished article cannot
        # leak in through the index.
        out = []
        for art in (_load_seed().get('news') or []):
            if len(out) >= _COLLECTION_IMAGE_CAP:
                break
            slug = art.get('slug', '')
            if not slug or not art.get('is_published', True):
                continue
            detail = get_news_detail(slug, lang)
            if detail is None:
                continue
            url = detail.get('image_url') or ''
            if not url:
                continue
            out.append((
                url,
                detail.get('title_t') or detail.get('title') or '',
                detail.get('summary_t') or detail.get('summary') or '',
            ))
        return out
    return []


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
    _lastmod = _site_last_modified()

    with override('en'):
        static_pages = [
            ('home', '0.9'),
            ('products', '0.9'),
            ('projects', '0.9'),
            ('projects_football', '0.8'),
            ('projects_tennis', '0.8'),
            ('news', '0.7'),
            # v1.10.23 (P4-A): the generic stadium-lighting page. Priority
            # 0.8 — above the news index because it owns 5 010/mo of
            # measured search volume, below /products/ because it is one term
            # rather than the whole catalogue.
            ('stadium_lighting', '0.8'),
            ('about', '0.7'),
            ('privacy', '0.4'),
            ('terms', '0.4'),
            ('contact', '0.7'),
        ]
        for name, priority in static_pages:
            # v1.10.22 (P3-B): collection pages carry their own imagery —
            # the banner a visitor sees, or the covers of the cards the page
            # lists. privacy/terms resolve to [] on purpose (legal text, no
            # images) and a page whose files went missing drops its entry
            # rather than shipping a 404 to the crawler.
            images = _collection_page_images(name)
            if not images:
                images = _collection_dynamic_images(name)
            urls.append(_entry(reverse(name), priority, _lastmod, images))

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

        # News detail pages: same treatment as products/projects. The seed's
        # `is_published` gate mirrors what get_news_detail() enforces, so an
        # unpublished article never leaks into the sitemap. Image tuples are
        # (url, title, caption) — `_image_entries` dedupes cover vs gallery.
        for art in data.get('news', []) or []:
            slug = art.get('slug', '')
            if not slug or not art.get('is_published', True):
                continue
            detail = get_news_detail(slug, 'en')
            if detail is None:
                continue
            title = detail.get('title_t', '') or detail.get('title', '')
            caption = detail.get('summary_t', '') or detail.get('summary', '')
            images = (
                [(detail.get('image_url', ''), title, caption)]
                + [(g.get('url', ''), title, caption)
                   for g in (detail.get('images') or [])]
            )
            urls.append(_entry(
                reverse('news_detail', args=[slug]), '0.6', _lastmod, images))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
    )
    xml += '\n'.join(urls)
    xml += '\n</urlset>'
    return render(request, 'sitemap.xml', {'xml': xml}, content_type='application/xml')


def news_feed(request):
    """RSS 2.0 feed of published news articles (B4, SEO/GEO).

    Served so AI answer engines and human aggregators can discover new
    articles. XML is built in Python (no template array concatenation) and
    every text node is XML-escaped via ``xml.sax.saxutils.escape`` — this is a
    SEPARATE escaping channel from the JSON-LD ``|escapejs`` used elsewhere.
    ``link`` uses ``settings.CANONICAL_ORIGIN`` (never the request host), the
    same choice as ``sitemap_xml``.
    """
    data = _load_seed()
    # Fixed canonical origin (#17) — same choice as sitemap_xml.
    origin = settings.CANONICAL_ORIGIN
    news = [a for a in (data.get('news') or []) if a.get('is_published', True)]
    # v1.10.2: sort newest-first explicitly, same reason and same key as
    # ``_get_news_from_json`` — RSS readers show the first item as the newest,
    # so "first == newest" must be a property of this function, not of the
    # seed file's physical layout (which seed_sync happens to write in
    # ``NewsArticle.Meta.ordering`` order). ISO-8601 strings with a shared
    # format sort chronologically.
    news.sort(key=lambda a: a.get('published_at') or '', reverse=True)

    items = []
    for art in news:
        slug = art.get('slug', '')
        if not slug:
            continue
        title = art.get('title', '') or ''
        summary = art.get('summary', '') or ''
        link = f'{origin}/news/{slug}/'
        pub = art.get('published_at', '') or ''
        pubdate = ''
        try:
            # RFC 822 pubDate from the ISO published_at. usegmt=True emits the
            # "GMT" form (e.g. "Fri, 25 Sep 2026 00:00:00 GMT"), which is valid
            # RFC 822 and parsed by all readers; requires a tz-aware datetime,
            # which the seed's "+00:00" suffix provides.
            pubdate = email.utils.format_datetime(
                datetime.fromisoformat(pub), usegmt=True)
        except (ValueError, TypeError):
            pubdate = pub
        items.append(
            '    <item>\n'
            f'      <title>{_xml_escape(title)}</title>\n'
            f'      <link>{_xml_escape(link)}</link>\n'
            f'      <description>{_xml_escape(summary)}</description>\n'
            f'      <pubDate>{_xml_escape(pubdate)}</pubDate>\n'
            f'      <guid isPermaLink="true">{_xml_escape(link)}</guid>\n'
            '    </item>'
        )

    items_xml = ('\n'.join(items) + '\n') if items else ''
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" '
        'xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '  <channel>\n'
        f'    <title>{_xml_escape("SolarOne News")}</title>\n'
        f'    <link>{_xml_escape(origin)}/news/</link>\n'
        f'    <description>{_xml_escape("Latest news, product launches and project case studies from SolarOne LED lighting.")}</description>\n'
        '    <language>en</language>\n'
        f'    <atom:link href="{_xml_escape(origin)}/news/feed.xml" '
        'rel="self" type="application/rss+xml"/>\n'
        f'{items_xml}'
        '  </channel>\n'
        '</rss>'
    )
    return HttpResponse(xml, content_type='application/rss+xml')


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