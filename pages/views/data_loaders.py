import json
import logging
from datetime import datetime

from django.conf import settings
from pages.models import Product, Project, NewsArticle
from .utils import (
    _load_seed, _DictProduct, _DictProject,
    _static_url, _find_static, _normalize_static_rel,
)
from .news_body import build_article_body
from .enrich import (
    _enrich_product, _enrich_project,
    _get_cached_products, _set_cached_products,
    _get_cached_projects, _set_cached_projects,
    _get_cached_product_detail, _set_cached_product_detail,
    _get_cached_project_detail, _set_cached_project_detail,
)
from .i18n import _product_category_filter

logger = logging.getLogger(__name__)


def _get_products_from_db(lang, active_category='', active_series=''):
    """Try loading products from DB. Returns None on failure."""
    # Production is fully stateless: content comes from the committed seed JSON,
    # never the database. Bypass the DB entirely (also removes the per-request
    # DB retry that could mask a missing connection). See A1 / B7.
    if getattr(settings, 'IS_VERCEL', False):
        return _get_products_from_json(lang, active_category, active_series)
    cached = _get_cached_products(lang, active_category, active_series)
    if cached is not None:
        return cached
    try:
        products_list = Product.objects.filter(parent__isnull=True, is_active=True)
        if active_category:
            products_list = products_list.filter(category__in=_product_category_filter(active_category))
        if active_series:
            products_list = products_list.filter(slug=active_series)
        products_list = products_list.order_by('order')
        result = []
        for p in products_list:
            _enrich_product(p, lang)
            result.append(p)
        if result:
            # Only cache a non-empty DB result. Caching an empty list would poison
            # the shared enrichment cache and block the seed-JSON fallback in
            # get_products() when the DB query legitimately returns nothing (e.g.
            # a freshly created empty database). Falling back to the seed JSON in
            # that case is the documented behaviour ("database first, seed JSON
            # fallback when the query ... returns nothing").
            _set_cached_products(result, lang, active_category, active_series)
        return result
    except Exception:
        logger.warning('DB products query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_products_from_json(lang, active_category='', active_series=''):
    """Load products from seed_data.json (fallback for Vercel)."""
    cached = _get_cached_products(lang, active_category, active_series)
    if cached is not None:
        return cached
    data = _load_seed()
    items = data.get('products', [])
    result = []
    for item in items:
        if item.get('parent_slug'):
            continue
        if not active_series and not item.get('is_active', True):
            continue
        if active_category and item.get('category') not in _product_category_filter(active_category):
            continue
        if active_series and item.get('slug') != active_series:
            continue
        p = _DictProduct(item)
        _enrich_product(p, lang)
        result.append(p)
    result.sort(key=lambda p: getattr(p, 'order', 0) or 0)
    _set_cached_products(result, lang, active_category, active_series)
    return result


def _get_product_detail_from_db(slug, lang):
    """Try loading a single product from DB. Returns None on failure."""
    if getattr(settings, 'IS_VERCEL', False):
        return _get_product_detail_from_json(slug, lang)
    cached = _get_cached_product_detail(slug, lang)
    if cached is not None:
        return cached
    try:
        product = Product.objects.select_related('parent').prefetch_related('images').get(slug=slug)
        _enrich_product(product, lang)
        _set_cached_product_detail(product, slug, lang)
        return product
    except Product.DoesNotExist:
        return None
    except Exception:
        logger.warning('DB product detail query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_product_detail_from_json(slug, lang):
    """Load a single product from seed_data.json (fallback for Vercel)."""
    cached = _get_cached_product_detail(slug, lang)
    if cached is not None:
        return cached
    data = _load_seed()
    for item in data.get('products', []):
        if item.get('slug') == slug:
            p = _DictProduct(item)
            _enrich_product(p, lang)
            _set_cached_product_detail(p, slug, lang)
            return p
    return None


def _sport_filter_values(active_sport_type):
    """Normalise the sport filter into a list of ``sport_type`` enum values.

    The collection pages (``/projects/football/``, ``/projects/tennis/``) each
    span *two* enum values — football is ``FOOTBALL_FIELD`` + ``SOCCER_FIELD``,
    tennis is ``TENNIS_COURTS`` + ``TENNIS`` — because the same sport is split
    across two keys in the data. ``get_projects`` flattens a multi-value filter
    into one comma-separated string so the cache key stays hashable; this
    splits it back apart for the queryset / seed scan.
    """
    if not active_sport_type:
        return []
    if isinstance(active_sport_type, (list, tuple, set)):
        return [v for v in active_sport_type if v]
    return [v for v in str(active_sport_type).split(',') if v]


def _get_projects_from_db(lang, active_venue_type='', active_sport_type=''):
    """Try loading projects from DB. Returns None on failure."""
    if getattr(settings, 'IS_VERCEL', False):
        return _get_projects_from_json(lang, active_venue_type, active_sport_type)
    cached = _get_cached_projects(lang, active_venue_type, active_sport_type)
    if cached is not None:
        return cached
    try:
        projects_list = Project.objects.all()
        if active_venue_type:
            projects_list = projects_list.filter(venue_type=active_venue_type)
        sports = _sport_filter_values(active_sport_type)
        if sports:
            projects_list = projects_list.filter(sport_type__in=sports)
        result = []
        for proj in projects_list:
            _enrich_project(proj, lang)
            result.append(proj)
        if result:
            # Mirror the products loader: do not cache an empty DB result, or it
            # would block the seed-JSON fallback in get_projects().
            _set_cached_projects(result, lang, active_venue_type, active_sport_type)
        return result
    except Exception:
        logger.warning('DB projects query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_projects_from_json(lang, active_venue_type='', active_sport_type=''):
    """Load projects from seed_data.json (fallback for Vercel)."""
    cached = _get_cached_projects(lang, active_venue_type, active_sport_type)
    if cached is not None:
        return cached
    data = _load_seed()
    items = data.get('projects', [])
    result = []
    sports = set(_sport_filter_values(active_sport_type))
    for item in items:
        if active_venue_type and item.get('venue_type') != active_venue_type:
            continue
        if sports and item.get('sport_type') not in sports:
            continue
        proj = _DictProject(item)
        _enrich_project(proj, lang)
        result.append(proj)
    _set_cached_projects(result, lang, active_venue_type, active_sport_type)
    return result


def _get_project_detail_from_db(slug, lang):
    """Try loading a single project from DB. Returns None on failure."""
    if getattr(settings, 'IS_VERCEL', False):
        return _get_project_detail_from_json(slug, lang)
    cached = _get_cached_project_detail(slug, lang)
    if cached is not None:
        return cached
    try:
        project = Project.objects.prefetch_related('images').get(slug=slug)
        _enrich_project(project, lang)
        _set_cached_project_detail(project, slug, lang)
        return project
    except Project.DoesNotExist:
        return None
    except Exception:
        logger.warning('DB project detail query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_project_detail_from_json(slug, lang):
    """Load a single project from seed_data.json (fallback for Vercel)."""
    cached = _get_cached_project_detail(slug, lang)
    if cached is not None:
        return cached
    data = _load_seed()
    for item in data.get('projects', []):
        if item.get('slug') == slug:
            proj = _DictProject(item)
            _enrich_project(proj, lang)
            _set_cached_project_detail(proj, slug, lang)
            return proj
    return None


# ---------------------------------------------------------------------------
# Public orchestration helpers (A1)
#
# Views used to hand-roll the ``if not x: x = _from_json(...)`` fallback at
# every call site. These wrappers centralise that logic so the fallback
# semantics (DB first, seed JSON fallback; Vercel served from JSON only) live
# in exactly one place. Rendering behaviour is unchanged.
# ---------------------------------------------------------------------------


def get_products(lang, active_category=None, active_series=None):
    """Return the product list for the products page.

    Local: database first, seed JSON fallback when the query fails or returns
    nothing. On Vercel (``IS_VERCEL``) the underlying loader already serves
    content from the committed seed JSON (stateless site).
    """
    cat = active_category or ''
    series = active_series or ''
    result = _get_products_from_db(lang, cat, series)
    if not result:
        result = _get_products_from_json(lang, cat, series)
    return result


def get_product_detail(slug, lang):
    """Return a single product (series or sub-series) or ``None``."""
    product = _get_product_detail_from_db(slug, lang)
    if product is None:
        product = _get_product_detail_from_json(slug, lang)
    return product


def get_projects(lang, active_venue_type=None, active_sport_type=None):
    """Return the project list for the projects page (DB first, JSON fallback)."""
    venue = active_venue_type or ''
    # Flattened to one string so the cache key stays hashable when a collection
    # page passes two sport values; _sport_filter_values() splits it back.
    sport = ','.join(_sport_filter_values(active_sport_type))
    result = _get_projects_from_db(lang, venue, sport)
    if not result:
        result = _get_projects_from_json(lang, venue, sport)
    return result


def get_project_detail(slug, lang):
    """Return a single project or ``None``."""
    project = _get_project_detail_from_db(slug, lang)
    if project is None:
        project = _get_project_detail_from_json(slug, lang)
    return project


#: NewsArticle fields that participate in translation. ``slug`` is a URL
#: fragment and ``image``/``content`` siblings are not translated — keeping the
#: tuple narrow is what lets a test pin the contract instead of trusting it.
NEWS_TRANSLATABLE_FIELDS = ('title', 'summary', 'content')
#: Extra dict keys the normalizer emits per language (``title_t`` & friends).
NEWS_TRANSLATED_KEYS = tuple(f'{f}_t' for f in NEWS_TRANSLATABLE_FIELDS)


def _news_translated(row, field, lang):
    """Return ``row[field]`` in ``lang``, falling back to the English value.

    ``pages.utils.translate()`` reads ``obj.translations`` off an *object*, but
    news rows are plain dicts on the seed path (and models on the DB path), so
    the lookup happens here rather than shimming a fake attribute onto the dict.
    Untranslated languages must fall back to English — otherwise a half-translated
    article renders blank on ``/ar/``, which is worse than an English article.

    ``row`` must already carry both ``translations`` and the English ``field``.
    """
    if not lang or lang == 'en':
        return row.get(field, '')
    tr = row.get('translations') or {}
    if isinstance(tr, str):
        try:
            tr = json.loads(tr)
        except (ValueError, TypeError):
            tr = {}
    val = (tr.get(lang) or {}).get(field, '') or ''
    return val or row.get(field, '')


def _news_translated_row(row, lang):
    """Return a copy of ``row`` with one ``<field>_t`` key per translatable field."""
    out = dict(row)
    for field in NEWS_TRANSLATABLE_FIELDS:
        out[f'{field}_t'] = _news_translated(row, field, lang)
    return out


def _news_social_image(row):
    """The image a social card / ``NewsArticle`` block should advertise.

    The cover is the natural pick, but an article does not have to have one:
    v1.10.6 stripped the three photographs from the market article and left
    only charts, and the template's old ``{{ article.image_url }}`` then rendered
    ``"image": "https://www.solaronelighting.com"`` in the JSON-LD (a bare
    origin -- consumers reject it) while ``og:image`` disappeared entirely,
    because the site-wide fallback is empty too. Both failures are silent.

    So: cover first, then the first gallery image, then nothing. Returning ''
    is a legitimate state -- the caller decides whether to omit the key or the
    whole meta tag, and a guard asserts the two agree.
    """
    if row.get('image_url'):
        return row['image_url']
    for image in row.get('images') or []:
        if image.get('url'):
            return image['url']
    return ''


def _normalize_news_image(i):
    """Normalize one seed ``news[].images[]`` entry to a template dict.

    The seed / admin shapes differ slightly (``alt`` vs ``alt_text``), so both
    aliases are accepted. ``width``/``height`` stay optional: the template only
    emits them when present (they are a CLS hint, never a resize instruction).

    ``id``/``name`` are kept because ``{{figure:…}}`` markers inside the body
    bind to them — see ``pages.views.news_body.build_article_body``.
    """
    return {
        'id': i.get('id') or '',
        'name': i.get('name') or '',
        'url': _static_url(i.get('image', '') or ''),
        'alt': i.get('alt') or i.get('alt_text') or '',
        'caption': i.get('caption') or '',
        'width': i.get('width') or None,
        'height': i.get('height') or None,
    }


def _normalize_news_article(a, lang='en'):
    """Normalize a seed ``news`` dict into the shape the template expects.

    The template renders ``article.published_at|date:"Y-m-d"`` (which requires a
    real ``datetime``) and ``article.image_url``. We parse the ISO ``published_at``
    string back into a datetime and resolve the image to a static URL so the seed
    path and the local-DB path present an identical interface to the template.

    ``images`` is normalized the same way as the DB path: a list of dicts with
    ``url``/``alt``/``caption`` (see ``_normalize_news_image``). Older seeds that
    only carry the single ``image`` key get an empty list and fall back to the
    legacy ``image_url`` rendering.

    ``lang`` selects the rendered ``<field>_t`` values (title/summary/content).
    Both the English keys and ``translations`` stay in the dict so sitemaps and
    the translation guards can still read the raw source.
    """
    raw = a.get('published_at', '') or ''
    published_at = raw
    try:
        published_at = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        published_at = raw
    images = [
        _normalize_news_image(i)
        for i in (a.get('images') or [])
        if i.get('image')
    ]
    row = {
        'slug': a.get('slug', ''),
        'title': a.get('title', ''),
        'category': a.get('category') or 'Exhibition Information',
        'summary': a.get('summary', ''),
        'content': a.get('content', ''),
        'published_at': published_at,
        'image_url': _static_url(a.get('image', '')),
        'images': images,
        'translations': a.get('translations') or {},
    }
    row = _news_translated_row(row, lang)
    # v1.10.4: interleave figures with the paragraphs they illustrate. Built
    # from the *translated* content so a translated body keeps its own
    # markers in place.
    blocks, unused = build_article_body(
        row.get('content_t') or row['content'], images)
    row['body_blocks'] = blocks
    row['unplaced_images'] = [images[i] for i in unused]
    row['social_image_url'] = _news_social_image(row)
    return row


_NEWS_ROW_BASE = (
    'slug',
    'title',
    'category',
    'summary',
    'content',
    'published_at',
    'image_url',
    'images',
    'translations',
)

#: Derived keys both paths append *after* the base normalizer, so the key set
#: of a news row is ``_NEWS_ROW_BASE`` + these + the ``<field>_t`` keys.
#: v1.10.4 in-body figures (``pages.views.news_body.build_article_body``):
#: the template renders ``body_blocks`` to interleave photos with paragraphs,
#: and ``unplaced_images`` carries gallery photos no marker referenced so a
#: forgotten marker degrades to the top grid instead of losing a photo.
#: v1.10.7 ``social_image_url``: the cover *or* the first gallery image, so an
#: article with no cover still advertises a real image in ``og:image`` and in
#: the ``NewsArticle`` block instead of a bare origin.
NEWS_DERIVED_KEYS = ('body_blocks', 'unplaced_images', 'social_image_url')


def _news_db_image_url(field):
    """Resolve a ``NewsImage.image`` / ``NewsArticle.image`` field to a URL.

    v1.10.4 — this used to be ``field.url``, i.e. Django's storage URL, which is
    ``MEDIA_URL``-rooted (``/media/…``). Every news photo in this project is
    actually committed under ``static/images/news/<slug>/``, so locally
    ``/media/images/news/…`` 404s: the file is in ``static/``, not in
    ``MEDIA_ROOT``. That is why the news detail page showed broken images while
    products and projects rendered fine — they resolve through
    ``_product_image_url`` / ``_project_image_url``, which go via ``_static_url``.

    So: resolve against ``static/`` first (identical to the seed path, which is
    what production reads), and only fall back to the storage URL when the file
    genuinely is not in the static tree. The fallback keeps real admin uploads
    working — those land in ``MEDIA_ROOT`` and exist nowhere under ``static/``.
    """
    if not field:
        return ''
    resolved = _static_url(field.name)
    if resolved and _find_static(_normalize_static_rel(field.name)):
        return resolved
    return field.url


def _normalize_news_row(a, lang='en'):
    """Serialize a ``NewsArticle`` row into the same dict the seed path builds.

    The DB rows are genuinely different objects (models) from the seed rows
    (plain dicts), but the template must not care: both hands it ``published_at``
    as a ``datetime``, ``image_url`` and the ``images`` list. Going through the
    same normalizer is what keeps the two paths from drifting apart.

    The key set is pinned to ``_NEWS_ROW_BASE`` + ``NEWS_DERIVED_KEYS`` + the
    ``<field>_t`` keys so a test can assert the two paths stay identical — a
    silently dropped ``translations`` key here would make admin edits vanish on
    Vercel while looking fine locally.
    """
    row = {
        'slug': a.slug,
        'title': a.title,
        'category': a.category,
        'summary': a.summary or '',
        'content': a.content,
        'published_at': a.published_at,
        'image_url': _news_db_image_url(a.image),
        'images': [
            {
                # v1.10.4: the PK is what a ``{{figure:…}}`` marker binds to.
                'id': im.pk,
                'name': '',
                'url': _news_db_image_url(im.image),
                'alt': im.alt_text or '',
                'caption': im.caption or '',
                'width': im.width or None,
                'height': im.height or None,
            }
            for im in a.images.all()
        ],
        'translations': a.translations or {},
    }
    out = _news_translated_row({k: row[k] for k in _NEWS_ROW_BASE}, lang)
    # Same interleave as the seed path — see `_normalize_news_article`.
    # The derived keys are added here, *not* in `_NEWS_ROW_BASE`, so the base
    # stays the plain serializable row and the pin test can still say "both
    # hands the template exactly the same keys".
    blocks, unused = build_article_body(
        out.get('content_t') or out['content'], out['images'])
    out['body_blocks'] = blocks
    out['unplaced_images'] = [out['images'][i] for i in unused]
    out['social_image_url'] = _news_social_image(out)
    return out


def _get_news_from_db(lang='en'):
    """Query published news articles from the DB. Returns [] on any failure.

    Prefetching matters here: a card renders one ``<img>`` per gallery row, so
    without ``prefetch_related`` every article would hit the DB again per photo.
    """
    return [
        _normalize_news_row(a, lang)
        for a in NewsArticle.objects.filter(is_published=True)
        .order_by('-published_at')
        .prefetch_related('images')
    ]


def _get_news_from_json(lang='en'):
    """Load published news articles from the committed seed JSON.

    v1.10.2: sorted newest-first explicitly. The order used to come straight
    from the JSON file, which only happened to be correct because ``seed_sync``
    writes it in ``NewsArticle.Meta.ordering`` (``-published_at``) order. That
    is a file-layout dependency, and a hand-edited seed would silently reverse
    the news list and the RSS feed. ISO-8601 strings sort chronologically as
    long as they share a format, which ``seed_sync`` guarantees.
    """
    seed_news = _load_seed().get('news', []) or []
    published = [a for a in seed_news if a.get('is_published', True)]
    published.sort(key=lambda a: a.get('published_at') or '', reverse=True)
    return [_normalize_news_article(a, lang) for a in published]


def get_news(lang):
    """Return the news-article list for the news page.

    On Vercel (``IS_VERCEL``) the site is stateless and content comes from the
    committed seed JSON. Locally we query the DB; if that fails we keep an empty
    list (mirrors the prior inline behaviour — no silent seed fallback), so the
    page degrades gracefully instead of erroring.
    """
    if getattr(settings, 'IS_VERCEL', False):
        return _get_news_from_json(lang)
    try:
        return _get_news_from_db(lang)
    except Exception:
        logger.warning('DB news query failed, returning empty list', exc_info=True)
        return []


def get_news_detail(slug, lang='en'):
    """Return one published news article as a dict, or ``None`` if unknown.

    Same duality as ``get_news``: seed JSON on Vercel (stateless), DB locally.
    The returned dict is the exact shape the list rows use (``<field>_t``
    translations, ``image_url``, ``images`` gallery), so the detail template is
    path-agnostic and cannot drift from the list cards.
    """
    if getattr(settings, 'IS_VERCEL', False):
        for a in _load_seed().get('news', []) or []:
            if a.get('slug') == slug and a.get('is_published', True):
                return _normalize_news_article(a, lang)
        return None
    try:
        article = (
            NewsArticle.objects
            .filter(slug=slug, is_published=True)
            .prefetch_related('images')
            .get()
        )
    except NewsArticle.DoesNotExist:
        return None
    except Exception:
        logger.warning('DB news detail query failed', exc_info=True)
        return None
    return _normalize_news_row(article, lang)