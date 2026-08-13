import os
import re
import json
import logging
from types import SimpleNamespace
from pathlib import Path
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.paginator import Paginator
from django.templatetags.static import static
from django.utils.translation import get_language, gettext as _
from django.conf import settings
from pages.models import Product, ProductImage, Project, ProjectImage, SiteConfig, ContactMessage, NewsArticle

logger = logging.getLogger(__name__)

# Path to seed data — used as fallback when DB is unavailable (e.g. Vercel ephemeral SQLite)
_SEED_CANDIDATES = [
    os.path.join(settings.BASE_DIR, 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data.json'),
]


# Product card display labels (per slug, matching sidebar category names)
# Maps each product slug to its card label. Falls back to category-based label.
_PRODUCT_CARD_LABELS = {
    'm-series': 'Area and Site',
    'rt410-series': 'Area and Site',
    'rt400-series': 'Highbay & Low Bay',
    'vsp-xxxxw-9m-yp': 'Sports Lighting System',
    'vsp-xxxxw-12m-yp': 'Flood Lighting',
    'fl1m': 'Roadway',
    'rt590fl-s': 'Flood Lighting',
    'rt600sl-t': 'Roadway',
}

# Product category → sidebar category display label mapping
# Reverses _SIDEBAR_CAT_TO_PRODUCT_CAT for display on product cards.
_PRODUCT_CAT_TO_SIDEBAR_LABEL = {
    'AREA_SITE': 'Area and Site',
    'ACCESSORY': 'Area and Site',
    'SPORTS_LIGHTING': 'Sports Lighting System',
    'FLOODLIGHT': 'Flood Lighting',
    'HIGHBAY_LOWBAY': 'Highbay & Low Bay',
    'ROADWAY': 'Roadway',
}


# Sidebar category keys map to one or more Product.category values
_SIDEBAR_CAT_TO_PRODUCT_CAT = {
    'AREA_SITE': ['AREA_SITE', 'ACCESSORY'],
    'SPORTS_LIGHTING_SYSTEM': ['SPORTS_LIGHTING'],
    'FLOODLIGHTING': ['FLOODLIGHT'],
    'HIGHBAY_LOWBAY': ['HIGHBAY_LOWBAY'],
    'ROADWAY': ['ROADWAY'],
}


def _load_seed():
    """Load seed data. On Vercel, import from the embedded Python module
    (pages.seed_data) so no filesystem access is needed. In local dev, fall
    back to reading seed_data.json from disk so the JSON stays the source of
    truth during development."""
    data = cache.get('seed_data_json')
    if data is None:
        try:
            from pages.seed_data import SEED_DATA
            data = SEED_DATA
        except Exception:
            logger.warning('Could not import pages.seed_data, trying JSON file', exc_info=True)
            data = None

        if data is None:
            for path in _SEED_CANDIDATES:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    break
                except Exception:
                    continue
            if data is None:
                logger.warning('Failed to load seed data from any source', exc_info=True)
                data = {'products': [], 'projects': [], 'siteconfig': {}}
        cache.set('seed_data_json', data, timeout=300)
    return data


# ============================================================================
# Lightweight wrappers that mimic the model interface for seed JSON fallback
# ============================================================================

class _DictProduct:
    def __init__(self, item):
        self.slug = item.get('slug', '')
        self.name = item.get('name', '')
        self.category = item.get('category', '')
        self.description = item.get('description', '')
        self.power = item.get('power', '')
        self.efficacy = item.get('efficacy', '')
        self.protection = item.get('protection', '')
        self.output = item.get('output', '')
        self.beam_angle = item.get('beam_angle', '')
        self.image = item.get('image', '')
        self.banner_image = item.get('banner_image', '')
        self.dimension_image = item.get('dimension_image', '')
        self.beam_angle_image = item.get('beam_angle_image', '')
        self.order = item.get('order', 0)
        self.translations = item.get('translations', {}) or {}
        self.parent_slug = item.get('parent_slug', '')
        self.gallery_paths = item.get('gallery', [])
        self.specs = item.get('specs', []) or []
        self.energy_data = item.get('energy_data', []) or []
        self.model_number = item.get('model_number', '')
        self.ordering_info = item.get('ordering_info', []) or []

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


class _DictProject:
    def __init__(self, item):
        self.slug = item.get('slug', '')
        self.title = item.get('title', '')
        self.location = item.get('location', '')
        self.venue_type = item.get('venue_type', '')
        self.sport_type = item.get('sport_type', '')
        self.description = item.get('description', '')
        self.results = item.get('results', '')
        self.image = item.get('image', '')
        self.order = item.get('order', 0)
        self.translations = item.get('translations', {}) or {}
        self.gallery_paths = item.get('gallery', [])
        self.pdf_url = item.get('pdf_url', '')

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


# ============================================================================
# Enrichment helpers (set translated fields, image URLs, galleries, specs)
# ============================================================================

def _media_url(field):
    """Return the URL for an ImageField file, or '' if empty."""
    if field and field.name:
        return field.url
    return ''


def _static_url(path):
    """Return static URL for a non-empty path.
    Strips 'images/' prefix from paths like 'images/processed/xxx.webp'
    so they resolve correctly under /static/images/ on Vercel.
    """
    if not path:
        return ''
    if path.startswith('images/'):
        return static(path)
    if path.startswith('products/'):
        return static(path)
    return static(path)


def _clean_hashed_name(name: str) -> str:
    """Strip Django-upload hashed suffix like _yPJsGNE from filename."""
    stem = name.rsplit('.', 1)[0]
    ext = name.rsplit('.', 1)[-1]
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]
    return f'{stem}.{ext}'


