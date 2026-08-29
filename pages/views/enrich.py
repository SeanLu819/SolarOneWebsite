import logging
from types import SimpleNamespace
from django.conf import settings
from django.templatetags.static import static
from django.utils.translation import gettext as _
from pages.models import Product, ProductImage, Project, ProjectImage
from .utils import (
    _find_static, _static_url, _dict_product_image_url, _product_image_url,
    _project_image_url, _project_gallery_urls, _find_project_cover_path,
    _DictProduct, _DictProject,
)
from .i18n import _PRODUCT_CARD_LABELS, _PRODUCT_CAT_TO_SIDEBAR_LABEL, _t

logger = logging.getLogger(__name__)

_enriched_products_cache = {}
_enriched_projects_cache = {}
_enriched_product_detail_cache = {}
_enriched_project_detail_cache = {}


def _cache_key_products(lang, active_category='', active_series=''):
    return f'{lang}|{active_category}|{active_series}'


def _cache_key_projects(lang, active_venue_type='', active_sport_type=''):
    return f'{lang}|{active_venue_type}|{active_sport_type}'


def _get_cached_products(lang, active_category='', active_series=''):
    key = _cache_key_products(lang, active_category, active_series)
    return _enriched_products_cache.get(key)


def _set_cached_products(products, lang, active_category='', active_series=''):
    key = _cache_key_products(lang, active_category, active_series)
    _enriched_products_cache[key] = products


def _get_cached_projects(lang, active_venue_type='', active_sport_type=''):
    key = _cache_key_projects(lang, active_venue_type, active_sport_type)
    return _enriched_projects_cache.get(key)


def _set_cached_projects(projects, lang, active_venue_type='', active_sport_type=''):
    key = _cache_key_projects(lang, active_venue_type, active_sport_type)
    _enriched_projects_cache[key] = projects


def _get_cached_product_detail(slug, lang):
    key = f'{slug}|{lang}'
    return _enriched_product_detail_cache.get(key)


def _set_cached_product_detail(product, slug, lang):
    key = f'{slug}|{lang}'
    _enriched_product_detail_cache[key] = product


def _get_cached_project_detail(slug, lang):
    key = f'{slug}|{lang}'
    return _enriched_project_detail_cache.get(key)


def _set_cached_project_detail(project, slug, lang):
    key = f'{slug}|{lang}'
    _enriched_project_detail_cache[key] = project


def invalidate_enrichment_cache():
    """Clear all enrichment caches. Call when seed data changes."""
    global _enriched_products_cache, _enriched_projects_cache
    global _enriched_product_detail_cache, _enriched_project_detail_cache
    from .utils import _dir_listing_cache, _static_file_set
    _enriched_products_cache = {}
    _enriched_projects_cache = {}
    _enriched_product_detail_cache = {}
    _enriched_project_detail_cache = {}
    _dir_listing_cache = {}
    _static_file_set = None


def _build_specs(obj):
    """Build a list of spec dicts from a product-like object."""
    spec_fields = [
        ('power', _('Power')),
        ('efficacy', _('Efficacy')),
        ('output', _('Output')),
        ('beam_angle', _('Beam Angle')),
        ('protection', _('Protection')),
    ]
    specs = []
    for field, label in spec_fields:
        value = getattr(obj, field, '')
        if value:
            specs.append({'value': value, 'label': label})
    return specs


