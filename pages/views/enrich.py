import logging
from types import SimpleNamespace
from django.templatetags.static import static
from django.utils.translation import gettext as _
from pages.models import Product, Project
from .utils import (
    _find_static, _static_url, _dict_product_image_url, _product_image_url,
    _project_image_url, _project_gallery_urls, _find_project_cover_path,
    _db_product_cover_url, _db_project_cover_url,
    _DictProduct, _DictProject,
)
from .i18n import _PRODUCT_CARD_LABELS, _PRODUCT_CAT_TO_SIDEBAR_LABEL, _t

logger = logging.getLogger(__name__)

# Shared certification badge used when a product has no per-product cert image.
# v1.9.8: the old fallback pointed at `m-series-flood-light-certifications.webp`,
# which does not exist on disk (verified 404 live2026-10-03) — so every product
# with an empty cert_image silently rendered NO badge at all. Keep this pointing
# at a file that actually exists; `test_cert_fallback_points_at_a_real_file`
# guards against reintroducing a dead path.
DEFAULT_CERT_IMAGE = 'images/products/m-series/certifications-ul-dlc-gs-ce-ip66.webp'

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
    """Clear all enrichment caches. Call when seed data changes.

    🔴 v1.10.15 — 这一段以前是**空操作**。原实现写着：

        from .utils import _dir_listing_cache, _static_file_set
        _dir_listing_cache = {}      # ← 局部重绑定
        _static_file_set = None      # ← 局部重绑定

    `from ... import` 只把名字绑到函数局部作用域，随后的赋值新建局部对象，
    `utils` 里真正的字典/变量分毫未动（上面四个 `_enriched_*_cache` 有
    `global` 声明，所以那四个是真清了 —— 不对称正是它长期没被发现的原因）。

    后果只在**长驻进程**里显现，测试永远看不见（每个测试进程缓存都是空的）：
    admin 上传图片写进 `static/` 后，`models.sync_project_on_save` 调到这里，
    目录列表缓存原封不动 → 早于上传那次请求缓存的空集继续命中 →
    `_find_project_gallery_files()` 返回 `[]` →
    `_find_project_cover_path()` 一路降到 `images/projects/gallery` 兜底 →
    页面渲染出 collectstatic 快照里的路径 → 404（2026-10-04 源深体育场现场）。

    现在统一走 `utils.clear_static_caches()`：状态的所有者自己清，且是
    `.clear()` 原地清，不是重新绑定。
    """
    global _enriched_products_cache, _enriched_projects_cache
    global _enriched_product_detail_cache, _enriched_project_detail_cache
    from .utils import clear_static_caches
    _enriched_products_cache = {}
    _enriched_projects_cache = {}
    _enriched_product_detail_cache = {}
    _enriched_project_detail_cache = {}
    clear_static_caches()


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


def _gallery_alt(base, qualifier, i):
    """Descriptive gallery alt text for image ``i`` (0-based).

    The seed product names ("M Series", "RT410 Series") contain no
    category/type words, so the bare ``"<name> — view N"`` carried almost no
    text for SEO. ``qualifier`` is the product category display or the project
    location — real text we already hold — and is folded in when present. When
    it is empty we fall back to the original string so no alt is ever
    ``" — view N"``.
    """
    if qualifier:
        return f'{base} — {qualifier} — view {i + 1}'
    return f'{base} — view {i + 1}'


def _enrich_product(product, lang):
    """Add template-friendly attributes to a Product or _DictProduct."""
    product.name_t = product.t('name', lang)
    product.description_t = product.t('description', lang)
    product.category_t = product.t('category', lang)
    product.seo_title_t = product.seo_title(lang)
    product.seo_description_t = product.seo_description(lang)
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
        product.image_url = _db_product_cover_url(product)
        product.banner_image_url = _product_image_url(product, 'banner_image')
        product.dimension_image_url = _product_image_url(product, 'dimension_image')
        product.beam_angle_image_url = _product_image_url(product, 'beam_angle_image')
        product.ordering_image_url = _product_image_url(product, 'ordering_image')
        cert_url = _product_image_url(product, 'cert_image')
        if not cert_url and product.category != 'ACCESSORY':
            if _find_static(DEFAULT_CERT_IMAGE):
                cert_url = static(DEFAULT_CERT_IMAGE)
        product.cert_image_url = cert_url
        product.gallery = [
            {
                'src': _product_image_url(
                    SimpleNamespace(slug=getattr(product, 'slug', ''), image=img.image),
                    'image'
                ),
                'alt': img.alt_text or _gallery_alt(
                    product.name_t, getattr(product, 'category_display', ''), i),
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
            if _find_static(DEFAULT_CERT_IMAGE):
                cert_url = static(DEFAULT_CERT_IMAGE)
        product.cert_image_url = cert_url
        product.gallery = [
            {'src': _dict_product_image_url(p, slug),
             'alt': _gallery_alt(product.name_t, getattr(product, 'category_display', ''), i)}
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
    project.seo_title_t = project.seo_title(lang)
    project.seo_description_t = project.seo_description(lang)
    # og:description uses the unclamped full-name form — the meta description
    # is cut to 160 chars for the SERP, which would leave a shared card ending
    # in an ellipsis. Set on both Project and _DictProject (both expose the
    # method); template falls back defensively if an object predates this.
    project.og_description_t = project.og_description(lang)

    slug = getattr(project, 'slug', '')
    project.has_compare_images = slug in _COMPARE_IMAGE_SLUGS

    if isinstance(project, Project):
        project.image_url = _db_project_cover_url(project)
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
                    'alt': img.alt_text or _gallery_alt(
                        project.title_t, getattr(project, 'location_t', ''), i),
                }
                for i, img in enumerate(db_images)
            ]
        else:
            static_gal_urls = _project_gallery_urls(project)
            project.gallery = [
                {'src': src,
                 'alt': _gallery_alt(project.title_t, getattr(project, 'location_t', ''), i)}
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
            {'src': src,
             'alt': _gallery_alt(project.title_t, getattr(project, 'location_t', ''), i)}
            for i, src in enumerate(gal_urls)
        ]