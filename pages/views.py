import os
import json
import logging
from django.shortcuts import render
from django.contrib import messages
from django.core.cache import cache
from django.templatetags.static import static
from django.utils.translation import get_language, gettext as _
from django.conf import settings
from pages.models import Product, Project, SiteConfig, ContactMessage

logger = logging.getLogger(__name__)

# Path to seed data — used as fallback when DB is unavailable (e.g. Vercel ephemeral SQLite)
# Try multiple candidate locations: BASE_DIR (local + most Vercel setups) and directories
# relative to this file (in case @vercel/python places the lambda in a subfolder).
_SEED_CANDIDATES = [
    os.path.join(settings.BASE_DIR, 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data.json'),
]


def _load_seed():
    """Load seed data. On Vercel, import from the embedded Python module
    (pages.seed_data) so no filesystem access is needed. In local dev, fall
    back to reading seed_data.json from disk so the JSON stays the source of
    truth during development."""
    data = cache.get('seed_data_json')
    if data is None:
        # Preferred: embedded Python module (works on Vercel)
        try:
            from pages.seed_data import SEED_DATA
            data = SEED_DATA
        except Exception:
            logger.warning('Could not import pages.seed_data, trying JSON file', exc_info=True)
            data = None

        # Fallback: read JSON file from disk (local dev)
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


class _DictProduct:
    """Lightweight wrapper that mimics the Product model interface for templates."""
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
        self.order = item.get('order', 0)
        self.translations = item.get('translations', {}) or {}

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


class _DictProject:
    """Lightweight wrapper that mimics the Project model interface for templates."""
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

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


def _get_products_from_db(lang, active_category='', active_series='', active_series_label=''):
    """Try loading products from DB. Returns None on failure (caller falls back to JSON)."""
    try:
        products_list = Product.objects.all()
        if active_category:
            products_list = products_list.filter(category=active_category)
        if active_series and active_series_label:
            products_list = products_list.filter(name__icontains=active_series_label.replace(' Series', ''))
        result = []
        for p in products_list:
            if p.image:
                p.image_url = static(p.image.name)
            else:
                p.image_url = ''
            p.name_t = p.t('name', lang)
            p.description_t = p.t('description', lang)
            p.category_t = p.t('category', lang)
            result.append(p)
        return result
    except Exception:
        logger.warning('DB products query failed, will fall back to seed JSON', exc_info=True)
        return None


def _get_products_from_json(lang, active_category='', active_series='', active_series_label=''):
    """Load products from seed_data.json (fallback for Vercel)."""
    data = _load_seed()
    items = data.get('products', [])
    result = []
    for item in items:
        if active_category and item.get('category') != active_category:
            continue
        if active_series and active_series_label:
            series_name = active_series_label.replace(' Series', '')
            if series_name.lower() not in item.get('name', '').lower():
                continue
        p = _DictProduct(item)
        p.image_url = static(p.image) if p.image else ''
        p.name_t = p.t('name', lang)
        p.description_t = p.t('description', lang)
        p.category_t = p.t('category', lang)
        result.append(p)
    return result


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
            if proj.image:
                proj.image_url = static(proj.image.name)
            else:
                proj.image_url = ''
            proj.title_t = proj.t('title', lang)
            proj.description_t = proj.t('description', lang)
            proj.location_t = proj.t('location', lang)
            proj.results_t = proj.t('results', lang)
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
        proj.image_url = static(proj.image) if proj.image else ''
        proj.title_t = proj.t('title', lang)
        proj.description_t = proj.t('description', lang)
        proj.location_t = proj.t('location', lang)
        proj.results_t = proj.t('results', lang)
        result.append(proj)
    return result


def _get_product_detail_from_db(slug, lang):
    """Try loading a single product from DB. Returns None on failure."""
    try:
        product = Product.objects.get(slug=slug)
        if product.image:
            product.image_url = static(product.image.name)
        else:
            product.image_url = ''
        product.name_t = product.t('name', lang)
        product.description_t = product.t('description', lang)
        product.category_t = product.t('category', lang)
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
            p.image_url = static(p.image) if p.image else ''
            p.name_t = p.t('name', lang)
            p.description_t = p.t('description', lang)
            p.category_t = p.t('category', lang)
            return p
    return None


# Translation map for sidebar labels
_SIDEBAR_I18N = {
    # Projects — venue types
    'Outdoor Sports':  {'fr': 'Sports Extérieur', 'es': 'Deportes Exterior', 'de': 'Outdoor-Sport', 'ar': 'رياضات خارجية', 'ru': 'Спорт на открытом воздухе'},
    'Indoor Sports':   {'fr': 'Sports Intérieur', 'es': 'Deportes Interior', 'de': 'Indoor-Sport', 'ar': 'رياضات داخلية', 'ru': 'Спорт в закрытом помещении'},
    'Airports and Ports': {'fr': 'Aéroports et Ports', 'es': 'Aeropuertos y Puertos', 'de': 'Flughäfen und Häfen', 'ar': 'المطارات والموانئ', 'ru': 'Аэропорты и порты'},
    # Projects — sport types
    'Football Field':   {'fr': 'Terrain de Football', 'es': 'Campo de Fútbol', 'de': 'Fußballplatz', 'ar': 'ملعب كرة قدم', 'ru': 'Футбольное поле'},
    'Soccer Field':     {'fr': 'Terrain de Soccer', 'es': 'Campo de Fútbol', 'de': 'Fußballplatz', 'ar': 'ملعب كرة القدم', 'ru': 'Футбольное поле'},
    'Baseball Field':   {'fr': 'Terrain de Baseball', 'es': 'Campo de Béisbol', 'de': 'Baseballfeld', 'ar': 'ملعب بيسبول', 'ru': 'Бейсбольное поле'},
    'Tennis Courts':    {'fr': 'Courts de Tennis', 'es': 'Canchas de Tenis', 'de': 'Tennisplätze', 'ar': 'ملعب تنس', 'ru': 'Теннисные корты'},
    'Track and Field':  {'fr': 'Piste d\'Athlétisme', 'es': 'Pista de Atletismo', 'de': 'Leichtathletikanlage', 'ar': 'مضمار وميدان', 'ru': 'Легкоатлетическая площадка'},
    'Stadium':          {'fr': 'Stade', 'es': 'Estadio', 'de': 'Stadion', 'ar': 'استاد', 'ru': 'Стадион'},
    'Basketball':       {'fr': 'Basketball', 'es': 'Baloncesto', 'de': 'Basketball', 'ar': 'كرة السلة', 'ru': 'Баскетбол'},
    'Volleyball':       {'fr': 'Volleyball', 'es': 'Voleibol', 'de': 'Volleyball', 'ar': 'كرة الطائرة', 'ru': 'Волейбол'},
    'Tennis':           {'fr': 'Tennis', 'es': 'Tenis', 'de': 'Tennis', 'ar': 'تنس', 'ru': 'Теннис'},
    'Multi-Sport Arena':{'fr': 'Complexe Multi-Sports', 'es': 'Pista Polideportiva', 'de': 'Mehrzweckhalle', 'ar': 'صالة متعددة الرياضات', 'ru': 'Универсальный спортивный зал'},
    'Airport':          {'fr': 'Aéroport', 'es': 'Aeropuerto', 'de': 'Flughafen', 'ar': 'مطار', 'ru': 'Аэропорт'},
    'Seaport':          {'fr': 'Port Maritime', 'es': 'Puerto', 'de': 'Seehafen', 'ar': 'ميناء بحري', 'ru': 'Морской порт'},
    # Products — categories (new structure)
    'Area and Site':            {'fr': 'Zone et Site', 'es': 'Área y Sitio', 'de': 'Bereich und Standort', 'ar': 'المنطقة والموقع', 'ru': 'Территория и площадка'},
    'Sports Lighting System': {'fr': 'Système d\'Éclairage Sportif', 'es': 'Sistema de Iluminación Deportiva', 'de': 'Sportbeleuchtungssystem', 'ar': 'نظام إضاءة رياضية', 'ru': 'Система спортивного освещения'},
    'Floodlighting':            {'fr': 'Projecteurs', 'es': 'Proyectores', 'de': 'Flutlicht', 'ar': 'إضاءة فيضانية', 'ru': 'Прожекторное освещение'},
    'Highbay & Low Bay':        {'fr': 'Haute & Basse Baie', 'es': 'Alta & Baja Bahía', 'de': 'Highbay & Lowbay', 'ar': 'إضاءة عالية ومنخفضة', 'ru': 'Высокий и низкий пролёт'},
    'Roadway':                  {'fr': 'Éclairage Routier', 'es': 'Alumbrado Vial', 'de': 'Straßenbeleuchtung', 'ar': 'إنارة الطرق', 'ru': 'Дорожное освещение'},
    'Accessory':                {'fr': 'Accessoire', 'es': 'Accesorio', 'de': 'Zubehör', 'ar': 'ملحق', 'ru': 'Аксессуар'},
    # Products — categories (legacy, kept for backward compatibility)
    'Flood Lighting':   {'fr': 'Éclairage de Stade', 'es': 'Iluminación Deportiva', 'de': 'Flutlicht', 'ar': 'إضاءة الملاعب', 'ru': 'Спортивное освещение'},
    'High Bay':         {'fr': 'Éclairage Haut', 'es': 'Iluminación Alta', 'de': 'Hallenleuchte', 'ar': 'إضاءة مرتفعة', 'ru': 'Промышленный свет'},
    'Street Lighting':  {'fr': 'Éclairage Routier', 'es': 'Alumbrado Público', 'de': 'Straßenbeleuchtung', 'ar': 'إنارة الشوارع', 'ru': 'Уличное освещение'},
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


# Sidebar data for Projects page
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
                {'key': 'TRACK_FIELD', 'label': _t('Track and Field', lang)},
            ],
        },
        {
            'key': 'INDOOR',
            'label': _t('Indoor Sports', lang),
            'sports': [
                {'key': 'BASKETBALL', 'label': _t('Basketball', lang)},
                {'key': 'VOLLEYBALL', 'label': _t('Volleyball', lang)},
                {'key': 'TENNIS', 'label': _t('Tennis', lang)},
                {'key': 'MULTI_SPORT', 'label': _t('Multi-Sport Arena', lang)},
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


# Sidebar data for Products page
def _get_products_sidebar(lang='en'):
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
            'label': _t('Floodlighting', lang),
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
            # DB unavailable — build a minimal config from seed JSON so pages render.
            # ImageField values are skipped (they are bare strings in the JSON and
            # would break .name access); hero_background/logo fall back to defaults.
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

    # Pre-compute static URLs for hero bg and logo.
    # Guard .name access in case config came from JSON fallback (bare value).
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
        config.logo_url = static('images/logo.png')

    # Apply i18n to text fields via _t() lookup
    lang = get_language()
    config.hero_title = _t(config.hero_title, lang)
    config.hero_subtitle = _t(config.hero_subtitle, lang)
    config.products_title = _t(config.products_title, lang)
    config.products_subtitle = _t(config.products_subtitle, lang)
    config.projects_title = _t(config.projects_title, lang)
    config.projects_subtitle = _t(config.projects_subtitle, lang)

    return {'config': config}


def home(request):
    return render(request, 'home.html', get_common_context())


def _get_client_ip(request):
    """Get the real client IP, accounting for proxies (Vercel, Cloudflare, etc.)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # Left-most entry is the original client
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or '0.0.0.0'


def _is_rate_limited(request):
    """Simple cache-based rate limiter for the contact form.

    Limits per IP+session to CONTACT_RATE_LIMIT submissions per
    CONTACT_RATE_WINDOW seconds. Returns True if the request should be
    blocked. Uses the cache backend (works on Vercel via cookie sessions
    fallback, local dev via LocMem cache)."""
    window = getattr(settings, 'CONTACT_RATE_WINDOW', 600)  # 10 min default
    limit = getattr(settings, 'CONTACT_RATE_LIMIT', 3)      # 3 per window

    ip = _get_client_ip(request)
    session_key = request.session.session_key or 'anon'
    key = f'contact_rate:{ip}:{session_key}'

    try:
        count = cache.get(key) or 0
        if count >= limit:
            return True
        cache.set(key, count + 1, timeout=window)
    except Exception:
        # If cache is unavailable, allow the request through (fail-open)
        # to avoid blocking legitimate submissions.
        logger.warning('Rate limit cache unavailable, failing open', exc_info=True)
        return False
    return False


def _send_contact_notification(contact_msg):
    """Send an email notification to site admins about a new contact message.

    Silently no-ops if EMAIL_BACKEND is not configured (no SMTP credentials).
    This keeps the contact flow working on Vercel without email setup while
    enabling email alerts once SMTP env vars are provided."""
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

    if request.method == 'POST':
        # 1.4 — rate limit check before any DB writes
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
        if name and email and message:
            try:
                contact_msg = ContactMessage.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    message=message
                )
                # 7.3 — fire-and-forget email notification to admin
                _send_contact_notification(contact_msg)
                messages.success(request, _('Your message has been sent successfully!'))
            except Exception:
                logger.warning('Failed to save contact message', exc_info=True)
                messages.error(request, _('Sorry, we could not save your message. Please try again.'))

    return render(request, 'contact.html', context)


def products(request):
    context = get_common_context()
    lang = get_language()

    # Sidebar data
    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    # Filtering via URL params
    active_category = request.GET.get('category', '')
    active_series = request.GET.get('series', '')
    context['active_category'] = active_category
    context['active_series'] = active_series

    # Resolve labels for active filters
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

    # Try DB first; fall back to seed JSON if DB unavailable (Vercel cold start)
    products_list = _get_products_from_db(lang, active_category, active_series, active_series_label)
    if products_list is None:
        products_list = _get_products_from_json(lang, active_category, active_series, active_series_label)

    context['products'] = products_list
    return render(request, 'products.html', context)


def projects(request):
    context = get_common_context()
    lang = get_language()

    # Sidebar data
    venue_types = _get_projects_sidebar(lang)
    context['venue_types'] = venue_types

    # Filtering via URL params
    active_venue_type = request.GET.get('venue', '')
    active_sport_type = request.GET.get('sport', '')
    context['active_venue_type'] = active_venue_type
    context['active_sport_type'] = active_sport_type

    # Resolve labels for active filters
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

    # Try DB first; fall back to seed JSON
    projects_list = _get_projects_from_db(lang, active_venue_type, active_sport_type)
    if projects_list is None:
        projects_list = _get_projects_from_json(lang, active_venue_type, active_sport_type)

    context['projects'] = projects_list
    return render(request, 'projects.html', context)


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)


def product_detail(request, slug):
    context = get_common_context()
    lang = get_language()

    # Sidebar data
    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    # Try DB first; fall back to seed JSON
    product = _get_product_detail_from_db(slug, lang)
    if product is None:
        product = _get_product_detail_from_json(slug, lang)

    # Resolve active series key from slug
    active_series = ''
    for cat in product_categories:
        for s in cat['series']:
            if s['slug'] == slug:
                active_series = s['key']
                break
        if active_series:
            break
    context['active_series'] = active_series

    if product:
        context['product'] = product

    # M Series main page uses a carousel gallery like sub-series pages
    if slug == 'm-series':
        context['gallery'] = [
            {'src': static('images/products/m-series/m-series-01.webp'), 'alt': 'M Series — view 1'},
            {'src': static('images/products/m-series/m-series-02.webp'), 'alt': 'M Series — view 2'},
            {'src': static('images/products/m-series/m-series-03.webp'), 'alt': 'M Series — view 3'},
            {'src': static('images/products/m-series/m-series-04.webp'), 'alt': 'M Series — view 4'},
        ]

    return render(request, 'product_detail.html', context)


# ============ Sub-series pages (FL1M, FL4M, ...) ============
# Static catalog of sub-series detail pages under M Series (Area and Site).
# Only FL1M–FL16M are linked from the sidebar; VSP/RGB entries are kept
# for backward-compatible URLs.

_SUBSERIES_CATALOG = {
    'fl1m': {
        'title': 'FL1M Series',
        'subtitle': '',
        'images': [
            {'src': 'images/products/fl1m/fl1m-01.png', 'alt': 'FL1M Series — view 1'},
            {'src': 'images/products/fl1m/fl1m-02.png', 'alt': 'FL1M Series — view 2'},
            {'src': 'images/products/fl1m/fl1m-03.png', 'alt': 'FL1M Series — view 3'},
            {'src': 'images/products/fl1m/fl1m-04.png', 'alt': 'FL1M Series — view 4'},
        ],
        'specs': [
            {'value': '80W',               'label': 'Illumination'},
            {'value': '10,000+',           'label': 'Lumens Delivered'},
            {'value': '75 ~ 90+',          'label': 'CRI'},
            {'value': '3000K ~ 5700K',     'label': 'Color Temperature'},
            {'value': 'IP66',              'label': 'Protection'},
            {'value': '0-10V, DALI, DMX',   'label': 'Controllable'},
        ],
    },
    'fl4m': {
        'title': 'FL4M Series',
        'subtitle': '4-module configuration of the FL M-series floodlight family.',
        'images': [
            {'src': 'images/products/fl4m/fl4m-01.png', 'alt': 'FL4M Series — view 1'},
            {'src': 'images/products/fl4m/fl4m-02.png', 'alt': 'FL4M Series — view 2'},
            {'src': 'images/products/fl4m/fl4m-03.png', 'alt': 'FL4M Series — view 3'},
            {'src': 'images/products/fl4m/fl4m-04.png', 'alt': 'FL4M Series — view 4'},
        ],
        'specs': [
            {'value': '320W',              'label': 'Illumination'},
            {'value': '40,000+',           'label': 'Lumens Delivered'},
            {'value': '75 ~ 90+',          'label': 'CRI'},
            {'value': '3000K ~ 5700K',     'label': 'Color Temperature'},
            {'value': 'IP66',              'label': 'Protection'},
            {'value': '0-10V, DALI, DMX',   'label': 'Controllable'},
        ],
        'banner_image': 'images/products/fl4m/fl4m-3d-view.png',
    },
    'fl6m': {
        'title': 'FL6M Series',
        'subtitle': '6-module configuration of the FL M-series floodlight family.',
        'images': [
            {'src': 'images/products/fl6m/fl6m-01.png', 'alt': 'FL6M Series — view 1'},
            {'src': 'images/products/fl6m/fl6m-02.png', 'alt': 'FL6M Series — view 2'},
            {'src': 'images/products/fl6m/fl6m-03.png', 'alt': 'FL6M Series — view 3'},
            {'src': 'images/products/fl6m/fl6m-04.png', 'alt': 'FL6M Series — view 4'},
        ],
        'specs': [
            {'value': '480W',        'label': 'Power'},
            {'value': '130 lm/W',    'label': 'Efficacy'},
            {'value': 'IP66',        'label': 'Protection'},
            {'value': '15°-60°',     'label': 'Beam Angle'},
        ],
    },
    'fl9m': {
        'title': 'FL9M Series',
        'subtitle': '9-module configuration of the FL M-series floodlight family.',
        'images': [
            {'src': 'images/products/fl9m/fl9m-01.png', 'alt': 'FL9M Series — view 1'},
            {'src': 'images/products/fl9m/fl9m-02.png', 'alt': 'FL9M Series — view 2'},
            {'src': 'images/products/fl9m/fl9m-03.png', 'alt': 'FL9M Series — view 3'},
            {'src': 'images/products/fl9m/fl9m-04.png', 'alt': 'FL9M Series — view 4'},
        ],
        'specs': [
            {'value': '720W',        'label': 'Power'},
            {'value': '130 lm/W',    'label': 'Efficacy'},
            {'value': 'IP66',        'label': 'Protection'},
            {'value': '15°-60°',     'label': 'Beam Angle'},
        ],
    },
    'fl12m': {
        'title': 'FL12M Series',
        'subtitle': '12-module configuration of the FL M-series floodlight family.',
        'images': [
            {'src': 'images/products/fl12m/fl12m-01.png', 'alt': 'FL12M Series — view 1'},
            {'src': 'images/products/fl12m/fl12m-02.png', 'alt': 'FL12M Series — view 2'},
            {'src': 'images/products/fl12m/fl12m-03.png', 'alt': 'FL12M Series — view 3'},
            {'src': 'images/products/fl12m/fl12m-04.png', 'alt': 'FL12M Series — view 4'},
        ],
        'specs': [
            {'value': '960W',        'label': 'Power'},
            {'value': '130 lm/W',    'label': 'Efficacy'},
            {'value': 'IP66',        'label': 'Protection'},
            {'value': '15°-60°',     'label': 'Beam Angle'},
        ],
    },
    'fl16m': {
        'title': 'FL16M Series',
        'subtitle': '16-module configuration of the FL M-series floodlight family.',
        'images': [
            {'src': 'images/products/fl16m/fl16m-01.png', 'alt': 'FL16M Series — view 1'},
            {'src': 'images/products/fl16m/fl16m-02.png', 'alt': 'FL16M Series — view 2'},
            {'src': 'images/products/fl16m/fl16m-03.png', 'alt': 'FL16M Series — view 3'},
            {'src': 'images/products/fl16m/fl16m-04.png', 'alt': 'FL16M Series — view 4'},
        ],
        'specs': [
            {'value': '1280W',       'label': 'Power'},
            {'value': '130 lm/W',    'label': 'Efficacy'},
            {'value': 'IP66',        'label': 'Protection'},
            {'value': '15°-60°',     'label': 'Beam Angle'},
        ],
    },
    'vsp-system':      {'title': 'VSP System',       'subtitle': 'Vision Strobe Protection system for broadcast venues.'},
    'rgb-rgbw-series': {'title': 'RGB/RGBW Series',  'subtitle': 'Color-tunable RGB/RGBW floodlight for events and façade lighting.'},
}


def product_series(request, slug):
    """Sub-series detail page (e.g. /products/series/fl1m/).

    Renders a two-column layout with an image carousel on the left and
    product info/specs on the right, mirroring the product_detail layout
    but with multiple images (carousel) instead of a single image.
    """
    context = get_common_context()
    lang = get_language()

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    series_data = _SUBSERIES_CATALOG.get(slug)
    if series_data is None:
        context['series_title'] = _('Product Series Not Found')
        context['series_subtitle'] = ''
        context['gallery'] = []
        context['specs'] = []
    else:
        context['series_title'] = series_data.get('title', '')
        context['series_subtitle'] = _t(series_data.get('subtitle', ''), lang)
        # Resolve static URLs for gallery images
        gallery = []
        for img in series_data.get('images', []):
            gallery.append({
                'src': static(img['src']),
                'alt': img.get('alt', ''),
            })
        context['gallery'] = gallery
        # Translate spec labels (values are technical, kept as-is)
        specs = []
        for spec in series_data.get('specs', []):
            specs.append({
                'value': spec['value'],
                'label': _t(spec['label'], lang),
            })
        context['specs'] = specs
        banner_img = series_data.get('banner_image', '')
        context['banner_image'] = static(banner_img) if banner_img else ''

    # Resolve active series + subseries keys for sidebar highlighting
    context['active_series'] = ''
    context['active_subseries'] = slug
    for cat in product_categories:
        for s in cat['series']:
            if 'subseries' in s:
                for sub in s['subseries']:
                    if sub['slug'] == slug:
                        context['active_series'] = s['key']
                        context['active_subseries'] = sub['key']
                        context['parent_series_slug'] = s['slug']
                        break
                if context['active_series']:
                    break
        if context['active_series']:
            break

    return render(request, 'product_series.html', context)
