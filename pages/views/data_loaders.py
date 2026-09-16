import logging
from datetime import datetime

from django.conf import settings
from pages.models import Product, Project, NewsArticle
from .utils import _load_seed, _DictProduct, _DictProject
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
        if active_sport_type:
            projects_list = projects_list.filter(sport_type=active_sport_type)
        result = []
        for proj in projects_list:
            _enrich_project(proj, lang)
            result.append(proj)
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
    for item in items:
        if active_venue_type and item.get('venue_type') != active_venue_type:
            continue
        if active_sport_type and item.get('sport_type') != active_sport_type:
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
    sport = active_sport_type or ''
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


def _normalize_news_article(a):
    """Normalize a seed ``news`` dict into the shape the template expects.

    The template renders ``article.published_at|date:"Y-m-d"`` (which requires a
    real ``datetime``) and ``article.image_url``. We parse the ISO ``published_at``
    string back into a datetime and resolve the image to a static URL so the seed
    path and the local-DB path present an identical interface to the template.
    """
    raw = a.get('published_at', '') or ''
    published_at = raw
    try:
        published_at = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        published_at = raw
    return {
        'slug': a.get('slug', ''),
        'title': a.get('title', ''),
        'summary': a.get('summary', ''),
        'content': a.get('content', ''),
        'published_at': published_at,
        'image_url': _static_url(a.get('image', '')),
    }


def _get_news_from_db():
    """Query published news articles from the DB. Returns [] on any failure."""
    articles = list(
        NewsArticle.objects.filter(is_published=True).order_by('-published_at')
    )
    for a in articles:
        a.image_url = a.image.url if a.image else ''
    return articles


def _get_news_from_json():
    """Load published news articles from the committed seed JSON."""
    seed_news = _load_seed().get('news', []) or []
    return [
        _normalize_news_article(a)
        for a in seed_news
        if a.get('is_published', True)
    ]


def get_news(lang):
    """Return the news-article list for the news page.

    On Vercel (``IS_VERCEL``) the site is stateless and content comes from the
    committed seed JSON. Locally we query the DB; if that fails we keep an empty
    list (mirrors the prior inline behaviour — no silent seed fallback), so the
    page degrades gracefully instead of erroring.
    """
    if getattr(settings, 'IS_VERCEL', False):
        return _get_news_from_json()
    try:
        return _get_news_from_db()
    except Exception:
        logger.warning('DB news query failed, returning empty list', exc_info=True)
        return []