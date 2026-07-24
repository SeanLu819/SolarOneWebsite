from django.shortcuts import render
from django.contrib import messages
from django.core.cache import cache
from django.templatetags.static import static
from django.utils.translation import get_language, gettext as _
from pages.models import Product, Project, SiteConfig, ContactMessage


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
    # Products — categories
    'Flood Lighting':   {'fr': 'Éclairage de Stade', 'es': 'Iluminación Deportiva', 'de': 'Flutlicht', 'ar': 'إضاءة الملاعب', 'ru': 'Спортивное освещение'},
    'High Bay':         {'fr': 'Éclairage Haut', 'es': 'Iluminación Alta', 'de': 'Hallenleuchte', 'ar': 'إضاءة مرتفعة', 'ru': 'Промышленный свет'},
    'Street Lighting':  {'fr': 'Éclairage Routier', 'es': 'Alumbrado Público', 'de': 'Straßenbeleuchtung', 'ar': 'إنارة الشوارع', 'ru': 'Уличное освещение'},
    # Products — series (generally kept as-is, but add per-language if needed)
    'M Series':         {'fr': 'Série M', 'es': 'Serie M', 'de': 'M-Serie', 'ar': 'سلسلة M', 'ru': 'Серия M'},
    'RT410 Series':     {'fr': 'Série RT410', 'es': 'Serie RT410', 'de': 'RT410-Serie', 'ar': 'سلسلة RT410', 'ru': 'Серия RT410'},
    'RT400 Series':     {'fr': 'Série RT400', 'es': 'Serie RT400', 'de': 'RT400-Serie', 'ar': 'سلسلة RT400', 'ru': 'Серия RT400'},
    'RT500 Series':     {'fr': 'Série RT500', 'es': 'Serie RT500', 'de': 'RT500-Serie', 'ar': 'سلسلة RT500', 'ru': 'Серия RT500'},
    'RT750 Series':     {'fr': 'Série RT750', 'es': 'Serie RT750', 'de': 'RT750-Serie', 'ar': 'سلسلة RT750', 'ru': 'Серия RT750'},
    'RT1060 Series':    {'fr': 'Série RT1060', 'es': 'Serie RT1060', 'de': 'RT1060-Serie', 'ar': 'سلسلة RT1060', 'ru': 'Серия RT1060'},
}


def _t(label, lang='en'):
    """Translate a sidebar label. Falls back to the English original."""
    if lang == 'en':
        return label
    entry = _SIDEBAR_I18N.get(label, {})
    return entry.get(lang, label)


# Sidebar data for Projects page
def _get_projects_sidebar(lang='en'):
    """Return structured sidebar data for projects — list of dicts."""
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
    """Return structured sidebar data for products — list of dicts."""
    return [
        {
            'key': 'FLOODLIGHT',
            'label': _t('Flood Lighting', lang),
            'series': [
                {'key': 'M_SERIES', 'slug': 'm-series', 'label': _t('M Series', lang)},
                {'key': 'RT410_SERIES', 'slug': 'rt410-series', 'label': _t('RT410 Series', lang)},
            ],
        },
        {
            'key': 'HIGH_BAY',
            'label': _t('High Bay', lang),
            'series': [
                {'key': 'RT400_SERIES', 'slug': 'rt400-series', 'label': _t('RT400 Series', lang)},
                {'key': 'RT500_SERIES', 'slug': 'rt500-series', 'label': _t('RT500 Series', lang)},
            ],
        },
        {
            'key': 'STREET_LIGHTING',
            'label': _t('Street Lighting', lang),
            'series': [
                {'key': 'RT750_SERIES', 'slug': 'rt750-series', 'label': _t('RT750 Series', lang)},
                {'key': 'RT1060_SERIES', 'slug': 'rt1060-series', 'label': _t('RT1060 Series', lang)},
            ],
        },
    ]


def get_common_context():
    """Get context shared across all pages"""
    config = cache.get('site_config')
    if not config:
        config = SiteConfig.objects.first()
        if not config:
            config = SiteConfig.objects.create()
        cache.set('site_config', config, timeout=300)

    # Pre-compute static URLs for hero bg and logo
    if config.hero_background:
        config.hero_bg_url = static(config.hero_background.name)
    else:
        config.hero_bg_url = static('images/hero-main.fw.png')

    if config.logo:
        config.logo_url = static(config.logo.name)
    else:
        config.logo_url = static('images/logo.png')

    return {'config': config}


def home(request):
    return render(request, 'home.html', get_common_context())


def contact(request):
    context = get_common_context()

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            messages.success(request, _('Your message has been sent successfully!'))

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

    # Filter products
    products_list = Product.objects.all()
    if active_category:
        products_list = products_list.filter(category=active_category)
    if active_series:
        # series filter uses name matching (e.g. "RT410 Series")
        if active_series_label:
            products_list = products_list.filter(name__icontains=active_series_label.replace(' Series', ''))

    for p in products_list:
        if p.image:
            p.image_url = static(p.image.name)
        else:
            p.image_url = ''
        p.name_t = p.t('name', lang)
        p.description_t = p.t('description', lang)
        p.category_t = p.t('category', lang)
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

    # Filter projects
    projects_list = Project.objects.all()
    if active_venue_type:
        projects_list = projects_list.filter(venue_type=active_venue_type)
    if active_sport_type:
        projects_list = projects_list.filter(sport_type=active_sport_type)

    for proj in projects_list:
        if proj.image:
            proj.image_url = static(proj.image.name)
        else:
            proj.image_url = ''
        proj.title_t = proj.t('title', lang)
        proj.description_t = proj.t('description', lang)
        proj.location_t = proj.t('location', lang)
        proj.results_t = proj.t('results', lang)
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

    # Find current product and its series key for active state
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        product = None

    # Resolve active series key from product's category
    active_series = ''
    if product:
        for cat in product_categories:
            for s in cat['series']:
                if s['slug'] == slug:
                    active_series = s['key']
                    break
            if active_series:
                break
    context['active_series'] = active_series

    if product:
        if product.image:
            product.image_url = static(product.image.name)
        else:
            product.image_url = ''
        product.name_t = product.t('name', lang)
        product.description_t = product.t('description', lang)
        product.category_t = product.t('category', lang)
        context['product'] = product

    return render(request, 'product_detail.html', context)