def _enrich_product(product, lang):
    """Add template-friendly attributes to a Product or _DictProduct."""
    product.name_t = product.t('name', lang)
    product.description_t = product.t('description', lang)
    product.category_t = product.t('category', lang)
    card_label = _PRODUCT_CARD_LABELS.get(product.slug) or _PRODUCT_CAT_TO_SIDEBAR_LABEL.get(product.category, product.category_t)
    product.category_display = _t(card_label, lang)

    raw_specs = getattr(product, 'specs', None)
    if raw_specs:
        product.specs = [
            {'label': str(_(s.get('label', ''))), 'value': str(s.get('value', ''))}
            for s in raw_specs
            if s and (s.get('label') or s.get('value'))
        ]
    else:
        product.specs = _build_specs(product)

    if isinstance(product, Product):
        product.image_url = _product_image_url(product, 'image')
        product.banner_image_url = _product_image_url(product, 'banner_image')
        product.dimension_image_url = _product_image_url(product, 'dimension_image')
        product.beam_angle_image_url = _product_image_url(product, 'beam_angle_image')
        product.ordering_image_url = _product_image_url(product, 'ordering_image')
        cert_url = _product_image_url(product, 'cert_image')
        if not cert_url and product.category != 'ACCESSORY':
            cert_default = 'images/products/m-series-certs.webp'
            if _find_static(cert_default):
                cert_url = static(cert_default)
        product.cert_image_url = cert_url
        product.gallery = [
            {
                'src': _product_image_url(
                    SimpleNamespace(slug=getattr(product, 'slug', ''), image=img.image),
                    'image'
                ),
                'alt': img.alt_text or f"{product.name_t} — view {i + 1}",
            }
            for i, img in enumerate(product.images.all())
        ]
        product.parent_slug = product.parent.slug if product.parent else ''
    else:
        slug = getattr(product, 'slug', '')
        product.image_url = _dict_product_image_url(product.image, slug)
        product.banner_image_url = _dict_product_image_url(product.banner_image, slug)
        product.dimension_image_url = _dict_product_image_url(product.dimension_image, slug)
        product.beam_angle_image_url = _dict_product_image_url(product.beam_angle_image, slug)
        product.ordering_image_url = _dict_product_image_url(product.ordering_image, slug)
        cert_url = _dict_product_image_url(getattr(product, 'cert_image', ''), slug) if hasattr(product, 'cert_image') else ''
        if not cert_url and getattr(product, 'category', '') != 'ACCESSORY':
            cert_default = 'images/products/m-series-certs.webp'
            if _find_static(cert_default):
                cert_url = static(cert_default)
        product.cert_image_url = cert_url
        product.gallery = [
            {'src': _dict_product_image_url(p, slug), 'alt': f"{product.name_t} — view {i + 1}"}
            for i, p in enumerate(product.gallery_paths)
        ]
        if not product.parent_slug:
            product.parent_slug = ''

    raw_ordering = getattr(product, 'ordering_info', None) or []
    if raw_ordering:
        product.ordering_cols = []
        for col in raw_ordering:
            if col:
                lines = [ln.strip() for ln in col.split('\n') if ln.strip()]
                product.ordering_cols.append(lines)
            else:
                product.ordering_cols.append([])
    else:
        product.ordering_cols = []


_COMPARE_IMAGE_SLUGS = frozenset({
    'football-field-led-retrofit',
})


def _enrich_project(project, lang):
    """Add template-friendly attributes to a Project or _DictProject."""
    project.title_t = project.t('title', lang)
    project.description_t = project.t('description', lang)
    project.location_t = project.t('location', lang)
    project.results_t = project.t('results', lang)

    slug = getattr(project, 'slug', '')
    project.has_compare_images = slug in _COMPARE_IMAGE_SLUGS

    if isinstance(project, Project):
        project.image_url = _project_image_url(project.image, slug)
        pdf_static = getattr(project, 'pdf_static', '') or ''
        if pdf_static:
            project.pdf_url = static(pdf_static)
        elif project.pdf_file:
            project.pdf_url = project.pdf_file.url
        else:
            project.pdf_url = ''
        db_images = list(project.images.all())
        if db_images:
            project.gallery = [
                {
                    'src': _project_image_url(img.image, slug),
                    'alt': img.alt_text or f"{project.title_t} — view {i + 1}",
                }
                for i, img in enumerate(db_images)
            ]
        else:
            static_gal_urls = _project_gallery_urls(project)
            project.gallery = [
                {'src': src, 'alt': f"{project.title_t} — view {i + 1}"}
                for i, src in enumerate(static_gal_urls)
            ]
    else:
        seed_image = getattr(project, 'image', '')
        cover = _find_project_cover_path(slug, seed_image) if slug else ''
        if cover:
            project.image_url = _static_url(cover)
        else:
            project.image_url = _static_url(seed_image)
        if not project.image_url and slug:
            cover = _find_project_cover_path(slug, getattr(project, 'image', ''))
            if cover:
                project.image_url = _static_url(cover)

        pdf_raw = getattr(project, 'pdf_url', '')
        if pdf_raw:
            project.pdf_url = _static_url(pdf_raw)
        else:
            project.pdf_url = ''

        seed_gal_paths = list(getattr(project, 'gallery_paths', []) or [])
        if seed_gal_paths:
            gal_urls = [_static_url(p) for p in seed_gal_paths if p]
            gal_urls = [u for u in gal_urls if u]
        else:
            static_gal_urls = _project_gallery_urls(slug) if slug else []
            gal_urls = static_gal_urls
        project.gallery = [
            {'src': src, 'alt': f"{project.title_t} — view {i + 1}"}
            for i, src in enumerate(gal_urls)
        ]