def _map_project_image(db_path: str) -> str:
    """Map DB media path to static path for a project main image."""
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    clean_name = _clean_hashed_name(name)
    if clean_name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        return f'images/processed/{clean_name}'
    if clean_name in ('home-project.webp',):
        return f'images/{clean_name}'
    return f'images/processed/{clean_name}'


def _map_project_gallery(db_path: str) -> str:
    """Map DB media path to static path for a project gallery image."""
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    clean_name = _clean_hashed_name(name)
    if clean_name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        return f'images/processed/{clean_name}'
    if clean_name in ('home-project.webp',):
        return f'images/{clean_name}'
    return f'images/processed/{clean_name}'


def _project_image_url(field):
    """Return image URL, preferring committed static assets when available."""
    if not field or not field.name:
        return ''
    mapped = _map_project_image(field.name)
    if mapped and finders.find(mapped):
        return static(mapped)
    media_full = os.path.join(settings.MEDIA_ROOT, field.name)
    if os.path.exists(media_full):
        return field.url
    return field.url


def _product_image_url(product, field_name):
    """Return the best image URL for a product field.

    We prefer committed static assets under static/images/ because those are the
    canonical images checked into the repo and are stable across local dev and
    Vercel. If no static asset exists, fall back to the uploaded media file URL.
    """
    field = getattr(product, field_name, None)
    if not field or not getattr(field, 'name', None):
        return ''

    slug = getattr(product, 'slug', '')
    field_name_value = str(field.name).replace('\\', '/')
    filename = Path(field_name_value).name
    stem = Path(filename).stem

    candidates = []
    if field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value}')
    if slug and filename:
        candidates.append(f'images/products/{slug}/{filename}')
    if filename:
        candidates.append(f'images/products/{filename}')
    if slug and stem:
        candidates.append(f'images/products/{slug}/{stem}.webp')
    if stem and field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value.rsplit(".", 1)[0]}.webp')

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if finders.find(candidate):
            return static(candidate)

    media_url = getattr(field, 'url', '')
    if media_url:
        return media_url

    media_full = os.path.join(settings.MEDIA_ROOT, field_name_value)
    if os.path.exists(media_full):
        return f'/media/{field_name_value.lstrip("/")}'
    return ''


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
    # Use per-slug label if defined, otherwise fall back to category-based label
    card_label = _PRODUCT_CARD_LABELS.get(product.slug) or _PRODUCT_CAT_TO_SIDEBAR_LABEL.get(product.category, product.category_t)
    product.category_display = _t(card_label, lang)

    # Prefer flexible specs JSON; fall back to legacy fields for old records.
    # Spec labels are stored in English in seed data; translate them via _()
    # so they render in the active language.
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
        product.image_url = _static_url(product.image)
        product.banner_image_url = _static_url(product.banner_image)
        product.dimension_image_url = _static_url(product.dimension_image)
        product.beam_angle_image_url = _static_url(product.beam_angle_image)
        product.gallery = [
            {'src': _static_url(p), 'alt': f"{product.name_t} — view {i + 1}"}
            for i, p in enumerate(product.gallery_paths)
        ]
        if not product.parent_slug:
            product.parent_slug = ''

    # Pre-process ordering_info for template rendering.
    # Each column is rendered as a single <td>; multi-line values use <br>.
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


def _enrich_project(project, lang):
    """Add template-friendly attributes to a Project or _DictProject."""
    project.title_t = project.t('title', lang)
    project.description_t = project.t('description', lang)
    project.location_t = project.t('location', lang)
    project.results_t = project.t('results', lang)

    if isinstance(project, Project):
        project.image_url = _project_image_url(project.image)
        # pdf_static lives in static/files/ (deployed with the app — preferred on Vercel).
        # pdf_file lives in media/ (not served on Vercel).
        pdf_static = getattr(project, 'pdf_static', '') or ''
        if pdf_static:
            project.pdf_url = static(pdf_static)
        elif project.pdf_file:
            project.pdf_url = project.pdf_file.url
        else:
            project.pdf_url = ''
        project.gallery = [
            {
                'src': _project_image_url(img.image),
                'alt': img.alt_text or f"{project.title_t} — view {i + 1}",
            }
            for i, img in enumerate(project.images.all())
        ]
    else:
        project.image_url = _static_url(project.image)
        project.pdf_url = _static_url(project.pdf_url) if project.pdf_url else ''
        project.gallery = [
            {'src': _static_url(p), 'alt': f"{project.title_t} — view {i + 1}"}
            for i, p in enumerate(project.gallery_paths)
        ]


# ============================================================================
# Product list helpers
# ============================================================================

def _product_category_filter(active_category):
    """Return a list of Product.category values for a sidebar category key."""
    return _SIDEBAR_CAT_TO_PRODUCT_CAT.get(active_category, [active_category])


