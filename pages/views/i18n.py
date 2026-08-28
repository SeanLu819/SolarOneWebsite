# Product card display labels (per slug, matching sidebar category names)
_PRODUCT_CARD_LABELS = {
    'm-series': 'Area and Site',
    'rt410-series': 'Area and Site',
    'vsp-xxxxw-9m-yp': 'Sports Lighting System',
    'vsp-xxxxw-12m-yp': 'Flood Lighting',
    'fl1m': 'Roadway',
    'rt590fl-s': 'Flood Lighting',
    'rt600sl-t': 'Roadway',
}

# Product category → sidebar category display label mapping
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
    'Velodrome':        {'fr': 'Vélodrome', 'es': 'Velódromo', 'de': 'Radrennbahn', 'ar': 'حلبة سباق الدراجات', 'ru': 'Велодром'},
    'Tennis & Pickleball': {'fr': 'Tennis & Pickleball', 'es': 'Tenis y Pickleball', 'de': 'Tennis & Pickleball', 'ar': 'التنس والبيكل بول', 'ru': 'Теннис и Пиклбол'},
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


def _product_category_filter(active_category):
    """Return a list of Product.category values for a sidebar category key."""
    return _SIDEBAR_CAT_TO_PRODUCT_CAT.get(active_category, [active_category])


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
                {'key': 'KARTING', 'label': _t('Karting Track', lang)},
            ],
        },
        {
            'key': 'INDOOR',
            'label': _t('Indoor Sports', lang),
            'sports': [
                {'key': 'MULTI_SPORT', 'label': _t('Multi-Sport Arena', lang)},
                {'key': 'BASKETBALL', 'label': _t('Basketball', lang)},
                {'key': 'VELODROME', 'label': _t('Velodrome', lang)},
                {'key': 'TENNIS', 'label': _t('Tennis & Pickleball', lang)},
                {'key': 'ICE_ARENA', 'label': _t('Ice Arena', lang)},
                {'key': 'FENCING', 'label': _t('Fencing', lang)},
                {'key': 'AQUATICS_CENTRE', 'label': _t('Aquatics Centre', lang)},
            ],
        },
        {
            'key': 'INFRASTRUCTURE',
            'label': _t('Airports', lang),
            'sports': [
                {'key': 'AIRPORT', 'label': _t('Airport', lang)},
            ],
        },
        {
            'key': 'ROADWAY',
            'label': _t('Roadway', lang),
            'sports': [
                {'key': 'CITY_EXPRESSWAY', 'label': _t('City Expressway', lang)},
            ],
        },
    ]


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
            'label': _t('Flood Lighting', lang),
            'series': [
                {'key': 'RT590FL_S', 'slug': 'rt590fl-s', 'label': 'RT590FL-S'},
                {'key': 'RT390FL',   'slug': 'rt390fl',   'label': 'RT390FL'},
                {'key': 'RT220UB',   'slug': 'rt220ub',   'label': 'RT220UB'},
                {'key': 'RT420FS_S', 'slug': 'rt420fs-s', 'label': 'RT420FS-S'},
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


def _resolve_project_sidebar(sport_type, lang='en', db_venue_type=''):
    """Resolve active_venue_type and active_sport_type for a project."""
    sidebar = _get_projects_sidebar(lang)
    canonical_venue = ''
    canonical_sport = ''
    for vt in sidebar:
        for st in vt['sports']:
            if st['key'] == sport_type:
                canonical_venue = vt['key']
                canonical_sport = st['key']
                break
        if canonical_sport:
            break
    if not canonical_sport:
        return '', ''

    active_venue_type = canonical_venue
    if db_venue_type and db_venue_type != canonical_venue:
        for vt in sidebar:
            if vt['key'] == db_venue_type:
                for st in vt['sports']:
                    if st['key'] == sport_type:
                        active_venue_type = db_venue_type
                        break
                break
    return active_venue_type, canonical_sport