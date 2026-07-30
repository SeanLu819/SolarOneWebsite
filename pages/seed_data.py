"""Seed data embedded as Python module for Vercel compatibility.

On Vercel, non-Python files (like seed_data.json) are not automatically included
in the serverless function bundle. Embedding the data here ensures it is always
available via a normal Python import.
"""

SEED_DATA = {'products': [{'beam_angle': '',
               'category': 'FLOODLIGHT',
               'description': 'Truly modular design — scalable from a single 1M (80W) module up to 16M (1280W) or '
                              'beyond. Flexible combination configurations to precisely match any project requirement.',
               'efficacy': '',
               'image': 'images/processed/rt200-m.webp',
               'name': 'M Series',
               'order': 1,
               'output': '',
               'pk': 1,
               'power': '80~1280W+',
               'protection': 'IP67',
               'slug': 'm-series',
               'translations': {'ar': {'category': 'معيارية',
                                       'description': 'تصميم معياري حقيقي — قابل للتوسع من وحدة واحدة 1M (80 واط) إلى '
                                                      '16M (1280 واط) أو أكثر. تكوينات مرنة وقابلة للدمج لتلبية '
                                                      'متطلبات أي مشروع بدقة.',
                                       'name': 'سلسلة M'},
                                'de': {'category': 'Modular',
                                       'description': 'Wirklich modulares Design — skalierbar von einem einzelnen 1M '
                                                      '(80W) Modul bis zu 16M (1280W) oder mehr. Flexible '
                                                      'Kombinationskonfigurationen zur genauen Erfüllung jeder '
                                                      'Projektforderung.',
                                       'name': 'M-Serie'},
                                'es': {'category': 'Modular',
                                       'description': 'Diseño verdaderamente modular — escalable desde un solo módulo '
                                                      '1M (80W) hasta 16M (1280W) o más. Configuraciones combinables '
                                                      'flexibles para satisfacer con precisión los requisitos de '
                                                      'cualquier proyecto.',
                                       'name': 'Serie M'},
                                'fr': {'category': 'Modulaire',
                                       'description': 'Design véritablement modulaire — évolutif d’un seul module 1M '
                                                      '(80W) jusqu’à 16M (1280W) ou plus. Configurations combinables '
                                                      'flexibles pour répondre précisément aux exigences de chaque '
                                                      'projet.',
                                       'name': 'Série M'},
                                'ru': {'category': 'Модульные',
                                       'description': 'Истинно модульная конструкция — масштабируемая от одного модуля '
                                                      '1M (80 Вт) до 16M (1280 Вт) и более. Гибкие комбинации '
                                                      'конфигураций для точного соответствия требованиям любого '
                                                      'проекта.',
                                       'name': 'Серия M'}}},
              {'beam_angle': '18~100°',
               'category': 'FLOODLIGHT',
               'description': 'Professional LED floodlights designed for sports fields, arenas, and large-area '
                              'illumination. Flicker-free drivers with broadcast-grade performance.',
               'efficacy': '',
               'image': 'images/processed/floodlight.webp',
               'name': 'RT410 Series',
               'order': 2,
               'output': '125lm/W',
               'pk': 2,
               'power': '260W',
               'protection': '',
               'slug': 'rt410-series',
               'translations': {'ar': {'category': 'مشاريع إضاءة',
                                       'description': 'أضواء LED احترافية مصممة للملاعب الرياضية والصالات ومساحات '
                                                      'الإضاءة الكبيرة. محركات بدون وميض بأداء بث مباشر.',
                                       'name': 'سلسلة RT410'},
                                'de': {'category': 'Flutlicht',
                                       'description': 'Professionelle LED-Flutlichter für Sportfelder, Arenen und '
                                                      'Großflächenbeleuchtung. Flackerfreie Treiber mit '
                                                      'Broadcast-Qualität.',
                                       'name': 'RT410-Serie'},
                                'es': {'category': 'Proyector',
                                       'description': 'Proyectores LED profesionales diseñados para campos deportivos, '
                                                      'arenas e iluminación de grandes áreas. Drivers sin parpadeo con '
                                                      'rendimiento de calidad broadcast.',
                                       'name': 'Serie RT410'},
                                'fr': {'category': 'Projecteur',
                                       'description': 'Projecteurs LED professionnels conçus pour les terrains de '
                                                      'sport, les arènes et les grandes surfaces d’éclairage. Drivers '
                                                      'sans scintillement avec performance de qualité broadcast.',
                                       'name': 'Série RT410'},
                                'ru': {'category': 'Прожекторы',
                                       'description': 'Профессиональные LED-прожекторы для спортивных площадок, арен и '
                                                      'больших площадей освещения. Драйверы без мерцания с '
                                                      'трансляционным качеством.',
                                       'name': 'Серия RT410'}}},
              {'beam_angle': '',
               'category': 'HIGH_BAY',
               'description': 'Industrial high bay luminaires for warehouses, factories, and gymnasiums. High-efficacy '
                              'design with superior thermal management for 50,000+ hour life.',
               'efficacy': '120lm/W',
               'image': 'images/processed/HB.webp',
               'name': 'HB Series',
               'order': 3,
               'output': '',
               'pk': 4,
               'power': '100~300W',
               'protection': 'IP66',
               'slug': 'rt400-series',
               'translations': {}}],
 'projects': [{'description': 'A precision photometric design was completed to ensure that the design specifications '
                              'were met. The design called for replacement of 40 existing 1500W MH light fixtures with '
                              '48 of our FL9M-630W LED performance sports lights.',
               'image': 'images/processed/footballfield.webp',
               'location': 'United States',
               'order': 1,
               'pk': 1,
               'results': '<strong>30fc</strong> average illuminance, <strong>uniformity 1.37 : 1</strong> — exceeding '
                          'the project requirements.',
               'slug': 'football-field-led-retrofit',
               'sport_type': 'FOOTBALL_FIELD',
               'title': 'Football Field LED Retrofit',
               'translations': {'ar': {'description': 'تم إكمال تصميم ضوئي دقيق لضمان توافق المواصفات. تضمن المشروع '
                                                      'استبدال 40 مصابيح MH بقدرة 1500 وات بـ 48 من مصابيح LED '
                                                      'FL9M-630W.',
                                       'location': 'الولايات المتحدة',
                                       'results': 'متوسط إضاءة 30fc، uniformity 1.37:1 — تجاوز متطلبات المشروع.',
                                       'title': 'ترقية LED لملاعب كرة القدم'},
                                'de': {'description': 'Ein präzises fotometrisches Design wurde durchgeführt um '
                                                      'sicherzustellen, dass die Designspezifikationen erfüllt werden. '
                                                      'Das Projekt sah den Ersatz von 40 vorhandenen 1500W MH-Leuchten '
                                                      'durch 48 unserer FL9M-630W LED vor.',
                                       'location': 'Vereinigte Staaten',
                                       'results': '30fc durchschnittliche Beleuchtung, Gleichmäßigkeit 1.37:1 — '
                                                  'übertrifft die Projektanforderungen.',
                                       'title': 'LED-Umrüstung Fußballfeld'},
                                'es': {'description': 'Se completó un diseño fotométrico de precisión para garantizar '
                                                      'el cumplimiento de las especificaciones. El proyecto requería '
                                                      'el reemplazo de 40 luminarias MH de 1500W por 48 de nuestras '
                                                      'LED FL9M-630W.',
                                       'location': 'Estados Unidos',
                                       'results': '30fc iluminación promedio, uniformidad 1.37:1 — superando los '
                                                  'requisitos del proyecto.',
                                       'title': 'Renovación LED Campo de Fútbol'},
                                'fr': {'description': 'Un design photométrique de précision a été réalisé pour '
                                                      'garantir que les spécifications de conception soient '
                                                      'respectées. Le projet prévoyait le remplacement de 40 '
                                                      'projecteurs MH 1500W existants par 48 de nos LED FL9M-630W.',
                                       'location': 'États-Unis',
                                       'results': '30fc éclairage moyen, uniformité 1.37:1 — dépassant les exigences '
                                                  'du projet.',
                                       'title': 'Rénovation LED Terrain de Football'},
                                'ru': {'description': 'Был выполнен точный фотометрический расчёт для обеспечения '
                                                      'соответствия проектным спецификациям. Проект предусматривал '
                                                      'замену 40 существующих светильников МГ 1500Вт на 48 наших LED '
                                                      'FL9M-630W.',
                                       'location': 'Соединённые Штаты',
                                       'results': 'Средняя освещённость 30фк, равномерность 1.37:1 — превышение '
                                                  'требований проекта.',
                                       'title': 'Модернизация LED футбольного поля'}},
               'venue_type': 'OUTDOOR'},
              {'description': '150 FL9M-630W Performance Series LED sports lights with remote mount drivers were '
                              'installed. A networking control system was incorporated to allow for remote on/off '
                              'control and power monitoring.',
               'image': 'images/processed/Baseball.webp',
               'location': 'United States',
               'order': 2,
               'pk': 2,
               'results': '<strong>50/30fc</strong> average illuminance, <strong>uniformity 2.0:1 / 2.5:1</strong> — '
                          'meeting the project specifications.',
               'slug': 'baseball-field-led-retrofit',
               'sport_type': 'BASEBALL_FIELD',
               'title': 'Baseball Field LED Retrofit',
               'translations': {'ar': {'description': 'تم تركيب 150 مصابيح LED رياضية FL9M-630W من سلسلة الأداء مع '
                                                      'محركات تحكم عن بعد. تم دمج نظام تحكم شبكي للسماح '
                                                      'بالتشغيل/الإيقاف عن بعد ومراقبة الطاقة.',
                                       'location': 'الولايات المتحدة',
                                       'results': 'متوسط إضاءة 50/30fc، uniformity 2.0:1 / 2.5:1 — تلبي مواصفات '
                                                  'المشروع.',
                                       'title': 'ترقية LED لملاعب البيسبول'},
                                'de': {'description': '150 LED-Sportfluter FL9M-630W der Performance-Serie mit '
                                                      'Fernmontage-Treibern wurden installiert. Ein '
                                                      'Netzwerk-Steuerungssystem wurde integriert für ferngesteuerte '
                                                      'Ein/Aus-Steuerung und Leistungsüberwachung.',
                                       'location': 'Vereinigte Staaten',
                                       'results': '50/30fc durchschnittliche Beleuchtung, Gleichmäßigkeit 2.0:1 / '
                                                  '2.5:1 — erfüllt die Projektspezifikationen.',
                                       'title': 'LED-Umrüstung Baseballfeld'},
                                'es': {'description': 'Se instalaron 150 luminarias LED deportivas FL9M-630W de la '
                                                      'serie Performance con controladores de montaje remoto. Se '
                                                      'incorporó un sistema de control en red para permitir '
                                                      'encendido/apagado remoto y monitoreo de potencia.',
                                       'location': 'Estados Unidos',
                                       'results': '50/30fc iluminación promedio, uniformidad 2.0:1 / 2.5:1 — '
                                                  'cumpliendo las especificaciones del proyecto.',
                                       'title': 'Renovación LED Campo de Béisbol'},
                                'fr': {'description': '150 projecteurs LED sportifs FL9M-630W de la série Performance '
                                                      'avec drivers à montage distant ont été installés. Un système de '
                                                      'contrôle réseau a été intégré pour permettre le contrôle à '
                                                      'distance marche/arrêt et la surveillance de puissance.',
                                       'location': 'États-Unis',
                                       'results': '50/30fc éclairage moyen, uniformité 2.0:1 / 2.5:1 — respectant les '
                                                  'spécifications du projet.',
                                       'title': 'Rénovation LED Terrain de Baseball'},
                                'ru': {'description': 'Установлены 150 спортивных LED-прожекторов FL9M-630W серии '
                                                      'Performance с удалёнными драйверами. Интегрирована сетевая '
                                                      'система управления для дистанционного включения/выключения и '
                                                      'мониторинга мощности.',
                                       'location': 'Соединённые Штаты',
                                       'results': 'Средняя освещённость 50/30фк, равномерность 2.0:1 / 2.5:1 — '
                                                  'соответствие проектным спецификациям.',
                                       'title': 'Модернизация LED бейбольного поля'}},
               'venue_type': 'OUTDOOR'},
              {'description': 'A multipurpose venue in France designed for HD television broadcast, convertible '
                              'between basketball and tennis configurations. FL9M-630W LED sports lights fully satisfy '
                              'the lighting requirements for both court types.',
               'image': 'images/processed/basketball.webp',
               'location': 'France',
               'order': 3,
               'pk': 3,
               'results': '<strong>&gt;2000 lux</strong> — meeting HD broadcast standards.',
               'slug': 'multi-sport-arena-hd-broadcast',
               'sport_type': 'MULTI_SPORT',
               'title': 'Multi-Sport Arena HD Broadcast',
               'translations': {'ar': {'description': 'مرفق متعدد الأغراض في فرنسا مصمم للتلفزيون عالي الدقة، قابل '
                                                      'للتحويل بين إعدادات كرة السلة والتنس. مصابيح LED FL9M-630W تلبي '
                                                      'بالكامل متطلبات الإضاءة.',
                                       'location': 'فرنسا',
                                       'results': '>2000 لوكس — تلبي معايير البث عالي الدقة.',
                                       'title': 'صالة رياضية متعددة الألعاب بث HD'},
                                'de': {'description': 'Eine Mehrzweckhalle in Frankreich für HD-Fernsehen, umschaltbar '
                                                      'zwischen Basketball- und Tennis-Konfiguration. FL9M-630W '
                                                      'LED-Sportfluter erfüllen vollumfänglich die '
                                                      'Beleuchtungsanforderungen.',
                                       'location': 'Frankreich',
                                       'results': '>2000 Lux — erfüllt HD-Broadcast-Standards.',
                                       'title': 'Mehrzweck-HD-Broadcast-Arena'},
                                'es': {'description': 'Un recinto polideportivo en Francia diseñado para televisión '
                                                      'HD, convertible entre configuraciones de baloncesto y tenis. '
                                                      'Las luminarias LED FL9M-630W satisfacen plenamente los '
                                                      'requisitos de iluminación.',
                                       'location': 'Francia',
                                       'results': '>2000 lux — cumpliendo los estándares de transmisión HD.',
                                       'title': 'Arena Multideporte HD Broadcast'},
                                'fr': {'description': 'Un lieu polyvalent en France conçu pour la télévision HD, '
                                                      'convertible entre configurations basket et tennis. Les '
                                                      'projecteurs LED FL9M-630W satisfont pleinement les exigences '
                                                      'd’éclairage pour le basket et le tennis.',
                                       'location': 'France',
                                       'results': '>2000 lux — répondant aux normes de diffusion HD.',
                                       'title': 'Arène Multisport HD Broadcast'},
                                'ru': {'description': 'Многоцелевой комплекс во Франции, спроектированный для '
                                                      'HD-телевидения, преобразуемый между баскетбольными и теннисными '
                                                      'конфигурациями. LED-прожекторы FL9M-630W полностью '
                                                      'удовлетворяют требованиям освещения.',
                                       'location': 'Франция',
                                       'results': '>2000 люкс — соответствие стандартам HD-вещания.',
                                       'title': 'Многоспортивная арена HD-вещания'}},
               'venue_type': 'INDOOR'},
              {'description': 'A multipurpose stadium in Shanghai Pudong New Area with 160,000 sqm and 20,000 seats. '
                              '320 FL12M-1000W LED sports lights (CCT: 5000-5500K) with networking control system for '
                              'remote on/off and power monitoring.',
               'image': 'images/processed/soccerfield.webp',
               'location': 'Shanghai, China',
               'order': 4,
               'pk': 4,
               'results': '<strong>2200 lux avg.</strong>, <strong>U0=0.8</strong>, <strong>Ra&gt;80</strong> — '
                          'meeting AFC Stadium Lighting Guidelines 2018.',
               'slug': 'yuanshen-sports-centre-stadium',
               'sport_type': 'SOCCER_FIELD',
               'title': 'Yuanshen Sports Centre Stadium',
               'translations': {'ar': {'description': 'ملعب متعدد الأغراض في شنغهاي بودونغ بمساحة 160,000 م² و20,000 '
                                                      'مقعد. 320 مصباح LED رياضي FL12M-1000W مع نظام تحكم شبكي.',
                                       'location': 'شنغهاي، الصين',
                                       'results': 'متوسط 2200 لوكس، U0=0.8، Ra>80 — تلبي إرشادات AFC لإضاءة الملاعب '
                                                  '2018.',
                                       'title': 'ملعب مركز يوانشين الرياضي'},
                                'de': {'description': 'Ein Mehrzweckstadion in Shanghai Pudong mit 160.000 m² und '
                                                      '20.000 Sitzplätzen. 320 LED-Sportfluter FL12M-1000W (TDF: '
                                                      '5000-5500K) mit Netzwerk-Steuerungssystem.',
                                       'location': 'Shanghai, China',
                                       'results': '2200 Lux Durchschnitt, U0=0.8, Ra>80 — erfüllt '
                                                  'AFC-Stadionbeleuchtungsrichtlinien 2018.',
                                       'title': 'Yuanshen Sportzentrum Stadion'},
                                'es': {'description': 'Un estadio polideportivo en Shanghai Pudong con 160,000 m² y '
                                                      '20,000 asientos. 320 luminarias LED FL12M-1000W (TCP: '
                                                      '5000-5500K) con sistema de control en red para '
                                                      'encendido/apagado remoto y monitoreo.',
                                       'location': 'Shanghai, China',
                                       'results': '2200 lux prom., U0=0.8, Ra>80 — cumpliendo las Directrices de '
                                                  'Iluminación de Estadios AFC 2018.',
                                       'title': 'Estadio del Centro Deportivo Yuanshen'},
                                'fr': {'description': 'Un stade polyvalent à Shanghai Pudong avec 160 000 m² et 20 000 '
                                                      'places. 320 projecteurs LED FL12M-1000W (TCP: 5000-5500K) avec '
                                                      'système de contrôle réseau pour la commande à distance et le '
                                                      'monitoring de puissance.',
                                       'location': 'Shanghai, Chine',
                                       'results': '2200 lux moy., U0=0.8, Ra>80 — répondant aux directives AFC Stadium '
                                                  'Lighting 2018.',
                                       'title': 'Stade du Centre Sportif Yuanshen'},
                                'ru': {'description': 'Многоцелевой стадион в районе Пудун, Шанхай, площадью 160 000 '
                                                      'м² на 20 000 мест. 320 спортивных LED-прожекторов FL12M-1000W '
                                                      '(ЦТТ: 5000-5500К) с сетевой системой управления.',
                                       'location': 'Шанхай, Китай',
                                       'results': 'Средняя 2200 люкс, U0=0.8, Ra>80 — соответствие руководящим '
                                                  'принципам AFC по освещению стадионов 2018.',
                                       'title': 'Стадион Спортивного центра Юаньшэнь'}},
               'venue_type': 'OUTDOOR'}],
 'siteconfig': {'about_stat_clients': '1000+',
                'about_stat_clients_label': 'Happy Clients',
                'about_stat_countries': '50+',
                'about_stat_countries_label': 'Countries Served',
                'about_stat_projects': '500+',
                'about_stat_projects_label': 'Projects Delivered',
                'about_stat_years': '18+',
                'about_stat_years_label': 'Years Experience',
                'about_text_1': 'Since 2007, SolarOne Vision has focused on the design and manufacture of high power '
                                'LED Sports lighting systems, LED Roadway infrastructure lighting systems, and LED '
                                'industrial lighting systems. We bring first-hand knowledge and experience for new and '
                                'retrofit projects — from small projects requiring a few lights to professional '
                                "high-level facilities, we've got you covered.",
                'about_text_2': "SolarOne's mission is to deliver innovative outdoor and indoor lighting solutions for "
                                'recreational, high school, college, and semi-professional sports venues, airports, '
                                'seaports, and other industrial facilities. We protect the environment, reduce energy '
                                'consumption, deliver satisfying and inspiring lighting experiences, and add value to '
                                "people's vision of life.",
                'about_title': 'Trusted worldwide for a reason.',
                'accent_color': '#0088FF',
                'brand_name': 'SolarOne',
                'contact_address': 'Beijing, China',
                'contact_email': 'sales@solarone.com',
                'contact_phone_1': '+8613910887405',
                'contact_phone_2': '+86 130 0000 0000',
                'contact_subtitle': 'Have a project in mind? Send us the details and our engineering team will respond '
                                    'with a full photometric proposal within 48 hours.',
                'contact_title': 'Get in Touch',
                'contact_whatsapp': '+86 13910887405',
                'font_family_body': "'Inter', 'Helvetica Neue', Arial, sans-serif",
                'font_family_heading': "'Inter', 'Helvetica Neue', Arial, sans-serif",
                'font_size_base': '16px',
                'font_size_body': '1.05rem',
                'font_size_card_desc': '0.95rem',
                'font_size_card_title': '1.25rem',
                'font_size_hero_subtitle': '1.15rem',
                'font_size_hero_title': '3.5rem',
                'font_size_nav': '17px',
                'font_size_section_title': '2.25rem',
                'footer_description': 'Professional LED lighting systems for sports, industrial, and infrastructure '
                                      'applications. Engineered in Beijing since 2007, trusted in 50+ countries '
                                      'worldwide.',
                'hero_background': '',
                'hero_subtitle': 'Professional SolarOne sports lighting solutions trusted in over 50 countries. From '
                                 'community fields to broadcast-ready stadiums, engineered for performance, built to outlast.',
                'hero_title': 'The Next Generation Lighting Systems For Every Area',
                'logo': '',
                'meta_description': 'Professional LED sports lighting, high bay, and modular luminaire solutions. '
                                    'Engineered in Beijing since 2007, trusted in 50+ countries worldwide.',
                'meta_title': 'SolarOne — Precision LED Lighting Systems',
                'og_image': '',
                'products_subtitle': 'From compact modular luminaires to stadium-grade high bay systems. Precision '
                                     'optics, modular architecture, and field-proven reliability across every product '
                                     'line.',
                'products_title': 'Our Products',
                'projects_subtitle': 'Real installations across five continents. From Olympic training centers to '
                                     'community football pitches, our luminaires deliver reliable performance under '
                                     'the toughest conditions.',
                'projects_title': 'Featured Projects',
                'social_facebook': 'https://facebook.com',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': '',
                'social_tiktok': 'https://tiktok.com',
                'social_youtube': 'https://youtube.com',
                'stat_countries': '50+',
                'stat_countries_label': 'Countries',
                'stat_energy': '50%+',
                'stat_energy_label': 'Energy Save',
                'stat_projects': '500+',
                'stat_projects_label': 'Projects',
                'stat_support': '5+',
                'stat_support_label': 'warranty'}}