def _get_products_from_db(lang, active_category='', active_series=''):
    """Try loading products from DB. Returns None on failure."""
    try:
        products_list = Product.objects.filter(parent__isnull=True)
        if active_category:
            products_list = products_list.filter(category__in=_product_category_filter(active_category))
        if active_series:
            products_list = products_list.filter(slug=active_series)
        products_list = products_list.order_by('order')
        result = []
        for p in products_list:
            _enrich_product(p, lang)
            result.append(p)
        return result
    except Exception:
        logger.warning('DB products query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_products_from_json(lang, active_category='', active_series=''):
    """Load products from seed_data.json (fallback for Vercel)."""
    data = _load_seed()
    items = data.get('products', [])
    result = []
    for item in items:
        if item.get('parent_slug'):
            continue
        if active_category and item.get('category') not in _product_category_filter(active_category):
            continue
        if active_series and item.get('slug') != active_series:
            continue
        p = _DictProduct(item)
        _enrich_product(p, lang)
        result.append(p)
    result.sort(key=lambda p: getattr(p, 'order', 0) or 0)
    return result


# ============================================================================
# Product detail helpers
# ============================================================================

def _get_product_detail_from_db(slug, lang):
    """Try loading a single product from DB. Returns None on failure."""
    try:
        product = Product.objects.select_related('parent').prefetch_related('images').get(slug=slug)
        _enrich_product(product, lang)
        return product
    except Product.DoesNotExist:
        return None
    except Exception:
        logger.warning('DB product detail query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_product_detail_from_json(slug, lang):
    """Load a single product from seed_data.json (fallback for Vercel)."""
    data = _load_seed()
    for item in data.get('products', []):
        if item.get('slug') == slug:
            p = _DictProduct(item)
            _enrich_product(p, lang)
            return p
    return None


# ============================================================================
# Project list helpers
# ============================================================================

def _get_projects_from_db(lang, active_venue_type='', active_sport_type=''):
    """Try loading projects from DB. Returns None on failure."""
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
        return result
    except Exception:
        logger.warning('DB projects query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_projects_from_json(lang, active_venue_type='', active_sport_type=''):
    """Load projects from seed_data.json (fallback for Vercel)."""
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
    return result


def _get_project_detail_from_db(slug, lang):
    """Try loading a single project from DB. Returns None on failure."""
    try:
        project = Project.objects.prefetch_related('images').get(slug=slug)
        _enrich_project(project, lang)
        return project
    except Project.DoesNotExist:
        return None
    except Exception:
        logger.warning('DB project detail query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_project_detail_from_json(slug, lang):
    """Load a single project from seed_data.json (fallback for Vercel)."""
    data = _load_seed()
    for item in data.get('projects', []):
        if item.get('slug') == slug:
            proj = _DictProject(item)
            _enrich_project(proj, lang)
            return proj
    return None


# ============================================================================
# Sidebar i18n
# ============================================================================

_SIDEBAR_I18N = {
    # Projects — venue types
    'Outdoor Sports':  {'fr': 'Sports Extérieur', 'es': 'Deportes Exterior', 'de': 'Outdoor-Sport', 'ar': 'رياضات خارجية', 'ru': 'Спорт на открытом воздухе'},
    'Indoor Sports':   {'fr': 'Sports Intérieur', 'es': 'Deportes Interior', 'de': 'Indoor-Sport', 'ar': 'رياضات داخلية', 'ru': 'Спорт в закрытом помещении'},
    'Airports and Ports': {'fr': 'Aéroports et Ports', 'es': 'Aeropuertos y Puertos', 'de': 'Flughäfen und Häfen', 'ar': 'المطارات والموانئ', 'ru': 'Аэропорты и порты'},
    'Winter Sports':    {'fr': 'Sports d\'Hiver', 'es': 'Deportes de Invierno', 'de': 'Wintersport', 'ar': 'الرياضات الشتوية', 'ru': 'Зимние виды спорта'},
    # Projects — sport types
    'Football Field':   {'fr': 'Terrain de Football', 'es': 'Campo de Fútbol', 'de': 'Fußballplatz', 'ar': 'ملعب كرة قدم', 'ru': 'Футбольное поле'},
    'Soccer Field':     {'fr': 'Terrain de Soccer', 'es': 'Campo de Fútbol', 'de': 'Fußballplatz', 'ar': 'ملعب كرة القدم', 'ru': 'Футбольное поле'},
    'Baseball Field':   {'fr': 'Terrain de Baseball', 'es': 'Campo de Béisbol', 'de': 'Baseballfeld', 'ar': 'ملعب بيسبول', 'ru': 'Бейсбольное поле'},
    'Tennis Courts':    {'fr': 'Courts de Tennis', 'es': 'Canchas de Tenis', 'de': 'Tennisplätze', 'ar': 'ملعب تنس', 'ru': 'Теннисные корты'},
    'Ice Arena':        {'fr': 'Patinoire', 'es': 'Pista de Hielo', 'de': 'Eisarena', 'ar': 'حلبة جليدية', 'ru': 'Ледовая арена'},
    'Ski Area':         {'fr': 'Domaine skiable', 'es': 'Área de Esquí', 'de': 'Skigebiet', 'ar': 'منطقة التزلج', 'ru': 'Горнолыжный курорт'},
    'Stadium':          {'fr': 'Stade', 'es': 'Estadio', 'de': 'Stadion', 'ar': 'استاد', 'ru': 'Стадион'},
    'Basketball':       {'fr': 'Basketball', 'es': 'Baloncesto', 'de': 'Basketball', 'ar': 'كرة السلة', 'ru': 'Баскетбол'},
    'Volleyball':       {'fr': 'Volleyball', 'es': 'Voleibol', 'de': 'Volleyball', 'ar': 'كرة الطائرة', 'ru': 'Волейбол'},
    'Tennis':           {'fr': 'Tennis', 'es': 'Tenis', 'de': 'Tennis', 'ar': 'تنس', 'ru': 'Теннис'},
    'Multi-Sport Arena':{'fr': 'Complexe Multi-Sports', 'es': 'Pista Polideportiva', 'de': 'Mehrzweckhalle', 'ar': 'صالة متعددة الرياضات', 'ru': 'Универсальный спортивный зал'},
    'Airport':          {'fr': 'Aéroport', 'es': 'Aeropuerto', 'de': 'Flughafen', 'ar': 'مطار', 'ru': 'Аэропорт'},
    'Seaport':          {'fr': 'Port Maritime', 'es': 'Puerto', 'de': 'Seehafen', 'ar': 'ميناء بحري', 'ru': 'Морской порт'},
    # Products — categories
    'Area and Site':            {'fr': 'Zone et Site', 'es': 'Área y Sitio', 'de': 'Bereich und Standort', 'ar': 'المنطقة والموقع', 'ru': 'Территория и площадка'},
    'Sports Lighting System': {'fr': 'Système d\'Éclairage Sportif', 'es': 'Sistema de Iluminación Deportiva', 'de': 'Sportbeleuchtungssystem', 'ar': 'نظام إضاءة رياضية', 'ru': 'Система спортивного освещения'},
    'Flood Lighting':           {'fr': 'Projecteurs', 'es': 'Proyectores', 'de': 'Flutlicht', 'ar': 'إضاءة فيضانية', 'ru': 'Прожекторное освещение'},
    'Highbay & Low Bay':        {'fr': 'Haute & Basse Baie', 'es': 'Alta & Baja Bahía', 'de': 'Highbay & Lowbay', 'ar': 'إضاءة عالية ومنخفضة', 'ru': 'Высокий и низкий пролёт'},
    'Roadway':                  {'fr': 'Éclairage Routier', 'es': 'Alumbrado Vial', 'de': 'Straßenbeleuchtung', 'ar': 'إنارة الطرق', 'ru': 'Дорожное освещение'},
    'Accessory':                {'fr': 'Accessoire', 'es': 'Accesorio', 'de': 'Zubehör', 'ar': 'ملحق', 'ru': 'Аксессуар'},
    # Products — series
    'M Series':         {'fr': 'Série M', 'es': 'Serie M', 'de': 'M-Serie', 'ar': 'سلسلة M', 'ru': 'Серия M'},
    'RT410 Series':     {'fr': 'Série RT410', 'es': 'Serie RT410', 'de': 'RT410-Serie', 'ar': 'سلسلة RT410', 'ru': 'Серия RT410'},
    'HB Series':        {'fr': 'Série HB', 'es': 'Serie HB', 'de': 'HB-Serie', 'ar': 'سلسلة HB', 'ru': 'Серия HB'},
    'RT750 Series':     {'fr': 'Série RT750', 'es': 'Serie RT750', 'de': 'RT750-Serie', 'ar': 'سلسلة RT750', 'ru': 'Серия RT750'},
    'RT1060 Series':    {'fr': 'Série RT1060', 'es': 'Serie RT1060', 'de': 'RT1060-Serie', 'ar': 'سلسلة RT1060', 'ru': 'Серия RT1060'},
    # Sub-series spec labels
    'Illumination':         {'fr': 'Illumination', 'es': 'Iluminación', 'de': 'Beleuchtung', 'ar': 'الإضاءة', 'ru': 'Освещение'},
    'Lumens Delivered':     {'fr': 'Lumens Livrés', 'es': 'Lúmenes Entregados', 'de': 'Gelieferte Lumen', 'ar': 'اللومن المُسلَّم', 'ru': 'Выходной световой поток'},
    'CRI':                  {'fr': 'IRC', 'es': 'IRC', 'de': 'CRI', 'ar': 'مؤشر تجسيد الألوان', 'ru': 'CRI'},
    'Color Temperature':    {'fr': 'Température de Couleur', 'es': 'Temperatura de Color', 'de': 'Farbtemperatur', 'ar': 'درجة حرارة اللون', 'ru': 'Цветовая температура'},
    'Protection':           {'fr': 'Protection', 'es': 'Protección', 'de': 'Schutzart', 'ar': 'الحماية', 'ru': 'Защита'},
    'Controllable':         {'fr': 'Contrôlable', 'es': 'Controlable', 'de': 'Steuerbar', 'ar': 'قابل للتحكم', 'ru': 'Управление'},
    'Power':                {'fr': 'Puissance', 'es': 'Potencia', 'de': 'Leistung', 'ar': 'القدرة', 'ru': 'Мощность'},
    'Efficacy':             {'fr': 'Efficacité', 'es': 'Eficacia', 'de': 'Effizienz', 'ar': 'الكفاءة', 'ru': 'Эффективность'},
    'Beam Angle':           {'fr': 'Angle de Faisceau', 'es': 'Ángulo de Haz', 'de': 'Abstrahlwinkel', 'ar': 'زاوية الشعاع', 'ru': 'Угол луча'},
    'Output':               {'fr': 'Sortie', 'es': 'Salida', 'de': 'Ausgang', 'ar': 'الإخراج', 'ru': 'Выход'},
    # Sub-series subtitles
    '4-module configuration of the FL M-series floodlight family.':  {'fr': 'Configuration 4 modules de la famille de projecteurs FL Série M.', 'es': 'Configuración de 4 módulos de la familia de proyectores FL Serie M.', 'de': '4-Modul-Konfiguration der FL M-Serie Flutlichtfamilie.', 'ar': 'تكوين 4 وحدات من عائلة كشافات FL سلسلة M.', 'ru': 'Конфигурация из 4 модулей семейства прожекторов FL M-серии.'},
    '6-module configuration of the FL M-series floodlight family.':  {'fr': 'Configuration 6 modules de la famille de projecteurs FL Série M.', 'es': 'Configuración de 6 módulos de la familia de proyectores FL Serie M.', 'de': '6-Modul-Konfiguration der FL M-Serie Flutlichtfamilie.', 'ar': 'تكوين 6 وحدات من عائلة كشافات FL سلسلة M.', 'ru': 'Конфигурация из 6 модулей семейства прожекторов FL M-серии.'},
    '9-module configuration of the FL M-series floodlight family.':  {'fr': 'Configuration 9 modules de la famille de projecteurs FL Série M.', 'es': 'Configuración de 9 módulos de la familia de proyectores FL Serie M.', 'de': '9-Modul-Konfiguration der FL M-Serie Flutlichtfamilie.', 'ar': 'تكوين 9 وحدات من عائلة كشافات FL سلسلة M.', 'ru': 'Конфигурация из 9 модулей семейства прожекторов FL M-серии.'},
    '12-module configuration of the FL M-series floodlight family.': {'fr': 'Configuration 12 modules de la famille de projecteurs FL Série M.', 'es': 'Configuración de 12 módulos de la familia de proyectores FL Serie M.', 'de': '12-Modul-Konfiguration der FL M-Serie Flutlichtfamilie.', 'ar': 'تكوين 12 وحدة من عائلة كشافات FL سلسلة M.', 'ru': 'Конфигурация из 12 модулей семейства прожекторов FL M-серии.'},
    '16-module configuration of the FL M-series floodlight family.': {'fr': 'Configuration 16 modules de la famille de projecteurs FL Série M.', 'es': 'Configuración de 16 módulos de la familia de proyectores FL Serie M.', 'de': '16-Modul-Konfiguration der FL M-Serie Flutlichtfamilie.', 'ar': 'تكوين 16 وحدة من عائلة كشافات FL سلسلة M.', 'ru': 'Конфигурация из 16 модулей семейства прожекторов FL M-серии.'},
    # SiteConfig — hero & section text
    'The Next Generation Lighting Systems For Every Area': {'fr': 'Les Systèmes d\'Éclairage de Nouvelle Génération Pour Tous les Espaces', 'es': 'Los Sistemas de Iluminación de Próxima Generación Para Cada Área', 'de': 'Die Lichtsysteme der nächsten Generation für jeden Bereich', 'ar': 'أنظمة الإضاءة من الجيل الجديد لكل مساحة', 'ru': 'Осветительные системы нового поколения для любой площадки'},
    'Professional SolarOne sports lighting solutions trusted in over 50 countries. From community fields to broadcast-ready stadiums, engineered for performance, built to outlast.': {'fr': 'Solutions d\'éclairage sportif SolarOne professionnelles, reconnues dans plus de 50 pays. Des terrains communautaires aux stades prêts pour la télévision, conçues pour la performance et la durabilité.', 'es': 'Soluciones profesionales de iluminación deportiva SolarOne confiables en más de 50 países. Desde campos comunitarios hasta estadios listos para retransmisión, diseñadas para el rendimiento y la durabilidad.', 'de': 'Professionelle SolarOne-Sportbeleuchtungslösungen, die in über 50 Ländern vertraut werden. Von Gemeindepätzen bis zu sendebereiten Stadien — für Leistung und Langlebigkeit entwickelt.', 'ar': 'حلول إضاءة رياضية احترافية من SolarOne موثوقة في أكثر من 50 دولة. من الملاعب المجتمعية إلى الملاعب الجاهزة للبث، مصممة للأداء والمتانة.', 'ru': 'Профессиональные решения для спортивного освещения SolarOne, которым доверяют в более чем 50 странах. От местных площадок до стадионов, готовых к телетрансляции — созданы для производительности и долговечности.'},
    'Our Products': {'fr': 'Nos Produits', 'es': 'Nuestros Productos', 'de': 'Unsere Produkte', 'ar': 'منتجاتنا', 'ru': 'Наши продукты'},
    'From compact modular luminaires to stadium-grade high bay systems. Precision optics, modular architecture, and field-proven reliability across every product line.': {'fr': 'Des luminaires modulaires compacts aux systèmes high bay de qualité stade. Optiques de précision, architecture modulaire et fiabilité éprouvée sur chaque gamme.', 'es': 'Desde luminarias modulares compactas hasta sistemas high bay de grado estadio. Ópticas de precisión, arquitectura modular y fiabilidad probada en cada línea.', 'de': 'Von kompakten modularen Leuchten bis zu stadiontauglichen High-Bay-Systemen. Präzisionsoptik, modulare Architektur und bewährte Zuverlässigkeit in jeder Produktlinie.', 'ar': 'من الإضاءات المعيارية المدمجة إلى أنظمة الإضاءة العالية بمستوى الملاعب. بصريات دقيقة، بنية معيارية، وموثوقية مثبتة في كل خط منتج.', 'ru': 'От компактных модульных светильников до систем High-Bay стадионного класса. Прецизионная оптика, модульная архитектура и проверенная надёжность в каждой линейке.'},
    'Trusted Worldwide': {'fr': 'Reconnu Mondialement', 'es': 'Confianza Mundial', 'de': 'Weltweit Vertraut', 'ar': 'موثوق عالميًا', 'ru': 'Нам доверяют по всему миру'},
    'Real installations across five continents. From Olympic training centers to community football pitches, our luminaires deliver reliable performance under the toughest conditions.': {'fr': 'Installations réelles sur cinq continents. Des centres d\'entraînement olympiques aux terrains de football communautaires, nos luminaires offrent des performances fiables dans les conditions les plus difficiles.', 'es': 'Instalaciones reales en cinco continentes. Desde centros de entrenamiento olímpicos hasta campos de fútbol comunitarios, nuestros luminarios ofrecen un rendimiento fiable en las condiciones más difíciles.', 'de': 'Echte Installationen auf fünf Kontinenten. Vom Olympia-Trainingszentrum bis zum kommunalen Fußballplatz — unsere Leuchten liefern zuverlässige Leistung unter den härtesten Bedingungen.', 'ar': 'تركيبات حقيقية عبر خمس قارات. من مراكز التدريب الأولمبية إلى ملاعب كرة القدم المجتمعية، توفر إضاءاتنا أداءً موثوقًا في أصعب الظروف.', 'ru': 'Реальные установки на пяти континентах. От олимпийских тренировочных центров до местных футбольных полей — наши светильники обеспечивают надёжную работу в самых суровых условиях.'},
}


def _t(label, lang='en'):
    """Translate a sidebar label. Falls back to the English original."""
    if lang == 'en':
        return label
    entry = _SIDEBAR_I18N.get(label, {})
    return entry.get(lang, label)


# ============================================================================
# Sidebar data
# ============================================================================

def _get_projects_sidebar(lang='en'):
    return [
        {
            'key': 'OUTDOOR',
            'label': _t('Outdoor Sports', lang),
            'sports': [
                {'key': 'FOOTBALL_FIELD', 'label': _t('Football Field', lang)},
                {'key': 'SOCCER_FIELD', 'label': _t('Soccer Field', lang)},
                {'key': 'BASEBALL_FIELD', 'label': _t('Baseball Field', lang)},
                {'key': 'TENNIS_COURTS', 'label': _t('Tennis Courts', lang)},
                {'key': 'SKI_AREA', 'label': _t('Ski Area', lang)},
            ],
        },
        {
            'key': 'INDOOR',
            'label': _t('Indoor Sports', lang),
            'sports': [
                {'key': 'MULTI_SPORT', 'label': _t('Multi-Sport Arena', lang)},
                {'key': 'BASKETBALL', 'label': _t('Basketball', lang)},
                {'key': 'VOLLEYBALL', 'label': _t('Volleyball', lang)},
                {'key': 'TENNIS', 'label': _t('Tennis', lang)},
                {'key': 'ICE_ARENA', 'label': _t('Ice Arena', lang)},
            ],
        },
        {
            'key': 'INFRASTRUCTURE',
            'label': _t('Airports and Ports', lang),
            'sports': [
                {'key': 'AIRPORT', 'label': _t('Airport', lang)},
                {'key': 'SEAPORT', 'label': _t('Seaport', lang)},
            ],
        },
    ]


def _get_products_sidebar(lang='en'):
    """Sidebar structure for product pages. Series/variant data can be
    maintained in the admin; the hierarchy here is used for navigation."""
    return [
        {
            'key': 'AREA_SITE',
            'label': _t('Area and Site', lang),
            'series': [
                {
                    'key': 'M_SERIES',
                    'slug': 'm-series',
                    'label': _t('M Series', lang),
                    'subseries': [
                        {'key': 'FL1M',  'slug': 'fl1m',  'label': 'FL1M'},
                        {'key': 'FL4M',  'slug': 'fl4m',  'label': 'FL4M'},
                        {'key': 'FL6M',  'slug': 'fl6m',  'label': 'FL6M'},
                        {'key': 'FL9M',  'slug': 'fl9m',  'label': 'FL9M'},
                        {'key': 'FL12M', 'slug': 'fl12m', 'label': 'FL12M'},
                        {'key': 'FL16M', 'slug': 'fl16m', 'label': 'FL16M'},
                    ],
                },
                {'key': 'RT410_SERIES', 'slug': 'rt410-series', 'label': 'RT410FL-S'},
                {'key': 'ACCESSORY', 'slug': 'accessory', 'label': _t('Accessory', lang)},
            ],
        },
        {
            'key': 'SPORTS_LIGHTING_SYSTEM',
            'label': _t('Sports Lighting System', lang),
            'series': [
                {'key': 'VSP_9M_YP',  'slug': 'vsp-xxxxw-9m-yp',  'label': 'VSP-XXXXW-9M-YP'},
                {'key': 'VSP_12M_YP', 'slug': 'vsp-xxxxw-12m-yp', 'label': 'VSP-XXXXW-12M-YP'},
            ],
        },
        {
            'key': 'FLOODLIGHTING',
            'label': _t('Flood Lighting', lang),
            'series': [
                {'key': 'RT590FL_S', 'slug': 'rt590fl-s', 'label': 'RT590FL-S'},
                {'key': 'RT390FL',   'slug': 'rt390fl',   'label': 'RT390FL'},
                {'key': 'RT220UB',   'slug': 'rt220ub',   'label': 'RT220UB'},
                {'key': 'RT420FS_S', 'slug': 'rt420fs-s', 'label': 'RT420FS-S'},
                {'key': 'RT370FS_S', 'slug': 'rt370fs-s', 'label': 'RT370FS-S'},
                {'key': 'RT300FS_S', 'slug': 'rt300fs-s', 'label': 'RT300FS-S'},
                {'key': 'RT180FS_S', 'slug': 'rt180fs-s', 'label': 'RT180FS-S'},
            ],
        },
        {
            'key': 'HIGHBAY_LOWBAY',
            'label': _t('Highbay & Low Bay', lang),
            'series': [
                {'key': 'RT400HB', 'slug': 'rt400hb', 'label': 'RT400HB'},
                {'key': 'RT500HB', 'slug': 'rt500hb', 'label': 'RT500HB'},
            ],
        },
        {
            'key': 'ROADWAY',
            'label': _t('Roadway', lang),
            'series': [
                {'key': 'RT600SL_T', 'slug': 'rt600sl-t', 'label': 'RT600SL-T'},
                {'key': 'RT820SL_T', 'slug': 'rt820sl-t', 'label': 'RT820SL-T'},
            ],
        },
    ]


def _resolve_product_sidebar(slug, lang='en'):
    """Resolve active_series, active_subseries and parent_slug for a product slug."""
    active_series = ''
    active_subseries = ''
    parent_slug = ''
    for cat in _get_products_sidebar(lang):
        for s in cat['series']:
            if s['slug'] == slug:
                active_series = s['key']
                parent_slug = ''
                break
            if 'subseries' in s:
                for sub in s['subseries']:
                    if sub['slug'] == slug:
                        active_series = s['key']
                        active_subseries = sub['key']
                        parent_slug = s['slug']
                        break
                if active_subseries:
                    break
        if active_series or active_subseries:
            break
    return active_series, active_subseries, parent_slug


def _resolve_project_sidebar(sport_type, lang='en'):
    """Resolve active_venue_type and active_sport_type for a project."""
    active_venue_type = ''
    active_sport_type = ''
    for vt in _get_projects_sidebar(lang):
        for st in vt['sports']:
            if st['key'] == sport_type:
                active_venue_type = vt['key']
                active_sport_type = st['key']
                break
        if active_sport_type:
            break
    return active_venue_type, active_sport_type


# ============================================================================
# Common context
# ============================================================================

def get_common_context():
    """Get context shared across all pages"""
    config = cache.get('site_config')
    if not config:
        try:
            config = SiteConfig.objects.first()
            if not config:
                config = SiteConfig.objects.create()
            cache.set('site_config', config, timeout=300)
        except Exception:
            logger.warning('DB SiteConfig query failed, building from seed JSON', exc_info=True)
            data = _load_seed()
            cfg = data.get('siteconfig', {})
            config = SiteConfig()
            _image_fields = {'hero_background', 'logo', 'og_image'}
            for key, val in cfg.items():
                if key in _image_fields:
                    continue
                if hasattr(config, key):
                    try:
                        setattr(config, key, val)
                    except Exception:
                        pass
            cache.set('site_config', config, timeout=300)

    hero_bg = getattr(config, 'hero_background', '')
    hero_name = getattr(hero_bg, 'name', hero_bg) if hero_bg else ''
    if hero_name:
        config.hero_bg_url = static(hero_name)
    else:
        config.hero_bg_url = static('images/hero-main.webp')

    logo = getattr(config, 'logo', '')
    logo_name = getattr(logo, 'name', logo) if logo else ''
    if logo_name:
        config.logo_url = static(logo_name)
    else:
        config.logo_url = static('images/logo.webp')

    lang = get_language()
    config.hero_title = _t(config.hero_title, lang)
    config.hero_subtitle = _t(config.hero_subtitle, lang)
    config.products_title = _t(config.products_title, lang)
    config.products_subtitle = _t(config.products_subtitle, lang)
    config.projects_title = _t(config.projects_title, lang)
    config.projects_subtitle = _t(config.projects_subtitle, lang)

    return {'config': config}


# ============================================================================
# Page views
# ============================================================================

def home(request):
    return render(request, 'home.html', get_common_context())


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or '0.0.0.0'


def _is_rate_limited(request):
    window = getattr(settings, 'CONTACT_RATE_WINDOW', 600)
    limit = getattr(settings, 'CONTACT_RATE_LIMIT', 3)
    ip = _get_client_ip(request)
    session_key = request.session.session_key or 'anon'
    key = f'contact_rate:{ip}:{session_key}'
    try:
        count = cache.get(key) or 0
        if count >= limit:
            return True
        cache.set(key, count + 1, timeout=window)
    except Exception:
        logger.warning('Rate limit cache unavailable, failing open', exc_info=True)
        return False
    return False


def _send_contact_notification(contact_msg):
    notify_to = getattr(settings, 'CONTACT_NOTIFY_EMAIL', '')
    if not notify_to:
        return False
    subject = f'[Contact] New message from {contact_msg.name}'
    body_lines = [
        f'Name:    {contact_msg.name}',
        f'Email:   {contact_msg.email}',
        f'Phone:   {contact_msg.phone or "(not provided)"}',
        '',
        'Message:',
        contact_msg.message,
        '',
        f'Submitted at: {contact_msg.created_at:%Y-%m-%d %H:%M:%S}',
        f'Reply URL:    mailto:{contact_msg.email}',
    ]
    try:
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message='\n'.join(body_lines),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@solarone.com'),
            recipient_list=[notify_to],
            fail_silently=True,
        )
        return True
    except Exception:
        logger.warning('Failed to send contact notification email', exc_info=True)
        return False


def contact(request):
    context = get_common_context()

    prefill_product = request.GET.get('product', '').strip()
    prefill_product_name = request.GET.get('product_name', '').strip()
    prefill_ref = request.GET.get('ref', '').strip()

    if prefill_product:
        context['prefill_product'] = prefill_product
        context['prefill_product_name'] = prefill_product_name
        context['prefill_ref'] = prefill_ref

    if request.method == 'POST':
        if _is_rate_limited(request):
            messages.error(
                request,
                _('Too many messages submitted recently. Please wait a few minutes before trying again.')
            )
            return render(request, 'contact.html', context)

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        if name and email and message:
            try:
                contact_msg = ContactMessage.objects.create(
                    name=name, email=email, phone=phone, message=message
                )
                _send_contact_notification(contact_msg)
                messages.success(request, _('Your message has been sent successfully!'))
            except Exception:
                logger.warning('Failed to save contact message', exc_info=True)
                messages.error(request, _('Sorry, we could not save your message. Please try again.'))
    return render(request, 'contact.html', context)


def products(request):
    context = get_common_context()
    lang = get_language()

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    active_category = request.GET.get('category', '')
    active_series = request.GET.get('series', '')
    context['active_category'] = active_category
    context['active_series'] = active_series

    active_category_label = ''
    active_series_label = ''
    for cat in product_categories:
        if cat['key'] == active_category:
            active_category_label = cat['label']
            for s in cat['series']:
                if s['key'] == active_series:
                    active_series_label = s['label']
                    break
            break
    context['active_category_label'] = active_category_label
    context['active_series_label'] = active_series_label

    products_list = _get_products_from_db(lang, active_category, active_series)
    if not products_list:
        products_list = _get_products_from_json(lang, active_category, active_series)

    context['products'] = products_list
    return render(request, 'products.html', context)


def product_detail(request, slug):
    """Unified product detail page for both series and sub-series.

    Content (text, images, banner, gallery) is read from the Product model so
    it can be edited in the admin. Seed JSON is kept as a fallback for Vercel.
    """
    context = get_common_context()
    lang = get_language()

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    product = _get_product_detail_from_db(slug, lang)
    if product is None:
        product = _get_product_detail_from_json(slug, lang)

    active_series, active_subseries, parent_slug = _resolve_product_sidebar(slug, lang)
    context['active_series'] = active_series
    context['active_subseries'] = active_subseries

    if product:
        context['product'] = product
        context['banner_image'] = product.banner_image_url
        context['banner_label'] = product.category_t
        context['gallery'] = product.gallery
        context['is_variant'] = bool(product.parent_slug)
        context['parent_slug'] = parent_slug or product.parent_slug
        # Certification badges for M Series / RT410 Series and their variants
        context['show_certs'] = (
            product.slug in ('m-series', 'rt410-series') or
            product.parent_slug == 'm-series'
        )

    return render(request, 'product_detail.html', context)


def product_series(request, slug):
    """Legacy sub-series URL: now uses the same unified detail template."""
    return product_detail(request, slug)


def news(request):
    context = get_common_context()
    articles = []
    try:
        articles = list(NewsArticle.objects.filter(is_published=True).order_by('-published_at'))
    except Exception:
        logger.warning('DB news query failed', exc_info=True)
    context['articles'] = articles
    return render(request, 'news.html', context)


def projects(request):
    context = get_common_context()
    lang = get_language()

    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    active_venue_type = request.GET.get('venue', '')
    active_sport_type = request.GET.get('sport', '')
    context['active_venue_type'] = active_venue_type
    context['active_sport_type'] = active_sport_type

    active_venue_type_label = ''
    active_sport_type_label = ''
    for vt in venue_types:
        if vt['key'] == active_venue_type:
            active_venue_type_label = vt['label']
            for s in vt['sports']:
                if s['key'] == active_sport_type:
                    active_sport_type_label = s['label']
                    break
            break
    context['active_venue_type_label'] = active_venue_type_label
    context['active_sport_type_label'] = active_sport_type_label

    projects_list = _get_projects_from_db(lang, active_venue_type, active_sport_type)
    if not projects_list:
        projects_list = _get_projects_from_json(lang, active_venue_type, active_sport_type)

    # Pagination: 10 projects per page
    paginator = Paginator(projects_list or [], 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['projects'] = page_obj.object_list
    context['page_obj'] = page_obj
    return render(request, 'projects.html', context)


def project_detail(request, slug):
    """Project detail page with backend-managed text and image carousel."""
    context = get_common_context()
    lang = get_language()

    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    project = _get_project_detail_from_db(slug, lang)
    if project is None:
        project = _get_project_detail_from_json(slug, lang)

    if project:
        context['project'] = project
        context['gallery'] = project.gallery
        active_venue_type, active_sport_type = _resolve_project_sidebar(getattr(project, 'sport_type', ''), lang)
        context['active_venue_type'] = active_venue_type
        context['active_sport_type'] = active_sport_type

        active_venue_type_label = ''
        active_sport_type_label = ''
        for vt in venue_types:
            if vt['key'] == active_venue_type:
                active_venue_type_label = vt['label']
                for s in vt['sports']:
                    if s['key'] == active_sport_type:
                        active_sport_type_label = s['label']
                        break
                break
        context['active_venue_type_label'] = active_venue_type_label
        context['active_sport_type_label'] = active_sport_type_label
    else:
        context['active_venue_type'] = ''
        context['active_sport_type'] = ''

    return render(request, 'project_detail.html', context)


def robots_txt(request):
    """Render robots.txt."""
    return render(request, 'robots.txt', content_type='text/plain')


def sitemap_xml(request):
    """Generate sitemap.xml listing all public URLs."""
    from django.urls import reverse
    from pages.seed_data import SEED_DATA

    data = _load_seed()
    products = data.get('products', [])
    projects = data.get('projects', [])

    scheme = 'https'
    host = request.get_host()

    urls = []

    # Static pages
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

    # Product detail pages
    for p in products:
        slug = p.get('slug', '')
        if slug:
            path = reverse('product_detail', args=[slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.7</priority></url>')

    # Product series pages (deduplicated)
    seen_series = set()
    for p in products:
        parent_slug = p.get('parent_slug', '')
        if parent_slug and parent_slug not in seen_series:
            seen_series.add(parent_slug)
            series_slug = f'{parent_slug}-series'
            path = reverse('product_series', args=[series_slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.6</priority></url>')

    # Project detail pages
    for p in projects:
        slug = p.get('slug', '')
        if slug:
            path = reverse('project_detail', args=[slug])
            urls.append(f'  <url><loc>{scheme}://{host}{path}</loc><priority>0.8</priority></url>')

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls)
    xml += '\n</urlset>'

    return HttpResponse(xml, content_type='application/xml')