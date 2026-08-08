"""Seed data embedded as Python module for Vercel compatibility.

On Vercel, non-Python files (like seed_data.json) are not automatically included
in the serverless function bundle. Embedding the data here ensures it is always
available via a normal Python import.
"""

SEED_DATA = {
  "products": [
    {
      "pk": 1,
      "name": "M Series",
      "slug": "m-series",
      "category": "AREA_SITE",
      "description": "Truly modular design — scalable from a single 1M (80W) module up to 16M (1280W) or beyond. Flexible combination configurations to precisely match any project requirement.",
      "power": "80~1280W+",
      "efficacy": "125lm/W",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/m-series/rt200-m.webp",
      "banner_image": "images/products/m-series/m-series-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 1,
      "parent_slug": "",
      "translations": {
        "fr": {
          "name": "Série M",
          "category": "Modulaire",
          "description": "Design véritablement modulaire — évolutif d’un seul module 1M (80W) jusqu’à 16M (1280W) ou plus. Configurations combinables flexibles pour répondre précisément aux exigences de chaque projet."
        },
        "es": {
          "name": "Serie M",
          "category": "Modular",
          "description": "Diseño verdaderamente modular — escalable desde un solo módulo 1M (80W) hasta 16M (1280W) o más. Configuraciones combinables flexibles para satisfacer con precisión los requisitos de cualquier proyecto."
        },
        "de": {
          "name": "M-Serie",
          "category": "Modular",
          "description": "Wirklich modulares Design — skalierbar von einem einzelnen 1M (80W) Modul bis zu 16M (1280W) oder mehr. Flexible Kombinationskonfigurationen zur genauen Erfüllung jeder Projektforderung."
        },
        "ru": {
          "name": "Серия M",
          "category": "Модульные",
          "description": "Истинно модульная конструкция — масштабируемая от одного модуля 1M (80 Вт) до 16M (1280 Вт) и более. Гибкие комбинации конфигураций для точного соответствия требованиям любого проекта."
        },
        "ar": {
          "name": "سلسلة M",
          "category": "معيارية",
          "description": "تصميم معياري حقيقي — قابل للتوسع من وحدة واحدة 1M (80 واط) إلى 16M (1280 واط) أو أكثر. تكوينات مرنة وقابلة للدمج لتلبية متطلبات أي مشروع بدقة."
        }
      },
      "gallery": [
        "images/products/m-series/m-series-01.webp",
        "images/products/m-series/m-series-02.webp",
        "images/products/m-series/m-series-03.webp",
        "images/products/m-series/m-series-04.webp"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "80~1280W+"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 2,
      "name": "RT410 Series",
      "slug": "rt410-series",
      "category": "AREA_SITE",
      "description": "Professional LED floodlights designed for sports fields, arenas, and large-area illumination. Flicker-free drivers with broadcast-grade performance.",
      "power": "260W",
      "efficacy": "125lm/W",
      "output": "",
      "beam_angle": "18~100°",
      "protection": "",
      "image": "images/products/rt410-series/floodlight.webp",
      "banner_image": "images/products/rt410-series/rt410-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 2,
      "parent_slug": "",
      "translations": {
        "fr": {
          "name": "Série RT410",
          "category": "Projecteur",
          "description": "Projecteurs LED professionnels conçus pour les terrains de sport, les arènes et les grandes surfaces d’éclairage. Drivers sans scintillement avec performance de qualité broadcast."
        },
        "es": {
          "name": "Serie RT410",
          "category": "Proyector",
          "description": "Proyectores LED profesionales diseñados para campos deportivos, arenas e iluminación de grandes áreas. Drivers sin parpadeo con rendimiento de calidad broadcast."
        },
        "de": {
          "name": "RT410-Serie",
          "category": "Flutlicht",
          "description": "Professionelle LED-Flutlichter für Sportfelder, Arenen und Großflächenbeleuchtung. Flackerfreie Treiber mit Broadcast-Qualität."
        },
        "ru": {
          "name": "Серия RT410",
          "category": "Прожекторы",
          "description": "Профессиональные LED-прожекторы для спортивных площадок, арен и больших площадей освещения. Драйверы без мерцания с трансляционным качеством."
        },
        "ar": {
          "name": "سلسلة RT410",
          "category": "مشاريع إضاءة",
          "description": "أضواء LED احترافية مصممة للملاعب الرياضية والصالات ومساحات الإضاءة الكبيرة. محركات بدون وميض بأداء بث مباشر."
        }
      },
      "gallery": [
        "images/products/rt410-series/rt410fl-s-01.webp",
        "images/products/rt410-series/rt410fl-s-02.webp",
        "images/products/rt410-series/rt410fl-s-03.webp",
        "images/products/rt410-series/rt410fl-s-04.webp"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "260W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "32500+lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~100°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 11,
      "name": "VSP-XXXXW-9M-YP",
      "slug": "vsp-xxxxw-9m-yp",
      "category": "SPORTS_LIGHTING",
      "description": "Vision Strobe Protection system for broadcast venues. Eliminates flicker in slow-motion replay with stable, high-frequency drive technology.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/vsp-xxxxw-9m-yp/vsp12m-01.webp",
      "banner_image": "images/products/vsp-xxxxw-9m-yp/vsp-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 3,
      "parent_slug": "",
      "translations": {
        "ar": {
          "category": "نظام إضاءة رياضية",
          "description": "نظام حماية ضد الوامض للمنشآت الإذاعية. يقضي على الوميض في إعادة العرض البطيئة بتقنية تشغيل عالية التردد ومستقرة.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "de": {
          "category": "Sportbeleuchtungssystem",
          "description": "Vision Strobe Protection-System für Broadcast-Veranstaltungsorte. Beseitigt Flackern bei Zeitlupenwiedergaben durch stabile Hochfrequenz-Antriebstechnologie.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "es": {
          "category": "Sistema de Iluminación Deportiva",
          "description": "Sistema de protección contra parpadeo de visión para recintos de broadcast. Elimina el parpadeo en reproducciones a cámara lenta con tecnología de accionamiento de alta frecuencia estable.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "fr": {
          "category": "Système d'Éclairage Sportif",
          "description": "Système de protection anti-stroboscope pour sites de diffusion. Élimine le scintillement des ralentis grâce à une technologie de commande haute fréquence stable.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "ru": {
          "category": "Система спортивного освещения",
          "description": "Система защиты от стробоскопического эффекта для телевизионных объектов. Устраняет мерцание при замедленной съемке за счет стабильной высокочастотной технологии питания.",
          "name": "VSP-XXXXW-9M-YP"
        }
      },
      "gallery": [
        "images/products/vsp-xxxxw-9m-yp/VSP9M-01.webp",
        "images/products/vsp-xxxxw-9m-yp/VSP9M-02.webp",
        "images/products/vsp-xxxxw-9m-yp/VSP9M-03.webp",
        "images/products/vsp-xxxxw-9m-yp/VSP9M-04.webp"
      ],
      "specs": [],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 13,
      "name": "RT590FL-S",
      "slug": "rt590fl-s",
      "category": "FLOODLIGHT",
      "description": "Professional LED floodlight designed for large-area illumination, sports fields, and industrial sites. High-efficacy performance with robust thermal management for long-lasting reliability.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt590fl-s/rt590.webp",
      "banner_image": "images/products/rt590fl-s/vsp-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 4,
      "parent_slug": "",
      "translations": {},
      "gallery": [],
      "specs": [],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 4,
      "name": "HB Series",
      "slug": "rt400-series",
      "category": "HIGHBAY_LOWBAY",
      "description": "Industrial high bay luminaires for warehouses, factories, and gymnasiums. High-efficacy design with superior thermal management for 50,000+ hour life.",
      "power": "100~300W",
      "efficacy": "120lm/W",
      "output": "",
      "beam_angle": "",
      "protection": "IP66",
      "image": "images/products/rt400-series/HB.webp",
      "banner_image": "",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 5,
      "parent_slug": "",
      "translations": {},
      "gallery": [],
      "specs": [
        {
          "label": "Power",
          "value": "100~300W"
        },
        {
          "label": "Efficacy",
          "value": "120lm/W"
        },
        {
          "label": "Protection",
          "value": "IP66"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 14,
      "name": "RT600SL-T",
      "slug": "rt600sl-t",
      "category": "ROADWAY",
      "description": "Professional LED roadway lighting solution designed for streets, highways, and infrastructure projects. Delivers uniform illumination with energy-efficient performance.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt600sl-t/RT600SL-T.webp",
      "banner_image": "images/products/rt600sl-t/fl1m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 6,
      "parent_slug": "",
      "translations": {},
      "gallery": [],
      "specs": [],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 6,
      "name": "FL4M",
      "slug": "fl4m",
      "category": "AREA_SITE",
      "description": "FL4M modular floodlight configuration — part of the M Series family.",
      "power": "320W",
      "efficacy": "125lm/W",
      "output": "40K+ lm",
      "beam_angle": "18~50°",
      "protection": "",
      "image": "images/products/fl4m/fl4m-01.png",
      "banner_image": "images/products/fl4m/fl4m-bar-1.webp",
      "dimension_image": "images/products/fl4m/fl4m-3d-view.png",
      "beam_angle_image": "images/products/fl4m/beamangle-12183050.webp",
      "order": 12,
      "parent_slug": "m-series",
      "translations": {
        "fr": {
          "description": "Configuration modulaire de projecteur FL4M — fait partie de la famille Série M."
        },
        "es": {
          "description": "Configuración modular de proyector FL4M — parte de la familia Serie M."
        },
        "de": {
          "description": "Modulare FL4M-Flutlichtkonfiguration — Teil der M-Serie-Familie."
        },
        "ru": {
          "description": "Модульная конфигурация прожектора FL4M — часть семейства серии M."
        },
        "ar": {
          "description": "تكوين وحدات كاشف FL4M — جزء من عائلة سلسلة M."
        }
      },
      "gallery": [
        "images/products/fl4m/fl4m-01.png",
        "images/products/fl4m/fl4m-02.png",
        "images/products/fl4m/fl4m-03.png",
        "images/products/fl4m/fl4m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "320W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "40K+ lm"
        },
        {
          "label": "Beam Angle",
          "value": "12~50°"
        },
        {
          "label": "CCT",
          "value": "3000~5700K"
        },
        {
          "label": "CRI",
          "value": "70~95"
        }
      ],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL4M-320W"
        },
        {
          "label": "Lumen Output",
          "value": ">41,600lm"
        },
        {
          "label": "System Wattage",
          "value": "320W"
        },
        {
          "label": "CRI",
          "value": "70~95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347~480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110~277VAC"
        },
        {
          "label": "L70 Hours",
          "value": "100,000 at 25°C"
        },
        {
          "label": "Operating Temperature Range",
          "value": "-40°C to 55°C"
        },
        {
          "label": "Surge (Common Mode / Differential Mode)",
          "value": "10kV"
        },
        {
          "label": "IP Rating",
          "value": "IP66"
        },
        {
          "label": "Effective Projected Area (EPA) at 90°",
          "value": "1.05 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "14.5\" X 14.5\"X 8.1\" / 368*368*343mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 24.5 lbs) 11.00 kgs"
        },
        {
          "label": "Material",
          "value": "Aluminum / Glass"
        },
        {
          "label": "LED Brand",
          "value": "Bridgelux"
        },
        {
          "label": "LED Driver",
          "value": "Inventronics Or Equal"
        }
      ],
      "ordering_info": [
        "FL4M\r\n(Light With 4 Module)",
        "320W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage\r\n(110-277VAC)\r\nH=High Voltage\r\n(347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1. 0-10V\r\n2. DMX\r\n3. Dali\r\n4. Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ],
      "model_number": "FL4M-320W-30K-S"
    },
    {
      "pk": 7,
      "name": "FL6M",
      "slug": "fl6m",
      "category": "AREA_SITE",
      "description": "FL6M modular floodlight configuration — part of the M Series family.",
      "power": "480W",
      "efficacy": "125lm/W",
      "output": "60K+ lm",
      "beam_angle": "18~50°",
      "protection": "",
      "image": "images/products/fl6m/fl6m-01.png",
      "banner_image": "images/products/fl6m/fl6m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 13,
      "parent_slug": "m-series",
      "translations": {},
      "gallery": [
        "images/products/fl6m/fl6m-01.png",
        "images/products/fl6m/fl6m-02.png",
        "images/products/fl6m/fl6m-03.png",
        "images/products/fl6m/fl6m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "480W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "60K+ lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~50°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 8,
      "name": "FL9M",
      "slug": "fl9m",
      "category": "AREA_SITE",
      "description": "FL9M modular floodlight configuration — part of the M Series family.",
      "power": "630W",
      "efficacy": "125lm/W",
      "output": "90K+ lm",
      "beam_angle": "18~50°",
      "protection": "",
      "image": "images/products/fl9m/fl9m-01.png",
      "banner_image": "images/products/fl9m/fl9m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 14,
      "parent_slug": "m-series",
      "translations": {},
      "gallery": [
        "images/products/fl9m/fl9m-01.png",
        "images/products/fl9m/fl9m-02.png",
        "images/products/fl9m/fl9m-03.png",
        "images/products/fl9m/fl9m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "630W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "90K+ lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~50°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 9,
      "name": "FL12M",
      "slug": "fl12m",
      "category": "AREA_SITE",
      "description": "FL12M modular floodlight configuration — part of the M Series family.",
      "power": "1000W",
      "efficacy": "125lm/W",
      "output": "120K+ lm",
      "beam_angle": "18~50°",
      "protection": "",
      "image": "images/products/fl12m/fl12m-01.png",
      "banner_image": "images/products/fl12m/fl12m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 15,
      "parent_slug": "m-series",
      "translations": {},
      "gallery": [
        "images/products/fl12m/fl12m-01.png",
        "images/products/fl12m/fl12m-02.png",
        "images/products/fl12m/fl12m-03.png",
        "images/products/fl12m/fl12m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "1000W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "120K+ lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~50°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 12,
      "name": "VSP-XXXXW-12M-YP",
      "slug": "vsp-xxxxw-12m-yp",
      "category": "SPORTS_LIGHTING",
      "description": "Vision Strobe Protection system for broadcast venues. Eliminates flicker in slow-motion replay with stable, high-frequency drive technology.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/vsp-xxxxw-12m-yp/rt590.webp",
      "banner_image": "images/products/vsp-xxxxw-12m-yp/vsp-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 15,
      "parent_slug": "vsp-xxxxw-9m-yp",
      "translations": {
        "ar": {
          "category": "نظام إضاءة رياضية",
          "description": "نظام حماية ضد الوامض للمنشآت الإذاعية. يقضي على الوميض في إعادة العرض البطيئة بتقنية تشغيل عالية التردد ومستقرة.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "de": {
          "category": "Sportbeleuchtungssystem",
          "description": "Vision Strobe Protection-System für Broadcast-Veranstaltungsorte. Beseitigt Flackern bei Zeitlupenwiedergaben durch stabile Hochfrequenz-Antriebstechnologie.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "es": {
          "category": "Sistema de Iluminación Deportiva",
          "description": "Sistema de protección contra parpadeo de visión para recintos de broadcast. Elimina el parpadeo en reproducciones a cámara lenta con tecnología de accionamiento de alta frecuencia estable.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "fr": {
          "category": "Système d'Éclairage Sportif",
          "description": "Système de protection anti-stroboscope pour sites de diffusion. Élimine le scintillement des ralentis grâce à une technologie de commande haute fréquence stable.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "ru": {
          "category": "Система спортивного освещения",
          "description": "Система защиты от стробоскопического эффекта для телевизионных объектов. Устраняет мерцание при замедленной съемке за счет стабильной высокочастотной технологии питания.",
          "name": "VSP-XXXXW-12M-YP"
        }
      },
      "gallery": [
        "images/products/vsp-xxxxw-12m-yp/vsp12m-01.webp",
        "images/products/vsp-xxxxw-12m-yp/vsp12m-02.webp",
        "images/products/vsp-xxxxw-12m-yp/vsp12m-03.webp",
        "images/products/vsp-xxxxw-12m-yp/vsp12m-04.webp"
      ],
      "specs": [],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 5,
      "name": "FL1M",
      "slug": "fl1m",
      "category": "AREA_SITE",
      "description": "FL1M modular floodlight configuration — part of the M Series family.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/fl1m/RT600SL-T.webp",
      "banner_image": "images/products/fl1m/fl1m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 16,
      "parent_slug": "m-series",
      "translations": {},
      "gallery": [
        "images/products/fl1m/fl1m-01.png",
        "images/products/fl1m/fl1m-02.png",
        "images/products/fl1m/fl1m-03.png",
        "images/products/fl1m/fl1m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "80W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "10k+lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~50°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    },
    {
      "pk": 10,
      "name": "FL16M",
      "slug": "fl16m",
      "category": "AREA_SITE",
      "description": "FL16M modular floodlight configuration — part of the M Series family.",
      "power": "1280W",
      "efficacy": "125lm/W",
      "output": "160K+ lm",
      "beam_angle": "18~50°",
      "protection": "",
      "image": "images/products/fl16m/fl16m-01.png",
      "banner_image": "images/products/fl16m/fl16m-bar-1.webp",
      "dimension_image": "",
      "beam_angle_image": "",
      "order": 16,
      "parent_slug": "m-series",
      "translations": {},
      "gallery": [
        "images/products/fl16m/fl16m-01.png",
        "images/products/fl16m/fl16m-02.png",
        "images/products/fl16m/fl16m-03.png",
        "images/products/fl16m/fl16m-04.png"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "1280W"
        },
        {
          "label": "Efficacy",
          "value": "125lm/W"
        },
        {
          "label": "Output",
          "value": "160K+ lm"
        },
        {
          "label": "Beam Angle",
          "value": "18~50°"
        }
      ],
      "energy_data": [],
      "ordering_info": [],
      "model_number": ""
    }
  ],
  "projects": [
    {
      "pk": 1,
      "title": "Bohemia Manor High School",
      "location": "United States",
      "slug": "football-field-led-retrofit",
      "venue_type": "OUTDOOR",
      "sport_type": "FOOTBALL_FIELD",
      "description": "【Customer Profile】\r\nBohemia Manor High School is a public school operated by Cecil County Public Schools located approximately one mile south of the small town of Chesapeake City in Cecil County, MD. This is a small school of 685 students which shares its campus with Bohemia Manor Middle School. The\r\nschool is also known by the nickname \"Bo Manor.“\r\n\r\n【Scope of Work】\r\nThe original lighting at the “Bo Manor” field was inefficient, under lit, and hassle to maintain. Also, the specifications of the project required use of the existing poles and structures.\r\n\r\n【The Solution】\r\nA precision photometric design was completed to ensure that the design specifications were met. The design called for replacement (40 total) of the existing 1500W MH light fixtures to (48 total) of our FL9M -630W LED performance sports lights.",
      "results": "<strong>30fc</strong> average illuminance, <strong>uniformity 1.37 : 1</strong> — exceeding the project requirements.",
      "image": "images/processed/footballfield.webp",
      "order": 1,
      "translations": {
        "fr": {
          "title": "Lycée Bohemia Manor",
          "location": "États-Unis",
          "description": "【Profil du client】\nBohemia Manor High School est une école publique gérée par Cecil County Public Schools située à environ 1,6 km au sud de la petite ville de Chesapeake City dans le comté de Cecil, MD. Il s'agit d'une petite école de 685 élèves qui partage son campus avec le collège Bohemia Manor.\nl'école est également connue sous le surnom de « Bo Manor ».\n\n【Étendue des travaux】\nL'éclairage d'origine du champ « Bo Manor » était inefficace, sous-éclairé et difficile à entretenir. En outre, les spécifications du projet nécessitaient l'utilisation des poteaux et des structures existants.\n\n【La solution】\nUne conception photométrique de précision a été réalisée pour s'assurer que les spécifications de conception étaient respectées. La conception a nécessité le remplacement (40 au total) des luminaires 1500W MH existants par (48 au total) de nos lampes de sport à LED FL9M -630W.",
          "results": "<strong>Éclairage</strong> moyen de 30 fc, <strong>uniformité 1,37 : 1</strong> — dépassant les exigences du projet."
        },
        "es": {
          "title": "Escuela Secundaria Bohemia Manor",
          "location": "Estados Unidos",
          "description": "Perfil 【del cliente】\nBohemia Manor High School es una escuela pública operada por las Escuelas Públicas del Condado de Cecil ubicada aproximadamente a una milla al sur de la pequeña ciudad de Chesapeake City en el Condado de Cecil, MD. Esta es una pequeña escuela de 685 estudiantes que comparte su campus con Bohemia Manor Middle School.\nla escuela también es conocida con el apodo de \"Bo Manor\".\n\n【Alcance del trabajo】\nLa iluminación original en el campo \"Bo Manor\" era ineficiente, poco iluminada y molesta de mantener. Además, las especificaciones del proyecto requerían el uso de los postes y estructuras existentes.\n\n【La solución】\nSe completó un diseño fotométrico de precisión para garantizar que se cumplieran las especificaciones de diseño. El diseño requería el reemplazo (40 en total) de los accesorios de iluminación existentes de 1500W MH a (48 en total) de nuestras luces deportivas de rendimiento LED FL9M -630W.",
          "results": "<strong>30</strong> fc iluminancia media, <strong>uniformidad 1.37 : 1</strong> — excediendo los requisitos del proyecto."
        },
        "de": {
          "title": "Bohemia Manor Gymnasium",
          "location": "Vereinigte Staaten von Amerika",
          "description": "【Kundenprofil】\nDie Bohemia Manor High School ist eine öffentliche Schule, die von Cecil County Public Schools betrieben wird und etwa eine Meile südlich der kleinen Stadt Chesapeake City in Cecil County, MD, liegt. Dies ist eine kleine Schule mit 685 Schülern, die ihren Campus mit der Bohemia Manor Middle School teilt. Die\nschule ist auch unter dem Spitznamen „Bo Manor“ bekannt.\n\n【Arbeitsumfang】\nDie ursprüngliche Beleuchtung im Feld \"Bo Manor\" war ineffizient, unterleuchtet und musste mühsam gewartet werden. Außerdem erforderten die Spezifikationen des Projekts die Nutzung der vorhandenen Pole und Strukturen.\n\n【Die Lösung】\nEin präzises photometrisches Design wurde fertiggestellt, um sicherzustellen, dass die Konstruktionsspezifikationen eingehalten wurden. Das Design sah den Austausch (insgesamt 40) der vorhandenen 1500-W-MH-Leuchten an (insgesamt 48) unserer FL9M-630-W-LED-Leistungssportleuchten vor.",
          "results": "<strong>30fc</strong> mittlere Beleuchtungsstärke, <strong>Gleichmäßigkeit 1,37 : 1</strong> — die Projektanforderungen übertreffend."
        },
        "ru": {
          "title": "Средняя школа Bohemia Manor",
          "location": "Соединенные Штаты Америки",
          "description": "Профиль 【клиента】\nСредняя школа Bohemia Manor - это государственная школа, управляемая государственными школами округа Сесил, расположенная примерно в одной миле к югу от небольшого городка Чесапик-Сити в округе Сесил, штат Мэриленд. Это небольшая школа на 685 учеников, которая делит свой кампус со средней школой Bohemia Manor.\nшкола также известна под прозвищем «Усадьба Бо».\n\n【Объем работ】\nПервоначальное освещение на месторождении «Усадьба Бо» было неэффективным, недостаточно освещенным и требовало хлопот в обслуживании. Также спецификации проекта требовали использования существующих опор и конструкций.\n\n【Решение】\nДля обеспечения соответствия проектным спецификациям была завершена точная фотометрическая конструкция. Дизайн предусматривал замену (всего 40) существующих светильников 1500 Вт MH на (всего 48) наших светодиодных спортивных светильников FL9M -630W.",
          "results": "<strong>30fc</strong> средняя освещенность, <strong>равномерность 1,37 : 1</strong> — превышение проектных требований."
        },
        "ar": {
          "title": "مدرسة بوهيميا مانور الثانوية",
          "location": "الولايات المتحدة الأمريكية",
          "description": "الملف الشخصي 【للعميل】\nمدرسة بوهيميا مانور الثانوية هي مدرسة عامة تديرها مدارس مقاطعة سيسيل العامة وتقع على بعد ميل واحد تقريبًا جنوب مدينة تشيسابيك الصغيرة في مقاطعة سيسيل بولاية ماريلاند. هذه مدرسة صغيرة تضم 685 طالبًا تشترك في حرمها الجامعي مع مدرسة بوهيميا مانور المتوسطة.\nتُعرف المدرسة أيضًا باسم \"بو مانور\".\n\n【نطاق العمل】\nكانت الإضاءة الأصلية في حقل \"بو مانور\" غير فعالة، وتحت الإضاءة، ومتعبة في الصيانة. كما تطلبت مواصفات المشروع استخدام الأعمدة والهياكل القائمة.\n\n【الحل】\nتم الانتهاء من تصميم فوتومتري دقيق لضمان تلبية مواصفات التصميم. دعا التصميم إلى استبدال (إجمالي 40) من تركيبات الإضاءة MH الحالية بقدرة 1500 واط إلى (إجمالي 48) من مصابيح LED الرياضية ذات الأداء FL9M -630W.",
          "results": "<strong>30fc</strong> متوسط الإضاءة، <strong>التوحيد 1.37 : 1</strong> — تجاوز متطلبات المشروع."
        }
      },
      "gallery": [
        "images/projects/gallery/bmhs-football-field-01.webp",
        "images/projects/gallery/bmhs-football-field-02.webp",
        "images/projects/gallery/bmhs-football-field-03.webp",
        "images/projects/gallery/bmhs-football-field-04.webp",
        "images/projects/gallery/bmhs-football-field-05.webp"
      ],
      "pdf_url": "projects/pdfs/football-field-led-retrofit/Bohemia_Manor_High_School_Case_Study_aIcvbD9.pdf"
    },
    {
      "pk": 4,
      "title": "Yuanshen Sports Centre Stadium",
      "location": "Shanghai, China",
      "slug": "yuanshen-sports-centre-stadium",
      "venue_type": "OUTDOOR",
      "sport_type": "SOCCER_FIELD",
      "description": "【Customer Profile】\r\nShangHai Yuanshen Sports Centre Stadium is a multipurpose stadium and competition venue in Shanghai's Pudong New Area. With a total area of 160,000 square meters.this venue can accommodate 20,000 spectators at the same time, It was once the home stadium of Shanghai Shenxin Football Club,it will become the new home of Shanghai SIPG Football Club(2021—)\r\n\r\n【Scope of Work】\r\nLighting standards for competitive tournament play were a must. As a result: Average lux: 2200lux ,U0=0.8 ,Ra>80 met the AFC stadium Lighting Guidelines 2018. During to the excellent light system solution the budgetary and performance expectations were able to be met.\r\n\r\n【The Solution】\r\nFL12M1000W High Performance Series LED sports lights CCT:5000-5500K With 320pcs ,were installed.\r\nAlso, a networking control system was incorporated to allow for remote on/off control and power monitoring.",
      "results": "<strong>2200 lux avg.</strong>, <strong>U0=0.8</strong>, <strong>Ra&gt;80</strong> — meeting AFC Stadium Lighting Guidelines 2018.",
      "image": "images/processed/soccerfield.webp",
      "order": 2,
      "translations": {
        "fr": {
          "title": "Stade du Centre Sportif Yuanshen",
          "location": "Shanghai, Chine",
          "description": "Un stade polyvalent à Shanghai Pudong avec 160 000 m² et 20 000 places. 320 projecteurs LED FL12M-1000W (TCP: 5000-5500K) avec système de contrôle réseau pour la commande à distance et le monitoring de puissance.",
          "results": "2200 lux moy., U0=0.8, Ra>80 — répondant aux directives AFC Stadium Lighting 2018."
        },
        "es": {
          "title": "Estadio del Centro Deportivo Yuanshen",
          "location": "Shanghai, China",
          "description": "Un estadio polideportivo en Shanghai Pudong con 160,000 m² y 20,000 asientos. 320 luminarias LED FL12M-1000W (TCP: 5000-5500K) con sistema de control en red para encendido/apagado remoto y monitoreo.",
          "results": "2200 lux prom., U0=0.8, Ra>80 — cumpliendo las Directrices de Iluminación de Estadios AFC 2018."
        },
        "de": {
          "title": "Yuanshen Sportzentrum Stadion",
          "location": "Shanghai, China",
          "description": "Ein Mehrzweckstadion in Shanghai Pudong mit 160.000 m² und 20.000 Sitzplätzen. 320 LED-Sportfluter FL12M-1000W (TDF: 5000-5500K) mit Netzwerk-Steuerungssystem.",
          "results": "2200 Lux Durchschnitt, U0=0.8, Ra>80 — erfüllt AFC-Stadionbeleuchtungsrichtlinien 2018."
        },
        "ru": {
          "title": "Стадион Спортивного центра Юаньшэнь",
          "location": "Шанхай, Китай",
          "description": "Многоцелевой стадион в районе Пудун, Шанхай, площадью 160 000 м² на 20 000 мест. 320 спортивных LED-прожекторов FL12M-1000W (ЦТТ: 5000-5500К) с сетевой системой управления.",
          "results": "Средняя 2200 люкс, U0=0.8, Ra>80 — соответствие руководящим принципам AFC по освещению стадионов 2018."
        },
        "ar": {
          "title": "ملعب مركز يوانشين الرياضي",
          "location": "شنغهاي، الصين",
          "description": "ملعب متعدد الأغراض في شنغهاي بودونغ بمساحة 160,000 م² و20,000 مقعد. 320 مصباح LED رياضي FL12M-1000W مع نظام تحكم شبكي.",
          "results": "متوسط 2200 لوكس، U0=0.8، Ra>80 — تلبي إرشادات AFC لإضاءة الملاعب 2018."
        }
      },
      "gallery": [
        "images/projects/gallery/shys-soccer-01.webp",
        "images/projects/gallery/shys-soccer-02.webp",
        "images/projects/gallery/shys-soccer-03.webp",
        "images/projects/gallery/shys-soccer-04.webp",
        "images/projects/gallery/shys-soccer-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 2,
      "title": "Carroll County Sports Complex",
      "location": "United States",
      "slug": "baseball-field-led-retrofit",
      "venue_type": "OUTDOOR",
      "sport_type": "BASEBALL_FIELD",
      "description": "150 FL9M-630W Performance Series LED sports lights with remote mount drivers were installed. A networking control system was incorporated to allow for remote on/off control and power monitoring.",
      "results": "<strong>50/30fc</strong> average illuminance, <strong>uniformity 2.0:1 / 2.5:1</strong> — meeting the project specifications.",
      "image": "images/processed/Baseball.webp",
      "order": 3,
      "translations": {
        "fr": {
          "title": "Rénovation LED Terrain de Baseball",
          "location": "États-Unis",
          "description": "150 projecteurs LED sportifs FL9M-630W de la série Performance avec drivers à montage distant ont été installés. Un système de contrôle réseau a été intégré pour permettre le contrôle à distance marche/arrêt et la surveillance de puissance.",
          "results": "50/30fc éclairage moyen, uniformité 2.0:1 / 2.5:1 — respectant les spécifications du projet."
        },
        "es": {
          "title": "Renovación LED Campo de Béisbol",
          "location": "Estados Unidos",
          "description": "Se instalaron 150 luminarias LED deportivas FL9M-630W de la serie Performance con controladores de montaje remoto. Se incorporó un sistema de control en red para permitir encendido/apagado remoto y monitoreo de potencia.",
          "results": "50/30fc iluminación promedio, uniformidad 2.0:1 / 2.5:1 — cumpliendo las especificaciones del proyecto."
        },
        "de": {
          "title": "LED-Umrüstung Baseballfeld",
          "location": "Vereinigte Staaten",
          "description": "150 LED-Sportfluter FL9M-630W der Performance-Serie mit Fernmontage-Treibern wurden installiert. Ein Netzwerk-Steuerungssystem wurde integriert für ferngesteuerte Ein/Aus-Steuerung und Leistungsüberwachung.",
          "results": "50/30fc durchschnittliche Beleuchtung, Gleichmäßigkeit 2.0:1 / 2.5:1 — erfüllt die Projektspezifikationen."
        },
        "ru": {
          "title": "Модернизация LED бейбольного поля",
          "location": "Соединённые Штаты",
          "description": "Установлены 150 спортивных LED-прожекторов FL9M-630W серии Performance с удалёнными драйверами. Интегрирована сетевая система управления для дистанционного включения/выключения и мониторинга мощности.",
          "results": "Средняя освещённость 50/30фк, равномерность 2.0:1 / 2.5:1 — соответствие проектным спецификациям."
        },
        "ar": {
          "title": "ترقية LED لملاعب البيسبول",
          "location": "الولايات المتحدة",
          "description": "تم تركيب 150 مصابيح LED رياضية FL9M-630W من سلسلة الأداء مع محركات تحكم عن بعد. تم دمج نظام تحكم شبكي للسماح بالتشغيل/الإيقاف عن بعد ومراقبة الطاقة.",
          "results": "متوسط إضاءة 50/30fc، uniformity 2.0:1 / 2.5:1 — تلبي مواصفات المشروع."
        }
      },
      "gallery": [
        "images/projects/gallery/CCSC-Baseball-01.webp",
        "images/projects/gallery/CCSC-Baseball-02.webp",
        "images/projects/gallery/CCSC-Baseball-03.webp",
        "images/projects/gallery/CCSC-Baseball-04.webp",
        "images/projects/gallery/CCSC-Baseball-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 6,
      "title": "Morgan State University Tennis Courts",
      "location": "United States",
      "slug": "morgan-state-university-tennis-courts",
      "venue_type": "OUTDOOR",
      "sport_type": "TENNIS_COURTS",
      "description": "【Customer Profile】\r\nMorgan State University is the premier public urban\r\nresearch university in Maryland, known for its excellence in\r\nteaching, intensive research, effective public service and\r\ncommunity engagement. Morgan prepares diverse and\r\ncompetitive graduates for success in a global,\r\ninterdependent society.",
      "results": "",
      "image": "images/processed/msu-tennis-01.webp",
      "order": 4,
      "translations": {},
      "gallery": [
        "images/projects/gallery/msu-tennis-01.webp",
        "images/projects/gallery/msu-tennis-02.webp",
        "images/projects/gallery/msu-tennis-03.webp",
        "images/projects/gallery/msu-tennis-04.webp",
        "images/projects/gallery/msu-tennis-05.webp"
      ],
      "pdf_url": "projects/pdfs/morgan-state-university-tennis-courts/Morgan_state___university__tennis_case_study.pdf"
    },
    {
      "pk": 3,
      "title": "Multi-Sport Arena HD Broadcast",
      "location": "France",
      "slug": "multi-sport-arena-hd-broadcast",
      "venue_type": "INDOOR",
      "sport_type": "MULTI_SPORT",
      "description": "A multipurpose venue in France designed for HD television broadcast, convertible between basketball and tennis configurations. FL9M-630W LED sports lights fully satisfy the lighting requirements for both court types.",
      "results": "<strong>&gt;2000 lux</strong> — meeting HD broadcast standards.",
      "image": "images/processed/basketball.webp",
      "order": 5,
      "translations": {
        "fr": {
          "title": "Arène Multisport HD Broadcast",
          "location": "France",
          "description": "Un lieu polyvalent en France conçu pour la télévision HD, convertible entre configurations basket et tennis. Les projecteurs LED FL9M-630W satisfont pleinement les exigences d’éclairage pour le basket et le tennis.",
          "results": ">2000 lux — répondant aux normes de diffusion HD."
        },
        "es": {
          "title": "Arena Multideporte HD Broadcast",
          "location": "Francia",
          "description": "Un recinto polideportivo en Francia diseñado para televisión HD, convertible entre configuraciones de baloncesto y tenis. Las luminarias LED FL9M-630W satisfacen plenamente los requisitos de iluminación.",
          "results": ">2000 lux — cumpliendo los estándares de transmisión HD."
        },
        "de": {
          "title": "Mehrzweck-HD-Broadcast-Arena",
          "location": "Frankreich",
          "description": "Eine Mehrzweckhalle in Frankreich für HD-Fernsehen, umschaltbar zwischen Basketball- und Tennis-Konfiguration. FL9M-630W LED-Sportfluter erfüllen vollumfänglich die Beleuchtungsanforderungen.",
          "results": ">2000 Lux — erfüllt HD-Broadcast-Standards."
        },
        "ru": {
          "title": "Многоспортивная арена HD-вещания",
          "location": "Франция",
          "description": "Многоцелевой комплекс во Франции, спроектированный для HD-телевидения, преобразуемый между баскетбольными и теннисными конфигурациями. LED-прожекторы FL9M-630W полностью удовлетворяют требованиям освещения.",
          "results": ">2000 люкс — соответствие стандартам HD-вещания."
        },
        "ar": {
          "title": "صالة رياضية متعددة الألعاب بث HD",
          "location": "فرنسا",
          "description": "مرفق متعدد الأغراض في فرنسا مصمم للتلفزيون عالي الدقة، قابل للتحويل بين إعدادات كرة السلة والتنس. مصابيح LED FL9M-630W تلبي بالكامل متطلبات الإضاءة.",
          "results": ">2000 لوكس — تلبي معايير البث عالي الدقة."
        }
      },
      "gallery": [
        "images/projects/gallery/choecm-basketball-01.webp",
        "images/projects/gallery/choecm-basketball-02.webp",
        "images/projects/gallery/choecm-basketball-03.webp",
        "images/projects/gallery/choecm-basketball-04.webp",
        "images/projects/gallery/choecm-basketball-05.webp",
        "images/projects/gallery/choecm-tennis-01.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 5,
      "title": "Narbonne Arena",
      "location": "France",
      "slug": "narbonne-arena",
      "venue_type": "INDOOR",
      "sport_type": "MULTI_SPORT",
      "description": "When the performers return, Narbonne Arena will be ready for them with a new GEO S12 line array system, installed by Texen. \r\nNarbonne Arena is the new cultural, sporting and event scene in Aude, in the south of France. Fully modular, it can accommodate up to 5000 people in its main space, and will host touring shows, concerts, symposia, meetings, conventions and sporting events. This new venue opened at the end of 2019, and its modern design includes good acoustics, says NEXO system specialist Carole Marsaud, who shares her NS-1 plots here.\r\nThere are 10 loudspeaker clusters around the venue, variously with 3x S12 and 4x S12 modules, with two larger arrays of 6x GEO S12 modules facing the main grandstand side. The system is powered by 3x NXAMP4x4s, equipped with Dante cards.",
      "results": "",
      "image": "images/processed/Narbonne-basketball-04.webp",
      "order": 6,
      "translations": {},
      "gallery": [
        "images/projects/gallery/Narbonne-basketball-01.webp",
        "images/projects/gallery/Narbonne-basketball-02.webp",
        "images/projects/gallery/Narbonne-basketball-03.webp",
        "images/projects/gallery/Narbonne-basketball-04.webp",
        "images/projects/gallery/Narbonne-basketball-05.webp"
      ],
      "pdf_url": ""
    }
  ],
  "siteconfig": {
    "hero_title": "The Next Generation Lighting Systems For Every Area",
    "hero_subtitle": "Professional SolarOne sports lighting solutions trusted in over 50 countries. From community fields to broadcast-ready stadiums, engineered for performance, built to outlast.",
    "hero_background": "",
    "stat_projects": "500+",
    "stat_projects_label": "Projects",
    "stat_countries": "50+",
    "stat_countries_label": "Countries",
    "stat_energy": "50%+",
    "stat_energy_label": "Energy Save",
    "stat_support": "5+",
    "stat_support_label": "warranty",
    "about_title": "Trusted worldwide for a reason.",
    "about_text_1": "Since 2007, SolarOne Vision has focused on the design and manufacture of high power LED Sports lighting systems, LED Roadway infrastructure lighting systems, and LED industrial lighting systems. We bring first-hand knowledge and experience for new and retrofit projects — from small projects requiring a few lights to professional high-level facilities, we've got you covered.",
    "about_text_2": "SolarOne's mission is to deliver innovative outdoor and indoor lighting solutions for recreational, high school, college, and semi-professional sports venues, airports, seaports, and other industrial facilities. We protect the environment, reduce energy consumption, deliver satisfying and inspiring lighting experiences, and add value to people's vision of life.",
    "about_stat_years": "18+",
    "about_stat_years_label": "Years Experience",
    "about_stat_projects": "500+",
    "about_stat_projects_label": "Projects Delivered",
    "about_stat_countries": "50+",
    "about_stat_countries_label": "Countries Served",
    "about_stat_clients": "1000+",
    "about_stat_clients_label": "Happy Clients",
    "products_title": "Our Products",
    "products_subtitle": "From compact modular luminaires to stadium-grade high bay systems. Precision optics, modular architecture, and field-proven reliability across every product line.",
    "projects_title": "Featured Projects",
    "projects_subtitle": "Real installations across five continents. From Olympic training centers to community football pitches, our luminaires deliver reliable performance under the toughest conditions.",
    "contact_title": "Get in Touch",
    "contact_subtitle": "Have a project in mind? Send us the details and our engineering team will respond with a full photometric proposal within 48 hours.",
    "contact_email": "sales@solaronelighting.com",
    "contact_phone_1": "+8613910887405",
    "contact_phone_2": "+8613910887405",
    "contact_whatsapp": "+86 13910887405",
    "contact_address": "Beijing, China",
    "social_facebook": "https://facebook.com",
    "social_instagram": "https://instagram.com",
    "social_youtube": "https://youtube.com",
    "social_tiktok": "https://tiktok.com",
    "social_linkedin": "",
    "footer_description": "Professional LED lighting systems for sports, industrial, and infrastructure applications. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.",
    "brand_name": "SolarOne",
    "logo": "",
    "meta_title": "SolarOne — Precision LED Lighting Systems",
    "meta_description": "Professional LED sports lighting, high bay, and modular luminaire solutions. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.",
    "og_image": "",
    "font_family_body": "'Inter', 'Helvetica Neue', Arial, sans-serif",
    "font_family_heading": "'Inter', 'Helvetica Neue', Arial, sans-serif",
    "font_size_base": "16px",
    "font_size_nav": "17px",
    "font_size_hero_title": "3.5rem",
    "font_size_hero_subtitle": "1.15rem",
    "font_size_section_title": "2.25rem",
    "font_size_body": "1.05rem",
    "font_size_card_title": "1.25rem",
    "font_size_card_desc": "0.95rem",
    "accent_color": "#0088FF"
  }
}
