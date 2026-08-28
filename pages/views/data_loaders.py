import logging
from pages.models import Product, Project
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