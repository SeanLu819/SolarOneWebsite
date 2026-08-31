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
      "ordering_image": "images/products/m-series/sample-number.webp",
      "cert_image": "",
      "order": 1,
      "is_active": True,
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
        "images/products/m-series/m-series-05.webp"
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
      "model_number": "",
      "ordering_info": []
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
      "dimension_image": "images/products/rt410-series/rt410-3d-view.webp",
      "beam_angle_image": "images/products/rt410-series/beamangle183050100.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 2,
      "is_active": True,
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT410FL-260W-XXK-S"
        },
        {
          "label": "Lumen Output",
          "value": ">31,200lm"
        },
        {
          "label": "System Wattage",
          "value": "260W"
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
          "value": "1.4(sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "15.8\" X 15.8\"X 4.2\" / 418 X 400 X 172 (mm)"
        },
        {
          "label": "Approximate Weight",
          "value": "(30lbs)13.5kgs"
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
      "model_number": "RT410FL-260W-XXK-S",
      "ordering_info": [
        "RT410FL",
        "260W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "30=30°\r\n50=50°\r\n100=100°\r\n8040=80°X 40°\r\n11060=110°X 60°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
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
      "image": "images/products/fl1m/fl1m-01.webp",
      "banner_image": "images/products/fl1m/fl1m-bar-1.webp",
      "dimension_image": "images/products/fl1m/fl1m-3d-view.webp",
      "beam_angle_image": "images/products/fl1m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 11,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl1m/fl1m-01.webp",
        "images/products/fl1m/fl1m-02.webp",
        "images/products/fl1m/fl1m-03.webp",
        "images/products/fl1m/fl1m-04.webp"
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL1M-80W"
        },
        {
          "label": "Lumen Output",
          "value": "10400 lm"
        },
        {
          "label": "System Wattage",
          "value": "80w"
        },
        {
          "label": "CRI",
          "value": ">80"
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
          "value": "0.26 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "8.6\" X 9.2\"X 5.4\"/218*235*137mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 5.2 lbs)2.3 kgs"
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
      "model_number": "FL1M-80W-30K-S",
      "ordering_info": [
        "FL1M (Light With 1 Module)",
        "80W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
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
      "image": "images/products/fl4m/fl4m-01.webp",
      "banner_image": "images/products/fl4m/fl4m-bar-1.webp",
      "dimension_image": "images/products/fl4m/fl4m-3d-view.webp",
      "beam_angle_image": "images/products/fl4m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 12,
      "is_active": True,
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
        "images/products/fl4m/fl4m-01.webp",
        "images/products/fl4m/fl4m-02.webp",
        "images/products/fl4m/fl4m-03.webp",
        "images/products/fl4m/fl4m-04.webp"
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
          "value": "( 24.5 lbs) 11.0 kgs"
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
      "model_number": "FL4M-320W-30K-S",
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
      ]
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
      "image": "images/products/fl6m/fl6m-01.webp",
      "banner_image": "images/products/fl6m/fl6m-bar-1.webp",
      "dimension_image": "images/products/fl6m/fl6m-3d-view.webp",
      "beam_angle_image": "images/products/fl6m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 13,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl6m/fl6m-01.webp",
        "images/products/fl6m/fl6m-02.webp",
        "images/products/fl6m/fl6m-03.webp",
        "images/products/fl6m/fl6m-04.webp"
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL6M-480W"
        },
        {
          "label": "Lumen Output",
          "value": ">58700lm"
        },
        {
          "label": "System Wattage",
          "value": "480W"
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
          "value": "1.58 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "21.8\" X 14.5\"X 8.1\"/553*368*343mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 37 lbs) 16.8 kgs"
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
      "model_number": "FL6M-480W-30K-S",
      "ordering_info": [
        "FL6M (Light With 6 Module)",
        "480W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
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
      "image": "images/products/fl9m/fl9m-01.webp",
      "banner_image": "images/products/fl9m/fl9m-bar-1.webp",
      "dimension_image": "images/products/fl9m/fl9m-3d-view.webp",
      "beam_angle_image": "images/products/fl9m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 14,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl9m/fl9m-01.webp",
        "images/products/fl9m/fl9m-02.webp",
        "images/products/fl9m/fl9m-03.webp",
        "images/products/fl9m/fl9m-04.webp"
      ],
      "specs": [
        {
          "label": "Power",
          "value": "720W"
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL9M-720W"
        },
        {
          "label": "Lumen Output",
          "value": ">87,600lm"
        },
        {
          "label": "System Wattage",
          "value": "720W"
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
          "value": "2.37 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "21.8\" X 21.8\"X 8.1\"/553*553*343mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 58lbs)26.0 kgs"
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
      "model_number": "FL9M-720W-XXK-S",
      "ordering_info": [
        "FL9M (Light With 9 Module)",
        "720W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
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
      "image": "images/products/fl12m/fl12m-01.webp",
      "banner_image": "images/products/fl12m/fl12m-bar-1.webp",
      "dimension_image": "images/products/fl12m/fl12m-3d-view.webp",
      "beam_angle_image": "images/products/fl12m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 15,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl12m/fl12m-01.webp",
        "images/products/fl12m/fl12m-02.webp",
        "images/products/fl12m/fl12m-03.webp",
        "images/products/fl12m/fl12m-04.webp"
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL12M-1000W"
        },
        {
          "label": "Lumen Output",
          "value": ">123,000 lm"
        },
        {
          "label": "System Wattage",
          "value": "1000W"
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
          "value": "3.16 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "21.8\" X 29.1\"X 8.1\"/553*737.90*343mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 59lbs)33.0 kgs"
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
      "model_number": "FL12M-1000W-YYK-H-30",
      "ordering_info": [
        "FL12M (Light With 12 Module)",
        "1000W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
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
      "image": "images/products/fl16m/fl16m-01.webp",
      "banner_image": "images/products/fl16m/fl16m-bar-01.webp",
      "dimension_image": "images/products/fl16m/fl16m-3d-view.webp",
      "beam_angle_image": "images/products/fl16m/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 16,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl16m/fl16m-01.webp",
        "images/products/fl16m/fl16m-02.webp",
        "images/products/fl16m/fl16m-03.webp",
        "images/products/fl16m/fl16m-04.webp"
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL16M-1360W"
        },
        {
          "label": "Lumen Output",
          "value": ">163,000 lm"
        },
        {
          "label": "System Wattage",
          "value": "1360W"
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
          "value": "4.16 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "29\" X 29 \"X 8.1\"/738*738*343mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 94.5lbs)42.5 kgs"
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
      "model_number": "FL12M-1360W-30K-H",
      "ordering_info": [
        "FL16M (Light With 16 Module)",
        "1360W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
    },
    {
      "pk": 23,
      "name": "FL9M-RGBW",
      "slug": "fl9m-rgbw",
      "category": "AREA_SITE",
      "description": "Any Color from anywhere, anytime, at your convenience! FL9M-RGBW-600W, We offer M-series RGB and RGBW lighting fixtures. The white light color temperature can be customized to your requirements, ranging from 3000K to 5700K.",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/fl9m-rgbw/rgbw-9m-w.webp",
      "banner_image": "images/products/fl9m-rgbw/rgbw-bar-01.webp",
      "dimension_image": "images/products/fl9m-rgbw/fl9m-3d-view.webp",
      "beam_angle_image": "images/products/fl9m-rgbw/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "images/products/fl9m-rgbw/cert-3.webp",
      "order": 17,
      "is_active": True,
      "parent_slug": "m-series",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/fl9m-rgbw/rgbw-9m-r.webp",
        "images/products/fl9m-rgbw/rgbw-9m-g.webp",
        "images/products/fl9m-rgbw/rgbw-9m-b.webp",
        "images/products/fl9m-rgbw/rgbw-9m-w.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "FL9M-RGBW"
        },
        {
          "label": "System Wattage",
          "value": "600W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "value": "2.37 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "21.8\" x 21.8\" x 8.1\" / 553 x 553 x 343 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "26.0 kgs( 58.0 lbs)"
        },
        {
          "label": "Material",
          "value": "Aluminum / Glass"
        },
        {
          "label": "LED Driver",
          "value": "Inventronics Or Equal"
        }
      ],
      "model_number": "FL9M-RGBW",
      "ordering_info": [
        "FL9M-RGBW",
        "600W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.DMX\r\n2.DALI",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "W = With Fixture\r\nS = Separated from Fixture"
      ]
    },
    {
      "pk": 22,
      "name": "Glare Shield for RT410",
      "slug": "glare-shield-for-rt410",
      "category": "ACCESSORY",
      "description": "Glare Shield for RT410",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/glare-shield-for-rt410/rt410-glare-shield-01.webp",
      "banner_image": "",
      "dimension_image": "",
      "beam_angle_image": "",
      "ordering_image": "",
      "cert_image": "",
      "order": 19,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/glare-shield-for-rt410/rt410-glare-shield-01.webp",
        "images/products/glare-shield-for-rt410/rt410-glare-shield-02.webp",
        "images/products/glare-shield-for-rt410/rt410-glare-shield-03.webp",
        "images/products/glare-shield-for-rt410/rt410-glare-shield-04.webp"
      ],
      "specs": [],
      "energy_data": [],
      "model_number": "",
      "ordering_info": []
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
      "image": "images/products/vsp-xxxxw-9m-yp/VSP9M-01.webp",
      "banner_image": "images/products/vsp-xxxxw-9m-yp/vsp-bar-3.webp",
      "dimension_image": "images/products/vsp-xxxxw-9m-yp/ac-en-3d-view.webp",
      "beam_angle_image": "images/products/vsp-xxxxw-9m-yp/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 21,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {
          "category": "Système d'Éclairage Sportif",
          "description": "Système de protection anti-stroboscope pour sites de diffusion. Élimine le scintillement des ralentis grâce à une technologie de commande haute fréquence stable.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "es": {
          "category": "Sistema de Iluminación Deportiva",
          "description": "Sistema de protección contra parpadeo de visión para recintos de broadcast. Elimina el parpadeo en reproducciones a cámara lenta con tecnología de accionamiento de alta frecuencia estable.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "de": {
          "category": "Sportbeleuchtungssystem",
          "description": "Vision Strobe Protection-System für Broadcast-Veranstaltungsorte. Beseitigt Flackern bei Zeitlupenwiedergaben durch stabile Hochfrequenz-Antriebstechnologie.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "ru": {
          "category": "Система спортивного освещения",
          "description": "Система защиты от стробоскопического эффекта для телевизионных объектов. Устраняет мерцание при замедленной съемке за счет стабильной высокочастотной технологии питания.",
          "name": "VSP-XXXXW-9M-YP"
        },
        "ar": {
          "category": "نظام إضاءة رياضية",
          "description": "نظام حماية ضد الوامض للمنشآت الإذاعية. يقضي على الوميض في إعادة العرض البطيئة بتقنية تشغيل عالية التردد ومستقرة.",
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "VSP-XXXXW-9M-YP (AC Enclosure))"
        },
        {
          "label": "System Wattage",
          "value": "4200W"
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
          "label": "L\" × W\" × H\"",
          "value": "15.7\" x 14.0\" x 23.6\" / 400 x 355 x 600 mm"
        },
        {
          "label": "Material",
          "value": "Stainless Steel 304"
        },
        {
          "label": "LED Driver",
          "value": "Inventronics Or Equal"
        }
      ],
      "model_number": "VSP-4200W-9M-YP",
      "ordering_info": [
        "VSP-4200W-9M-YP",
        "4200W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "S = Separated from Fixture"
      ]
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
      "image": "images/products/vsp-xxxxw-12m-yp/vsp12m-01.webp",
      "banner_image": "images/products/vsp-xxxxw-12m-yp/vsp-bar-1.webp",
      "dimension_image": "images/products/vsp-xxxxw-12m-yp/led-en-3d-view.webp",
      "beam_angle_image": "images/products/vsp-xxxxw-12m-yp/beamangle-12183050.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 22,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {
          "category": "Système d'Éclairage Sportif",
          "description": "Système de protection anti-stroboscope pour sites de diffusion. Élimine le scintillement des ralentis grâce à une technologie de commande haute fréquence stable.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "es": {
          "category": "Sistema de Iluminación Deportiva",
          "description": "Sistema de protección contra parpadeo de visión para recintos de broadcast. Elimina el parpadeo en reproducciones a cámara lenta con tecnología de accionamiento de alta frecuencia estable.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "de": {
          "category": "Sportbeleuchtungssystem",
          "description": "Vision Strobe Protection-System für Broadcast-Veranstaltungsorte. Beseitigt Flackern bei Zeitlupenwiedergaben durch stabile Hochfrequenz-Antriebstechnologie.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "ru": {
          "category": "Система спортивного освещения",
          "description": "Система защиты от стробоскопического эффекта для телевизионных объектов. Устраняет мерцание при замедленной съемке за счет стабильной высокочастотной технологии питания.",
          "name": "VSP-XXXXW-12M-YP"
        },
        "ar": {
          "category": "نظام إضاءة رياضية",
          "description": "نظام حماية ضد الوامض للمنشآت الإذاعية. يقضي على الوميض في إعادة العرض البطيئة بتقنية تشغيل عالية التردد ومستقرة.",
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
      "energy_data": [
        {
          "label": "Series Name",
          "value": "VSP-XXXXW-12M-YP (LED Driver Enclosure)"
        },
        {
          "label": "System Wattage",
          "value": "4200W"
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
          "label": "L\" × W\" × H\"",
          "value": "15.7\" x 14.0\" x 39.4\" / 400 x 355 x 1000 mm"
        },
        {
          "label": "Material",
          "value": "Stainless Steel 304"
        },
        {
          "label": "LED Driver",
          "value": "Inventronics Or Equal"
        }
      ],
      "model_number": "VSP-4200W-12M-YP",
      "ordering_info": [
        "VSP-4200W-12M-YP",
        "4200W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "12=12°\r\n18=18°\r\n30=30°\r\n50=50°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket\r\nL = Sitting Mount Bracket",
        "S = Separated from Fixture"
      ]
    },
    {
      "pk": 20,
      "name": "RT590FL-S",
      "slug": "rt590fl-s",
      "category": "FLOODLIGHT",
      "description": "RT590FL-S",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt590fl-s/rt590fl-s-01.webp",
      "banner_image": "images/products/rt590fl-s/rt590-bar-02.webp",
      "dimension_image": "images/products/rt590fl-s/tr590-3d-view.webp",
      "beam_angle_image": "images/products/rt590fl-s/beamangle-3050120.webp",
      "ordering_image": "",
      "cert_image": "images/products/rt590fl-s/cert-3.webp",
      "order": 31,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt590fl-s/rt590fl-s-01.webp",
        "images/products/rt590fl-s/rt590fl-s-02.webp",
        "images/products/rt590fl-s/rt590fl-s-03.webp",
        "images/products/rt590fl-s/rt590fl-s-04.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT590FL-160W"
        },
        {
          "label": "Lumen Output",
          "value": ">20,800 lm"
        },
        {
          "label": "System Wattage",
          "value": "160W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "value": "0.26 (sq. ft.)"
        },
        {
          "label": "L\" × W\" × H\"",
          "value": "23.2\"  x 11.9\" x  9.8\" / 589 x 301 x 248.5mm"
        },
        {
          "label": "Approximate Weight",
          "value": "12.8 kgs( 28.2 lbs)"
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
      "model_number": "RT590FL-160W",
      "ordering_info": [
        "LED Flood Light",
        "160W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "120=120°\r\n30=30°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket"
      ]
    },
    {
      "pk": 16,
      "name": "RT390FL-S",
      "slug": "rt390fl",
      "category": "FLOODLIGHT",
      "description": "RT390FL-S",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt390fl/rt390-01.webp",
      "banner_image": "images/products/rt390fl/rt390-bar-01.webp",
      "dimension_image": "images/products/rt390fl/rt390-3d-view.webp",
      "beam_angle_image": "images/products/rt390fl/beamangle-3050120.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 32,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt390fl/rt390-01.webp",
        "images/products/rt390fl/rt390-02.webp",
        "images/products/rt390fl/rt390-03.webp",
        "images/products/rt390fl/rt390-04.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT390FL-S"
        },
        {
          "label": "Lumen Output",
          "value": ">10,400lm"
        },
        {
          "label": "System Wattage",
          "value": "80W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "369 x 294 x 336 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "(18.7 lbs) 8.5 kgs"
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
      "model_number": "RT390FL-80W",
      "ordering_info": [
        "RT390FL",
        "80W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "120=120°\r\n30=30°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket"
      ]
    },
    {
      "pk": 17,
      "name": "RT400HB",
      "slug": "rt400hb",
      "category": "HIGHBAY_LOWBAY",
      "description": "Typical Applications\r\nHigh school, college , professional stadiums, Large area, Industrial Facilities, Building facades",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt400hb/rt400hb-01.webp",
      "banner_image": "images/products/rt400hb/rt400hb-barnner-01.webp",
      "dimension_image": "images/products/rt400hb/rt400hb-3d-view01.webp",
      "beam_angle_image": "images/products/rt400hb/rt400hb-beamangle-254590.png",
      "ordering_image": "",
      "cert_image": "",
      "order": 42,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt400hb/rt400hb-01.webp",
        "images/products/rt400hb/rt400hb-02.webp",
        "images/products/rt400hb/rt400hb-03.webp",
        "images/products/rt400hb/rt400hb-04.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT400HB-130W"
        },
        {
          "label": "Lumen Output",
          "value": ">16,900 lm"
        },
        {
          "label": "System Wattage",
          "value": "130W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "15.6\" x 15.6\" x 15.8\" / 395 x 395 x 401 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "8.0 kgs( 17.6 lbs)"
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
      "model_number": "RT400HB-130W",
      "ordering_info": [
        "HB=HighBay Light",
        "130W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)",
        "25=25°\r\n45=45°\r\n90=90°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V",
        "U = Hang Mount Bracket"
      ]
    },
    {
      "pk": 18,
      "name": "RT500HB",
      "slug": "rt500hb",
      "category": "HIGHBAY_LOWBAY",
      "description": "Typical Applications\r\nHigh school, college, professional stadiums, Large area, Industrial Facilities, Building facades .",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt500hb/hb500-04.webp",
      "banner_image": "images/products/rt500hb/rt500hb-barnner-01.webp",
      "dimension_image": "images/products/rt500hb/rt500hb-3d-view.webp",
      "beam_angle_image": "images/products/rt500hb/rt500hb-beamangle-254590.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 43,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt500hb/hb500-04.webp",
        "images/products/rt500hb/hb500-02.webp",
        "images/products/rt500hb/hb500-03.webp",
        "images/products/rt500hb/hb500-05.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT500HB-280W"
        },
        {
          "label": "Lumen Output",
          "value": ">36,400 lm"
        },
        {
          "label": "System Wattage",
          "value": "280W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "19.7\" x 19.7\" x 18.0\"/500 x 500 x 457 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "16.0 kgs( 35.3 lbs)"
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
      "model_number": "FL1M-80W",
      "ordering_info": [
        "HB=HighBay Light",
        "280W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "25=25°\r\n45=45°\r\n90=90°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI\r\n4.Zigbee",
        "U = Hang Mount Bracket"
      ]
    },
    {
      "pk": 19,
      "name": "RT220UB",
      "slug": "rt220ub",
      "category": "FLOODLIGHT",
      "description": "Building Security ,Packing lots, residential area, display window, advertisement billboard..etc",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt220ub/rt220ub-01.webp",
      "banner_image": "images/products/rt220ub/rt220ub-banner.webp",
      "dimension_image": "images/products/rt220ub/rt220ub-3d-view.webp",
      "beam_angle_image": "images/products/rt220ub/beamangle-120d-1.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 44,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt220ub/rt220ub-01.webp",
        "images/products/rt220ub/rt220ub-02.webp",
        "images/products/rt220ub/rt220ub-03.webp",
        "images/products/rt220ub/rt220ub-04.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT220UB"
        },
        {
          "label": "Lumen Output",
          "value": ">5,200 lm"
        },
        {
          "label": "System Wattage",
          "value": "40W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "10.1\" x 8.1\" x 5.0\" / 257.5 x 207 x 128 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "2.3 kgs( 5.2 lbs)"
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
      "model_number": "FL1M-80W",
      "ordering_info": [
        "FloodLight",
        "40W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "100=100°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V",
        "U = Hang Mount Bracket"
      ]
    },
    {
      "pk": 21,
      "name": "RT420FS-S",
      "slug": "rt420fs-s",
      "category": "FLOODLIGHT",
      "description": "Typical Applications\r\n Building Security ,Packing lots, residential area, display window, advertisement billboard..etc",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt420fs-s/rt420fl-01.webp",
      "banner_image": "images/products/rt420fs-s/rt420fl-banner-01.webp",
      "dimension_image": "images/products/rt420fs-s/rt420fl-3d-view.webp",
      "beam_angle_image": "images/products/rt420fs-s/beamangle-120d-1.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 45,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt420fs-s/rt420fl-01.webp",
        "images/products/rt420fs-s/rt420fl-02.webp",
        "images/products/rt420fs-s/rt420fl-03.webp",
        "images/products/rt420fs-s/rt420fl-05.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT420FS-S100W"
        },
        {
          "label": "Lumen Output",
          "value": ">13,000 lm"
        },
        {
          "label": "System Wattage",
          "value": "100W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "16.5\" x 15.4\" x 4.9\" / 420 x 390 x 125 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "8.0kgs( 17.6 lbs)"
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
      "model_number": "RT420FS-S100W",
      "ordering_info": [
        "LED Flood Light",
        "100W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "120=120°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. DMX\r\n3. DALI",
        "U = Hang Mount Bracket"
      ]
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
      "banner_image": "images/products/rt600sl-t/rt600sl-t-bar-1.webp",
      "dimension_image": "images/products/rt600sl-t/RT600SL-dimension-1.webp",
      "beam_angle_image": "images/products/rt600sl-t/rt600sl-beamangle70-140.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 51,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt600sl-t/RT600SL-T.webp",
        "images/products/rt600sl-t/rt600sl-03.webp",
        "images/products/rt600sl-t/rt600sl-02.webp",
        "images/products/rt600sl-t/rt600sl-04.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT600SL-T-120W"
        },
        {
          "label": "Lumen Output",
          "value": ">14,400 lm"
        },
        {
          "label": "System Wattage",
          "value": "120W"
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
          "label": "L\" × W\" × H\"",
          "value": "23.5\"  x 13.8\" x  3.9\" / 596 x 350 x 100mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 27.6 lbs) 12.5 kgs"
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
      "model_number": "RT600SL-T",
      "ordering_info": [
        "RT600SL-T",
        "1200W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "70140=70°x 140°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. Photocell \r\n3. PLC\r\n4.Zigbee"
      ]
    },
    {
      "pk": 15,
      "name": "RT820SL-T",
      "slug": "rt820sl-t",
      "category": "ROADWAY",
      "description": "RT820SL-T",
      "power": "",
      "efficacy": "",
      "output": "",
      "beam_angle": "",
      "protection": "",
      "image": "images/products/rt820sl-t/rt820-01.webp",
      "banner_image": "images/products/rt820sl-t/rt820sl-bar-2.webp",
      "dimension_image": "images/products/rt820sl-t/rt820-3d-view.png",
      "beam_angle_image": "images/products/rt820sl-t/rt600sl-beamangle70-140.webp",
      "ordering_image": "",
      "cert_image": "",
      "order": 52,
      "is_active": True,
      "parent_slug": "",
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/products/rt820sl-t/rt820-01.webp",
        "images/products/rt820sl-t/rt820-02.webp",
        "images/products/rt820sl-t/rt820-03.webp"
      ],
      "specs": [],
      "energy_data": [
        {
          "label": "Series Name",
          "value": "RT820SL-T"
        },
        {
          "label": "Lumen Output",
          "value": ">10,400lm"
        },
        {
          "label": "System Wattage",
          "value": "240W"
        },
        {
          "label": "CRI",
          "value": "70-95"
        },
        {
          "label": "Color Temperature (Kevin)",
          "value": "3000K-3500K、 4000K-4500k、5000K 、5700K"
        },
        {
          "label": "Input Voltage (High Voltage)",
          "value": "347-480VAC"
        },
        {
          "label": "Input Voltage (Low Voltage)",
          "value": "110-277VAC"
        },
        {
          "label": "L70 Hours",
          "value": ">100,000 at 25°C"
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
          "label": "L\" × W\" × H\"",
          "value": "32.3\" x 13.8\" x 3.9\" / 821 × 350 × 100 mm"
        },
        {
          "label": "Approximate Weight",
          "value": "( 40.3 lbs) 18.3 kgs"
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
      "model_number": "RT820SL-T",
      "ordering_info": [
        "RT820SL-T",
        "240W",
        "30=3000K\r\n40=4000K\r\n57=5700K",
        "S=Standard Voltage (110-277VAC)\r\nH=High Voltage (347-480VAC)",
        "70140=70x140°",
        "GRY=Grey\r\nBLK=Black",
        "1.0-10V\r\n2. Photocell\r\n3. PLC\r\n4.Zigbee"
      ]
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
      "description": "【Customer Profile】\r\nBohemia Manor High School, a public institution situated in Cecil County, MD.\r\n\r\n【Scope of Work】\r\nThe \"Bo Manor\" field suffered from an outdated, under-lit, and high-maintenance lighting system. Additionally, project parameters required seamless integration with the pre-existing pole structures.\r\n\r\n【The Solution】\r\nWe conducted a comprehensive photometric design to ensure all technical requirements were met. The final retrofit replaced 40 existing 1500W metal halide units with 48 of our FL9M 630W LED performance sports lights, delivering superior illumination and efficiency",
      "results": "<strong>30fc</strong> average illuminance, <strong>uniformity 1.37:1</strong> — exceeding the project requirements.",
      "image": "images/projects/football-field-led-retrofit/bmhs-football-field-02.webp",
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
        "images/projects/football-field-led-retrofit/bmhs-football-field-01.webp",
        "images/projects/football-field-led-retrofit/bmhs-football-field-02.webp",
        "images/projects/football-field-led-retrofit/bmhs-football-field-03.webp",
        "images/projects/football-field-led-retrofit/bmhs-football-field-04.webp",
        "images/projects/football-field-led-retrofit/bmhs-football-field-05.webp"
      ],
      "pdf_url": "files/football_field_led_retrofit.pdf"
    },
    {
      "pk": 13,
      "title": "Yuanshen Sports Centre Stadium",
      "location": "Shanghai, China",
      "slug": "yuanshen-sports-centre-stadium",
      "venue_type": "OUTDOOR",
      "sport_type": "SOCCER_FIELD",
      "description": "【Customer Profile】\r\nLocated in Shanghai's Pudong New Area, this 160,000 sqm multipurpose stadium accommodates 20,000 spectators. Formerly home to Shanghai Shenxin FC, it has served as the home ground for CSL powerhouse Shanghai Port FC (formerly SIPG) since 2021.\r\n\r\n【Scope of Work】\r\nElite tournament lighting standards were mandatory. The system was engineered to deliver 2,200 lux average illuminance, U0 ≥0.8, and Ra >80, ensuring full compliance with the 2018 AFC Stadium Lighting Guidelines. Our tailored solution successfully balanced these stringent performance metrics with the project's budgetary constraints.\r\n\r\n【The Solution】\r\nWe deployed 320 FL12M-1000W High-Performance LED sports luminaires (5000–5500K). A smart networked control system was also incorporated, providing remote switching, dimming capabilities, and real-time power monitoring.",
      "results": "2200 lux avg., U0=0.8, Ra>80 — meeting AFC Stadium Lighting Guidelines 2018.",
      "image": "images/projects/yuanshen-sports-centre-stadium/shys-soccer-02.webp",
      "order": 3,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/yuanshen-sports-centre-stadium/shys-soccer-01.webp",
        "images/projects/yuanshen-sports-centre-stadium/shys-soccer-02.webp",
        "images/projects/yuanshen-sports-centre-stadium/shys-soccer-03.webp",
        "images/projects/yuanshen-sports-centre-stadium/shys-soccer-04.webp",
        "images/projects/yuanshen-sports-centre-stadium/shys-soccer-05.webp"
      ],
      "pdf_url": "files/yuanshen_sports_centre_stadium.pdf"
    },
    {
      "pk": 2,
      "title": "Carroll County Sports Complex",
      "location": "United States",
      "slug": "baseball-field-led-retrofit",
      "venue_type": "OUTDOOR",
      "sport_type": "BASEBALL_FIELD",
      "description": "【Customer Profile】\r\nCarroll County Sports Complex is a premier community athletic facility dedicated exclusively to baseball. The complex serves as a vital training and competition hub for surrounding elementary and middle schools, as well as local youth leagues and regional tournaments.\r\n\r\n【Scope of Work】\r\nThe five baseball fields were previously equipped with outdated, high-maintenance lighting fixtures that suffered from uneven illumination and frequent bulb replacements. The facility management sought a modernized lighting upgrade that would deliver superior, glare-free visibility for fast-moving baseballs, while significantly reducing energy consumption and long-term maintenance costs for the school district.\r\n\r\n【The Solution】\r\nA total of 150 FL9M-630W Performance Series LED sports lights featuring remote-mount drivers were installed to ensure optimal thermal management and extended lifespan. Additionally, an advanced networked control system was integrated to enable seamless remote on/off operation and real-time power monitoring, streamlining facility management and maximizing operational efficiency.",
      "results": "<strong>50/30fc</strong> average illuminance, <strong>uniformity 2.0:1 / 2.5:1</strong> — meeting the project specifications.",
      "image": "images/projects/baseball-field-led-retrofit/ccsc-baseball-720p-01.webp",
      "order": 5,
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
        "images/projects/baseball-field-led-retrofit/ccsc-baseball-720p-01.webp",
        "images/projects/baseball-field-led-retrofit/ccsc-baseball-1080p-02.webp",
        "images/projects/baseball-field-led-retrofit/ccsc-baseball-1080p-03.webp",
        "images/projects/baseball-field-led-retrofit/ccsc-baseball-1080p-04.webp",
        "images/projects/baseball-field-led-retrofit/ccsc-baseball-1080p-05.webp"
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
      "description": "【Customer Profile】\r\nMorgan State University is Maryland’s premier public urban research university, renowned for its academic excellence and impactful community engagement.\r\n\r\n【Scope of Work】\r\nThe university sought to upgrade its athletic and campus lighting to enhance nighttime safety and support student-athletes. The project required a high-performance solution that met NCAA standards while aligning with the institution's sustainability goals.\r\n\r\n【The Solution】\r\nA customized LED lighting system was deployed across key venues, featuring precision photometric aiming for uniform, glare-free illumination. An integrated smart control platform was installed to enable remote scheduling and real-time energy monitoring, streamlining facility management and reducing operational costs.",
      "results": "<strong>over 80fc</strong> average illuminance, <strong>uniformity 1.67:1</strong>",
      "image": "images/projects/morgan-state-university-tennis-courts/msu-tennis-01.webp",
      "order": 7,
      "translations": {
        "fr": {
          "title": "Courts de tennis de l'Université Morgan State",
          "description": "【Profil du client】\nMorgan State University est la première université publique de recherche urbaine du Maryland, connue pour son excellence en matière d'enseignement, de recherche intensive, de service public efficace et d'engagement communautaire. Morgan prépare les diplômés diversifiés et compétitifs à réussir dans une société mondiale et interdépendante.",
          "location": "États-Unis"
        },
        "es": {
          "title": "Pistas de tenis de la Universidad Estatal Morgan",
          "description": "Perfil 【del cliente】\nMorgan State University es la principal universidad pública de investigación urbana en Maryland, conocida por su excelencia en la enseñanza, la investigación intensiva, el servicio público efectivo y la participación de la comunidad. Morgan prepara graduados diversos y competitivos para el éxito en una sociedad global e interdependiente.",
          "location": "Estados Unidos"
        },
        "de": {
          "title": "Tennisplätze der Morgan State University",
          "description": "【Kundenprofil】\nDie Morgan State University ist die führende öffentliche Stadtforschungsuniversität in Maryland, die für ihre Exzellenz in der Lehre, intensive Forschung, effektiven öffentlichen Dienst und soziales Engagement bekannt ist. Morgan bereitet vielfältige und wettbewerbsfähige Absolventen auf den Erfolg in einer globalen, voneinander abhängigen Gesellschaft vor.",
          "location": "Vereinigte Staaten von Amerika"
        },
        "ru": {
          "title": "Теннисные корты Morgan State University",
          "description": "Профиль 【клиента】\nГосударственный университет Моргана является ведущим государственным городским исследовательским университетом в Мэриленде, известным своим превосходством в обучении, интенсивных исследованиях, эффективной государственной службе и вовлечении сообщества. Morgan готовит разнообразных и конкурентоспособных выпускников к успеху в глобальном, взаимозависимом обществе.",
          "location": "Соединенные Штаты Америки"
        },
        "ar": {
          "title": "ملاعب التنس بجامعة ولاية مورغان",
          "description": "الملف الشخصي 【للعميل】\nجامعة ولاية مورغان هي الجامعة البحثية الحضرية العامة الرائدة في ولاية ماريلاند، والمعروفة بتميزها في التدريس والبحث المكثف والخدمة العامة الفعالة والمشاركة المجتمعية. تعد مورغان خريجين متنوعين وتنافسين للنجاح في مجتمع عالمي مترابط.",
          "location": "الولايات المتحدة الأمريكية"
        }
      },
      "gallery": [
        "images/projects/morgan-state-university-tennis-courts/msu-tennis-01.webp",
        "images/projects/morgan-state-university-tennis-courts/msu-tennis-02.webp",
        "images/projects/morgan-state-university-tennis-courts/msu-tennis-03.webp",
        "images/projects/morgan-state-university-tennis-courts/msu-tennis-04.webp",
        "images/projects/morgan-state-university-tennis-courts/msu-tennis-05.webp"
      ],
      "pdf_url": "files/morgan_state_university_tennis_courts.pdf"
    },
    {
      "pk": 7,
      "title": "Nanshan Ski Village",
      "location": "Beijing, China",
      "slug": "nanshan-ski-village",
      "venue_type": "OUTDOOR",
      "sport_type": "SKI_AREA",
      "description": "【Customer Profile】\r\nSituated north of Beijing, Nanshan Ski Village has served as China’s largest and most advanced ski resort since 2001, offering top-tier equipment and amenities for skiers and snowboarders alike.\r\n\r\n【Scope of Work】\r\nThe project required a lighting system tailored for winter sports. Advanced glare control and uniform illumination were mandatory to eliminate distracting shadows on the slopes. In a high-speed sport with zero margin for error, our LED technology ensures that lighting remains a reliable constant, providing the ultimate visual clarity for skiers and snowboarders.\r\n\r\n【The Solution】\r\nThrough rigorous photometric modeling, we optimized glare control and established exact aiming coordinates for every fixture. The SolarOne Vision Smart 260W RT410 Flood Lights were effortlessly integrated into the resort's infrastructure. Our LED solution outperforms legacy metal halide systems by delivering exceptional uniformity on the slopes and in the air, while drastically reducing light pollution. Additionally, the LEDs offer a lifespan of over 100,000 hours, compared to just 18,000 hours for traditional metal halides.",
      "results": "SolarOne Vision Smart RT410 floodlights upgrade lighting at Nanshan Ski Village. Low‑glare, uniform lighting protects vision for fast‑moving skiers and snowboarders. With minimal light spill, near‑zero maintenance and long‑life LEDs, the fixtures deliver excellent visual comfort for athletes and visitors, backed by a 10‑year manufacturer’s warranty.",
      "image": "images/projects/nanshan-ski-village/nanshan-ski-01.webp",
      "order": 9,
      "translations": {
        "fr": {
          "title": "Village de ski de Nanshan",
          "description": "【Profil du client】\nLe village de ski de Nanshan est situé au nord de la ville de Pékin. Depuis son ouverture en 2001, cette station de ski est devenue la plus grande du genre en Chine, offrant les équipements et les équipements de ski les plus avancés pour tous les amateurs de ski, qu'ils soient touristes ou locaux.\n\n【Étendue des travaux】\nSolarOne Vision Smart RT-410 a été sélectionné pour éclairer le village de ski de Nanshan. Dans tous les sports, l'éclairage LED offre la meilleure scène pour les compétiteurs, et ce n'est pas différent pour les skieurs et les snowboarders. La technologie de contrôle de l'éblouissement équivaut à un éclairage plus uniforme avec moins d'ombres indésirables ou de points chauds qui peuvent distraire les contributeurs pendant leur course. Dans un sport avec peu de marge d'erreur, la technologie LED permet de s'assurer que les lumières ne créent pas une autre variable pour les skieurs et les snowboarders.\n\n【La solution】\nUne conception photométrique d'ingénierie a été réalisée. L'éblouissement et la sortie de lumière ont été effectués. Ensuite, nous avons fourni des points de visée exacts pour chaque match. Les lampes d'inondation SolarOne Vision Smart 260W RT410 ont été facilement installées dans le village de ski de Nanshan. Nos solutions d'éclairage LED fournissent une lumière uniforme dans l'air et sur la pente beaucoup plus efficacement que la lumière aux halogénures métalliques et réduisent considérablement le déversement de lumière indésirable et la pollution lumineuse. La durée de vie des LED dépasse généralement 100 000 heures par rapport à une durée de vie traditionnelle des halogénures métalliques de 18 000 heures.",
          "location": "Pékin, Chine"
        },
        "es": {
          "title": "Nanshan Ski Village",
          "description": "Perfil 【del cliente】\nNanshan Ski Village se encuentra al norte de la ciudad de Pekín. Desde su apertura en 2001, esta estación de esquí se ha convertido en la más grande de su tipo en China, proporcionando los equipos y servicios de esquí más avanzados para todos los entusiastas del esquí, tanto turistas como lugareños.\n\n【Alcance del trabajo】\nSolarOne Vision Smart RT-410 fue seleccionado para iluminar la estación de esquí de Nanshan. En todos los deportes, la iluminación LED proporciona el mejor escenario para que los competidores se desempeñen, y no es diferente para los esquiadores y snowboarders. La tecnología de control de deslumbramiento equivale a una iluminación más uniforme con menos sombras no deseadas o puntos calientes que pueden distraer a los usuarios durante su carrera. En un deporte con poco margen de error, la tecnología LED ayuda a garantizar que las luces no creen otra variable para los esquiadores y snowboarders.\n\n【La solución】\nSe realizó un diseño fotométrico de ingeniería. Se realizó el deslumbramiento y la salida de luz. Luego proporcionamos puntos de puntería exactos para cada accesorio. La serie de luces de inundación SolarOne Vision Smart 260W RT410 se instaló fácilmente en la estación de esquí de Nanshan. Nuestras soluciones de iluminación LED proporcionan una luz uniforme en el aire y en la pendiente de manera mucho más eficiente que la luz de haluro metálico y reducen significativamente los derrames de luz no deseados y la contaminación lumínica. La vida útil de los LED generalmente supera las 100.000 horas en comparación con una vida útil tradicional de haluro metálico de 18.000 horas.",
          "location": "Pekin, China"
        },
        "de": {
          "title": "Nanshan Skidorf",
          "description": "【Kundenprofil】\nDas Skidorf Nanshan liegt nördlich von Peking-Stadt. Seit seiner Eröffnung im Jahr 2001 ist dieses Skigebiet das größte seiner Art in China und bietet die fortschrittlichsten Skiausrüstungen und Annehmlichkeiten für alle Skibegeisterten - sowohl Touristen als auch Einheimische.\n\n【Arbeitsumfang】\nSolarOne Vision Smart RT-410 wurde ausgewählt, um das Nanshan Ski Village zu beleuchten. In allen Sportarten bietet LED-Beleuchtung die beste Bühne für Konkurrenten, und das ist für Ski- und Snowboarder nicht anders. Die Blendschutztechnologie sorgt für eine gleichmäßigere Beleuchtung mit weniger unerwünschten Schatten oder Hotspots, die Patrons während ihres Laufs ablenken können. In einer Sportart mit wenig Spielraum für Fehler sorgt die LED-TECHNOLOGIE dafür, dass die Lichter keine weitere Variable für Skifahrer und Snowboarder darstellen.\n\n【Die Lösung】\nEs wurde ein konstruiertes photometrisches Design durchgeführt. Die Blend- und Lichtleistung wurde durchgeführt. Dann haben wir für jede Vorrichtung genaue Zielpunkte angegeben. Die SolarOne Vision Smart 260W RT410 Flutlicht-Serie wurde einfach im Skidorf Nanshan installiert. Unsere LED-Beleuchtungslösungen liefern gleichmäßiges Licht in der Luft und am Hang viel effizienter als Metallhalogenidlicht und reduzieren unerwünschtes Licht und Lichtverschmutzung erheblich. Die Lebensdauer von LEDs übersteigt im Allgemeinen 100.000 Stunden im Vergleich zu einer herkömmlichen Lebensdauer von 18.000 Stunden.",
          "location": "Peking, China"
        },
        "ru": {
          "title": "Лыжная деревня Наньшань",
          "description": "Профиль 【клиента】\nЛыжная деревня Наньшань расположена к северу от Пекина. С момента своего открытия в 2001 году этот горнолыжный курорт стал крупнейшим в своем роде в Китае, предоставляя самое современное горнолыжное оборудование и удобства для всех любителей горнолыжного спорта - как туристов, так и местных жителей.\n\n【Объем работ】\nДля освещения горнолыжной деревни Наньшань был выбран SolarOne Vision Smart RT-410. Во всех видах спорта светодиодное освещение обеспечивает лучшую сцену для выступлений участников, и оно ничем не отличается для лыжников и сноубордистов. Технология управления бликами обеспечивает более равномерное освещение с меньшим количеством нежелательных теней или горячих точек, которые могут отвлекать посетителей во время пробежки. В спорте с небольшим запасом на ошибку СВЕТОДИОДНАЯ технология помогает обеспечить, чтобы огни не создавали еще одну переменную для лыжников и сноубордистов.\n\n【Решение】\nВыполнен инженерный фотометрический расчет. Выполняли ослепление и светоотдачу. Затем мы предоставили точные точки прицеливания для каждого приспособления. SolarOne Vision Smart 260W RT410 Flood Light Series были легко установлены в лыжной деревне Наньшань. Наши светодиодные осветительные решения обеспечивают равномерный свет в воздухе и на склоне гораздо эффективнее, чем свет галогенида металла, и значительно уменьшают нежелательный разлив света и световое загрязнение. Срок службы светодиодов обычно превышает 100 000 часов по сравнению с традиционным сроком службы галогенида металла, составляющим 18 000 часов.",
          "location": "Пекин, Китай"
        },
        "ar": {
          "title": "قرية نانشان للتزلج",
          "description": "الملف الشخصي 【للعميل】\nتقع قرية نانشان للتزلج شمال مدينة بكين. منذ افتتاحه في عام 2001، أصبح منتجع التزلج هذا الأكبر من نوعه في الصين حيث يوفر أحدث معدات التزلج ووسائل الراحة لجميع عشاق التزلج - السياح والسكان المحليين على حد سواء.\n\n【نطاق العمل】\nتم اختيار SolarOne Vision Smart RT -410 لإضاءة قرية نانشان للتزلج. في جميع الألعاب الرياضية، توفر إضاءة LED أفضل مرحلة للمنافسين لأداءها، ولا يختلف الأمر بالنسبة للتزلج والتزلج على الجليد. تساوي تقنية التحكم في الوهج إضاءة أكثر اتساقًا مع عدد أقل من الظلال غير المرغوب فيها أو النقاط الساخنة التي يمكن أن تشتت انتباه العملاء أثناء الجري. في رياضة ذات هامش خطأ ضئيل، تساعد تقنية LED على ضمان أن الأضواء لا تخلق متغيرًا آخر للمتزلجين والمتزلجين على الجليد.\n\n【الحل】\nتم إجراء تصميم هندسي للقياسات الضوئية. تم تنفيذ الوهج وإخراج الضوء. ثم قدمنا نقاط التصويب الدقيقة لكل مباراة. تم تركيب سلسلة أضواء الفيضانات SolarOne Vision Smart 260W RT410 بسهولة في قرية نانشان للتزلج. توفر حلول الإضاءة LED الخاصة بنا ضوءًا موحدًا في الهواء وعلى المنحدر بكفاءة أكبر بكثير من ضوء الهاليد المعدني وتقلل بشكل كبير من انسكاب الضوء غير المرغوب فيه والتلوث الضوئي. يتجاوز عمر مصابيح LED عمومًا 100000 ساعة مقارنة بعمر هاليد معدني تقليدي يبلغ 18000 ساعة.",
          "location": "بكين، الصين"
        }
      },
      "gallery": [
        "images/projects/nanshan-ski-village/nanshan-ski-01.webp",
        "images/projects/nanshan-ski-village/nanshan-ski-02.webp",
        "images/projects/nanshan-ski-village/nanshan-ski-03.webp",
        "images/projects/nanshan-ski-village/nanshan-ski-04.webp",
        "images/projects/nanshan-ski-village/nanshan-ski-05.webp"
      ],
      "pdf_url": "files/nanshan_ski_village.pdf"
    },
    {
      "pk": 3,
      "title": "Andre Vacheresse Stadium",
      "location": "France",
      "slug": "multi-sport-arena-hd-broadcast",
      "venue_type": "INDOOR",
      "sport_type": "MULTI_SPORT",
      "description": "【Customer Profile】\r\nLocated in Roanne, France, Halle André Vacheresse is a premier indoor arena serving as the home of Chorale Roanne Basket and a host venue for the Tennis Fed Cup.\r\n\r\n【Scope of Work】\r\nThe project entailed a one-for-one upgrade of legacy 1500W metal halide fixtures. To accommodate diverse events like basketball and tennis, the gymnasium required a versatile lighting system. Premium LED lighting was chosen to dramatically elevate the athlete experience, providing high-lumen, glare-free illumination essential for tracking fast-moving action and executing precise shots.\r\n\r\n【The Solution】\r\nThrough rigorous photometric modeling, we optimized glare control and established exact aiming coordinates for every fixture. The SolarOne Vision Smart FL9M-720W lights were effortlessly integrated via our one-for-one retrofit plan. Our LED solution outperforms legacy metal halides by delivering exceptional uniformity in the air and on the court, achieving an outstanding average uniformity of 82%.",
      "results": "<strong>&gt;2000 lux</strong> — meeting HD broadcast standards.",
      "image": "images/projects/multi-sport-arena-hd-broadcast/basketball.webp",
      "order": 10,
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
        "images/projects/multi-sport-arena-hd-broadcast/choecm-basketball-01.webp",
        "images/projects/multi-sport-arena-hd-broadcast/choecm-basketball-02.webp",
        "images/projects/multi-sport-arena-hd-broadcast/choecm-basketball-03.webp",
        "images/projects/multi-sport-arena-hd-broadcast/choecm-basketball-04.webp",
        "images/projects/multi-sport-arena-hd-broadcast/choecm-basketball-05.webp",
        "images/projects/multi-sport-arena-hd-broadcast/choecm-tennis-01.webp"
      ],
      "pdf_url": "files/multi_sport_arena_hd_broadcast.pdf"
    },
    {
      "pk": 5,
      "title": "Narbonne Arena",
      "location": "France",
      "slug": "narbonne-arena",
      "venue_type": "INDOOR",
      "sport_type": "MULTI_SPORT",
      "description": "【Customer Profile】\r\nOpened in late 2019, Narbonne Arena is a premier modular venue in southern France. Accommodating up to 5,000 attendees, it serves as a central hub for touring shows, concerts, conventions, and sporting events.\r\n\r\n【Scope of Work】\r\nThe arena required a state-of-the-art audio infrastructure to complement its modern architectural acoustics. The project demanded a highly versatile sound system capable of delivering exceptional audio clarity across diverse event configurations and modular layouts.\r\n\r\n【The Solution】\r\nInstalled by Texen, the new GEO S12 line array system features 10 strategically deployed loudspeaker clusters, including two larger 6-module arrays facing the main grandstand. The system is powered by three NXAMP4x4 amplifiers equipped with Dante cards, ensuring seamless signal routing and uncompromising audio performance.",
      "results": "",
      "image": "images/projects/narbonne-arena/Narbonne-basketball-04.webp",
      "order": 13,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/narbonne-arena/Narbonne-basketball-04.webp",
        "images/projects/narbonne-arena/Narbonne-basketball-03.webp",
        "images/projects/narbonne-arena/Narbonne-basketball-02.webp",
        "images/projects/narbonne-arena/Narbonne-basketball-01.webp",
        "images/projects/narbonne-arena/Narbonne-basketball-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 8,
      "title": "Beijing Capital International Airport",
      "location": "Beijing, China",
      "slug": "beijing-capital-international-airport",
      "venue_type": "INFRASTRUCTURE",
      "sport_type": "AIRPORT",
      "description": "【Customer Profile】\r\nAs the primary international gateway to Beijing, Capital International Airport ranks among the world's largest and busiest aviation hubs.\r\n\r\n【Scope of Work】\r\nThe project required a comprehensive, one-for-one retrofit of existing 1000W metal halide fixtures across the airport's apron, terminals, and parking facilities. The objective was to deliver bright, uniform illumination for critical ground operations while significantly reducing energy consumption, maintenance costs, and unwanted light pollution to enhance overall safety.\r\n\r\n【The Solution】\r\nA rigorous photometric design was executed to optimize glare control and establish precise aiming coordinates for every fixture. The SolarOne Vision Smart 260W RT410 Flood Lights were seamlessly integrated via a one-for-one retrofit plan. Outperforming legacy metal halides, this LED solution delivers superior uniformity both in the air and on the ground, while reducing light spill and extending the system lifespan to over 100,000 hours.",
      "results": "SolarOne Vision Smart RT410 floodlights transform lighting performance at Beijing Capital International Airport. Offering 80% lighting uniformity and 75% energy savings, these low‑glare luminaires deliver superior visual comfort for pilots, ground crews and passengers. Engineered for extreme temperatures with near‑zero maintenance, they are supported by a 10‑year manufacturer's warranty.",
      "image": "images/projects/beijing-capital-international-airport/bcia-airport-01.webp",
      "order": 15,
      "translations": {
        "fr": {
          "title": "Aéroport international de Beijing",
          "description": "【Profil du client】\nL'aéroport international de Beijing Capital est le deuxième plus grand aéroport du monde et le principal aéroport international desservant Pékin. \n【Étendue des travaux】 \nSolarOne a été contacté pour créer une solution d'éclairage pour l'aire de trafic, les terminaux et les parkings de l'aéroport international de la capitale de Pékin. Ce projet consistait en un remplacement un pour un des luminaires aux halogénures métalliques de 1 000 watts existants. \nLes voyages en avion nécessitent beaucoup de déplacements ici même au sol. Les solutions d'éclairage LED SolarOne fournissent un éclairage lumineux et uniforme le long des routes d'accès aux aéroports, des parkings, des passerelles, des couloirs et des halls, réduisant ainsi la consommation d'énergie et les coûts d'entretien à deux chiffres. Notre technologie Vision Smart réduit les débordements de lumière tout en améliorant la sécurité de fonctionnement.\n【La solution】\nUne conception photométrique d'ingénierie a été réalisée. Nous avons vérifié l'éblouissement et la luminosité. Ensuite, nous avons fourni des points de visée exacts pour chaque match. [Error: Server Error: You made too many requests to the server.Accor]",
          "location": "[Error: Server Error: You made too many requests to the server.Accor]",
          "results": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]"
        },
        "es": {
          "title": "[Error: Server Error: You made too many requests to the server.Accor]",
          "description": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]",
          "location": "[Error: Server Error: You made too many requests to the server.Accor]",
          "results": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]"
        },
        "de": {
          "title": "[Error: Server Error: You made too many requests to the server.Accor]",
          "description": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]",
          "location": "[Error: Server Error: You made too many requests to the server.Accor]",
          "results": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]"
        },
        "ru": {
          "title": "[Error: Server Error: You made too many requests to the server.Accor]",
          "description": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]",
          "location": "[Error: Server Error: You made too many requests to the server.Accor]",
          "results": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]"
        },
        "ar": {
          "title": "[Error: Server Error: You made too many requests to the server.Accor]",
          "description": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]",
          "location": "[Error: Server Error: You made too many requests to the server.Accor]",
          "results": "[Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor] [Error: Server Error: You made too many requests to the server.Accor]"
        }
      },
      "gallery": [
        "images/projects/beijing-capital-international-airport/bcia-airport-01.webp",
        "images/projects/beijing-capital-international-airport/bcia-airport-02.webp",
        "images/projects/beijing-capital-international-airport/bcia-airport-03.webp",
        "images/projects/beijing-capital-international-airport/bcia-airport-04.webp",
        "images/projects/beijing-capital-international-airport/bcia-airport-05.webp"
      ],
      "pdf_url": "files/beijing_capital_international_airport.pdf"
    },
    {
      "pk": 10,
      "title": "Beijing International Tennis Center",
      "location": "Beijing, China",
      "slug": "beijing-international-tennis-center",
      "venue_type": "INDOOR",
      "sport_type": "TENNIS",
      "description": "【Customer Profile】\r\nBuilt in 1973, the Beijing International Club Tennis Hall holds the distinction of being China's first indoor professional tennis venue. To align with modern standards and ensure its continued development, the facility underwent a comprehensive reconstruction on its original site in 2015.\r\n\r\n【Scope of Work】\r\nThe reconstruction project required a one-for-one replacement of the existing 1000W metal halide fixtures. As tennis is a sport with virtually no margin for error, the lighting system had to provide the ultimate visual stage for athletes. Advanced glare control and uniform illumination were mandatory to eliminate distracting shadows or hot spots, ensuring that the lighting remains a reliable constant rather than an unpredictable variable during high-speed play.\r\n\r\n【The Solution】\r\nA rigorous photometric design was executed to optimize glare control and establish precise aiming coordinates for every fixture. The new LED lighting system was seamlessly integrated via a one-for-one retrofit plan, outperforming legacy metal halides by delivering exceptional uniformity both in the air and on the court, thereby guaranteeing optimal visual clarity for professional tennis.",
      "results": "SolarOne Vision Smart RT410FL‑S160W elevates lighting performance at Beijing International Tennis Club. Delivering 75% uniformity and 50% energy savings, these low‑glare luminaires ensure excellent visual comfort for athletes and coaches. Long‑life LEDs reduce part replacements with virtually no ongoing maintenance.",
      "image": "images/projects/beijing-international-tennis-center/bitc-tennis-01.webp",
      "order": 17,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/beijing-international-tennis-center/bitc-tennis-01.webp",
        "images/projects/beijing-international-tennis-center/bitc-tennis-02.webp",
        "images/projects/beijing-international-tennis-center/bitc-tennis-03.webp",
        "images/projects/beijing-international-tennis-center/bitc-tennis-04.webp"
      ],
      "pdf_url": "files/beijing_international_tennis_center.pdf"
    },
    {
      "pk": 11,
      "title": "National Snow and Ice Research Center",
      "location": "Beijing, China",
      "slug": "national-snow-and-ice-research-center",
      "venue_type": "INDOOR",
      "sport_type": "ICE_ARENA",
      "description": "【Customer Profile】\r\nBuilt on the historic site of a former 1897 engine factory, the National Snow and Ice Training and Research Center served as a vital hub for the 2022 Beijing Winter Olympics. It features Asia's first CO2 ice-making speed skating hall, comprising a 400m rink and two short track rinks built to strict Olympic competition standards.\r\n\r\n【Scope of Work】\r\nAs an elite Olympic training venue, the center required a high-performance lighting system that met rigorous broadcast and training standards. The solution needed to deliver exceptional visual clarity and precise color rendering for high-speed skating, while seamlessly integrating with the venue's sustainable infrastructure.\r\n\r\n【The Solution】\r\nA total of 304 FL9M-630W High-Performance LED sports luminaires (CCT: 5000–5500K, Ra: 90) were strategically installed to ensure optimal visual conditions. Additionally, an advanced networked control system was integrated to enable remote operation and real-time power monitoring, streamlining facility management.",
      "results": "Built to meet strict tournament‑grade lighting requirements, the 400 m speed‑skating rink achieves 2000 lx average illuminance with U₀ uniformity of 0.7, satisfying HD live TV broadcast standards. Its intelligent lighting control system with interval‑lighting mode delivers an extra 50% energy savings. The complete lighting solution meets both project budget and performance expectations.",
      "image": "images/projects/national-snow-and-ice-research-center/27factory-01.webp",
      "order": 19,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/national-snow-and-ice-research-center/27factory-01.webp",
        "images/projects/national-snow-and-ice-research-center/27factory-02.webp",
        "images/projects/national-snow-and-ice-research-center/27factory-03.webp",
        "images/projects/national-snow-and-ice-research-center/27factory-04.webp",
        "images/projects/national-snow-and-ice-research-center/27factory-05.webp"
      ],
      "pdf_url": "files/national_snow_and_ice_research_center.pdf"
    },
    {
      "pk": 12,
      "title": "Hangzhou Asian Games Velodrome",
      "location": "Hangzhou, China",
      "slug": "chunan-velodrome",
      "venue_type": "INDOOR",
      "sport_type": "VELODROME",
      "description": "【Customer Profile】\r\nLocated in the Qiandao Lake Tourism Resort, the Chun'an Velodrome served as the core cycling venue for the Hangzhou Asian Games. Inspired by the \"Leaping Fish in the Morning Sun\" concept, this 40-meter-tall landmark features a dynamic oval steel canopy and floodlighting system. It houses a 250-meter international standard indoor track with a seating capacity of 3,040.\r\n\r\n【Scope of Work】\r\nAs the premier venue for elite Asian Games cycling competitions, the velodrome required a world-class lighting system capable of supporting high-speed track events. The lighting solution needed to deliver flawless uniformity and precise color rendering for both athletes and broadcast cameras, while seamlessly complementing the venue's dynamic, pearl-inspired architectural design.\r\n\r\n【The Solution】\r\nA comprehensive photometric design was executed to optimize glare control and ensure precise aiming for the steeply banked track. The integrated dynamic floodlighting system was strategically calibrated to highlight the venue's iconic architecture, delivering exceptional visual clarity and an immersive atmosphere for both competitors and spectators.",
      "results": "Horizontal illuminance: > 3200 lux (Uniformity: 0.90)\r\nMain Camera illuminance: > 2600 lux (Uniformity: 0.84)\r\nAuxiliary Camera illuminance: > 2200 lux (Uniformity: 0.70)\r\nComplies with HD broadcasting standards.",
      "image": "images/projects/chunan-velodrome/bycicle-chunan01.webp",
      "order": 21,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/chunan-velodrome/bycicle-chunan01.webp",
        "images/projects/chunan-velodrome/bycicle-chunan04.webp",
        "images/projects/chunan-velodrome/bycicle-chunan03.webp",
        "images/projects/chunan-velodrome/bycicle-chunan02.webp",
        "images/projects/chunan-velodrome/bycicle-chunan05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 9,
      "title": "Olympic Sports Center Gymnasium (Beijing)",
      "location": "Beijing, China",
      "slug": "olympic-sports-center-gymnasium-beijing",
      "venue_type": "INDOOR",
      "sport_type": "BASKETBALL",
      "description": "【Customer Profile】\r\nLocated on the north side of the National Olympic Sports Center, the Beijing National Olympic Center Gymnasium (commonly known as the \"Aoti Center Gymnasium\") is a premier hexagonal arena. Spanning 4 hectares with a floor area of 32,410 square meters, it accommodates 6,300 spectators and serves as the home venue for the Beijing Royal Fighters of the Chinese Basketball Association (CBA).\r\n\r\n【Scope of Work】\r\nAs the home arena for a professional CBA team, the gymnasium required a high-performance lighting system capable of supporting elite basketball competitions and broadcast standards. The project demanded a solution that delivers exceptional visual clarity, uniform illumination, and minimal glare to track fast-moving action, while seamlessly integrating with the venue's unique hexagonal architecture.\r\n\r\n【The Solution】\r\nA rigorous photometric design was executed to optimize glare control and establish precise aiming coordinates for the 40x70-meter playing court. The new LED lighting system was seamlessly installed, outperforming legacy fixtures by delivering superior uniformity across the court and in the air, ensuring optimal visual conditions for both athletes and spectators.",
      "results": "Horizontal illuminance: > 4000 lux (Uniformity: 0.8)\r\nCamera illuminance: > 3000 lux (Uniformity: 0.7)\r\nComplies with HD broadcasting standards.",
      "image": "images/projects/olympic-sports-center-gymnasium-beijing/oscg-01.webp",
      "order": 23,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/olympic-sports-center-gymnasium-beijing/oscg-01.webp",
        "images/projects/olympic-sports-center-gymnasium-beijing/oscg-02.webp",
        "images/projects/olympic-sports-center-gymnasium-beijing/oscg-03.webp",
        "images/projects/olympic-sports-center-gymnasium-beijing/oscg-04.webp",
        "images/projects/olympic-sports-center-gymnasium-beijing/oscg-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 14,
      "title": "Beijing LIULIQIAO Bridge",
      "location": "Beijing, China",
      "slug": "beijing-liu-li-bridge",
      "venue_type": "ROADWAY",
      "sport_type": "CITY_EXPRESSWAY",
      "description": "【Customer Profile】\r\nLiuliqiao is a major traffic hub situated on Beijing’s Third Ring Road, serving as a critical artery for the city's high-volume vehicular flow.\r\n【Scope of Work】\r\nThe intersection's original lighting infrastructure consisted of nine 1000W high-pressure sodium (HPS) lamps mounted on six 35-meter high-mast poles. The facility required a comprehensive lighting upgrade to significantly reduce energy consumption and modernize the illumination quality while maintaining adequate visibility for nighttime traffic safety.\r\n【The Solution】\r\nThe project executed a strategic retrofit, replacing the legacy HPS lamps with eighteen 200W LED floodlights utilizing a 2800K color temperature. This upgrade achieved a remarkable 66.67% energy-saving rate. The optimized system now delivers an average illuminance of 33 lx with a uniformity ratio of 0.56, maintaining a maximum illuminance of 68 lx and a minimum of 23 lx to ensure safe and consistent road visibility.",
      "results": "The original nine 1000W high-pressure sodium (HPS) lamps have been replaced with eighteen 200W LED floodlights. The average illuminance is 33 lx, with a uniformity ratio of 0.56. The maximum illuminance is 68 lx, and the minimum is 23 lx.\r\nUsing a 2800K color temperature, this upgrade achieves an energy-saving rate of 66.67%.",
      "image": "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-01.webp",
      "order": 25,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-01.webp",
        "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-02.webp",
        "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-03.webp",
        "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-04.webp",
        "images/projects/beijing-liu-li-bridge/llq-roadway-1080p-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 15,
      "title": "Fencing Venue of the 7th CISM Military World Games",
      "location": "Wuhan, China",
      "slug": "fencing-venue-of-the-7th-cism-military-world-games",
      "venue_type": "INDOOR",
      "sport_type": "FENCING",
      "description": "【Customer Profile】\r\nThe Wuhan Business University Fencing Hall served as the venue for the fencing events of the Modern Pentathlon during the 7th CISM Military World Games. Notably, this project was the first to be completed and boasted the shortest construction cycle among all 35 venues for the Games.\r\n\r\n【Scope of Work】\r\nThe arena features a competition area with 10 pistes and a training area with 5 to 8 pistes, accommodating up to 2,185 spectators. The primary lighting challenge was to achieve a True \"shadowless\" effect. To meet the rigorous demands of high-speed fencing, the ceiling illumination required precise photometric calculations to eliminate distracting shadows and provide flawless visual clarity for the athletes.\r\n\r\n【The Solution】\r\nOver 180 FL6M-480W LED fixtures were strategically installed across the ceiling. Through meticulous optical design and exact aiming point calculations, the system delivers a uniform, shadowless glow that completely envelops the athletes. This advanced lighting solution ensures optimal visual conditions, allowing competitors to track fast-moving actions with absolute precision.",
      "results": "Horizontal illuminance: > 3600 lux (Uniformity: 0.90)\r\nMain Camera illuminance: > 1500 lux (Uniformity: 0.80)\r\nComplies with HD broadcasting standards.",
      "image": "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-04.webp",
      "order": 27,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-01.webp",
        "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-02.webp",
        "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-03.webp",
        "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-04.webp",
        "images/projects/fencing-venue-of-the-7th-cism-military-world-games/whzyxy-fencing-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 16,
      "title": "Red 1 Karting Beijing",
      "location": "Beijing, China",
      "slug": "red-1-karting-beijing",
      "venue_type": "OUTDOOR",
      "sport_type": "KARTING",
      "description": "Red 1 Karting Beijing is a well-known indoor and outdoor comprehensive karting operator in Beijing, featuring China's first CIK-FIA certified international professional karting track.",
      "results": "",
      "image": "images/projects/red-1-karting-beijing/red1-karting-1080p-01.webp",
      "order": 29,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/red-1-karting-beijing/red1-karting-1080p-01.webp",
        "images/projects/red-1-karting-beijing/red1-karting-1080p-02.webp",
        "images/projects/red-1-karting-beijing/red1-karting-1080p-03.webp",
        "images/projects/red-1-karting-beijing/red1-karting-1080p-04.webp",
        "images/projects/red-1-karting-beijing/red1-karting-1080p-05.webp"
      ],
      "pdf_url": "files/red_1_karting_beijing.pdf"
    },
    {
      "pk": 17,
      "title": "Yingdong Natatorium",
      "location": "Beijing, China",
      "slug": "yingdong-natatorium",
      "venue_type": "INDOOR",
      "sport_type": "AQUATICS_CENTRE",
      "description": "【Customer Profile】\r\nLocated within Beijing's National Olympic Sports Center, the Yingdong Natatorium is a landmark aquatic venue funded by Henry Fok in 1986. Spanning 44,635 square meters with 6,000 seats, it has hosted prestigious international events including the 1990 Asian Games and the 2008 Beijing Olympics.\r\n\r\n【Scope of Work】\r\nThe venue required a high-performance lighting system engineered specifically for high-definition television broadcasting. The solution needed to deliver top-tier illumination while strictly managing glare and water reflections, ensuring optimal visual clarity and color rendering for elite aquatic competitions.\r\n\r\n【The Solution】\r\nA comprehensive photometric design was executed to optimize glare control and establish precise aiming coordinates. The new LED system delivers superior uniformity both in the air and across the pool, guaranteeing flawless visual conditions for athletes and broadcast cameras while meeting stringent HD broadcasting standards.",
      "results": "Horizontal illuminance: > 2700 lux (Uniformity: 0.70)\r\nMain Camera illuminance: > 2200 lux (Uniformity: 0.60)\r\nAuxiliary Camera illuminance: > 1500 lux (Uniformity: 0.55)\r\nComplies with HD broadcasting standards.",
      "image": "images/projects/yingdong-natatorium/ydyyg-swim-01.webp",
      "order": 31,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/yingdong-natatorium/ydyyg-swim-01.webp",
        "images/projects/yingdong-natatorium/ydyyg-swim-02.webp",
        "images/projects/yingdong-natatorium/ydyyg-swim-03.webp",
        "images/projects/yingdong-natatorium/ydyyg-swim-04.webp",
        "images/projects/yingdong-natatorium/ydyyg-swim-05.webp"
      ],
      "pdf_url": ""
    },
    {
      "pk": 18,
      "title": "Perryville High School",
      "location": "United States",
      "slug": "perryville-high-school",
      "venue_type": "OUTDOOR",
      "sport_type": "FOOTBALL_FIELD",
      "description": "【Customer Profile】\r\nPerryville High School is a prominent public educational institution in Perryville, Maryland, operated by Cecil County Public Schools. The campus serves as the proud home of the Perryville Panthers.\r\n\r\n【Scope of Work】\r\nMuch like the recent \"Bo Manor\" project completed for CCPS, the athletic field at Perryville suffered from an outdated, under-lit, and high-maintenance lighting system. Additionally, project parameters strictly required seamless integration with the pre-existing pole structures.\r\n\r\n【The Solution】\r\nA comprehensive photometric design was executed to ensure all technical requirements were met. The final retrofit replaced forty (40) legacy 1500W metal halide units with forty-eight (48) of our FL9M-630W LED performance sports lights, delivering superior illumination and efficiency.",
      "results": "<strong>30fc</strong> average illuminance, <strong>uniformity 1.56:1</strong> — exceeding the project requirements.",
      "image": "images/projects/perryville-high-school/phs-football-02.webp",
      "order": 33,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/perryville-high-school/phs-football-05.webp",
        "images/projects/perryville-high-school/phs-football-01.webp",
        "images/projects/perryville-high-school/phs-football-04.webp",
        "images/projects/perryville-high-school/phs-football-03.webp",
        "images/projects/perryville-high-school/phs-football-02.webp"
      ],
      "pdf_url": "files/perryville_high_school.pdf"
    },
    {
      "pk": 19,
      "title": "McIntosh County Academy",
      "location": "United States",
      "slug": "mcintosh-county-academy",
      "venue_type": "OUTDOOR",
      "sport_type": "FOOTBALL_FIELD",
      "description": "【Customer Profile】\r\nMcIntosh County Academy is the sole public high school in McIntosh County, Georgia. Formerly known as Darien High School, it serves as a vital educational and athletic hub for the local community.\r\n\r\n【Scope of Work】\r\nThe school sought to upgrade its existing football field lighting to a modern, energy-efficient LED system. A critical project constraint was the requirement to reuse the existing poles and infrastructure to ensure the upgrade remained on schedule and strictly within budget.\r\n\r\n【The Solution】\r\nA precision photometric design was executed to guarantee full compliance with IES recommended lighting levels. The project was seamlessly completed via a one-for-one retrofit using our FL9M-720W LED performance sports lights, delivering spectacular illumination and operational efficiency.",
      "results": "",
      "image": "images/projects/mcintosh-county-academy/mc-football-04.webp",
      "order": 35,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/mcintosh-county-academy/mc-football-01.webp",
        "images/projects/mcintosh-county-academy/mc-football-02.webp",
        "images/projects/mcintosh-county-academy/mc-football-04.webp",
        "images/projects/mcintosh-county-academy/mc-football-03.webp",
        "images/projects/mcintosh-county-academy/mc-football-05.webp"
      ],
      "pdf_url": "files/mcintosh_county_academy.pdf"
    },
    {
      "pk": 20,
      "title": "Garrison Forest School",
      "location": "United States",
      "slug": "garrison-forest-school",
      "venue_type": "OUTDOOR",
      "sport_type": "SOCCER_FIELD",
      "description": "【Customer Profile】\r\nGarrison Forest School (GFS) is a premier, non-denominational private college preparatory school located on a 110-acre campus in Owings Mills, Maryland. Serving girls from kindergarten through 12th grade alongside a coeducational pre-K program, GFS is fully accredited by both the Middle States Association of Colleges and Secondary Schools and the Association of Independent Maryland Schools.\r\n\r\n【Scope of Work】\r\nWorking in close collaboration with the school's facility management team, the project aimed to install a state-of-the-art LED lighting system. The primary objectives were to deliver tournament-level illumination for athletic events while ensuring the new system was highly durable and easy to maintain.\r\n\r\n【The Solution】\r\nThe VSP Sports Lighting system was deployed, featuring high-performance FL12M-1000W fixtures. To optimize long-term maintenance, the system utilizes remote-mounted driver boxes, providing facility managers with safe and effortless accessibility for future servicing.",
      "results": ">50fc",
      "image": "images/projects/garrison-forest-school/Garrison_Forest-1.webp",
      "order": 37,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/garrison-forest-school/Garrison_Forest-1.webp",
        "images/projects/garrison-forest-school/Garrison_Forest-2.webp",
        "images/projects/garrison-forest-school/Garrison_Forest-3.webp",
        "images/projects/garrison-forest-school/Garrison_Forest-4.webp",
        "images/projects/garrison-forest-school/Garrison_Forest-5.webp"
      ],
      "pdf_url": "files/garrison_forest_school.pdf"
    },
    {
      "pk": 21,
      "title": "North Creek Community Center",
      "location": "United States",
      "slug": "north-creek-community-center",
      "venue_type": "OUTDOOR",
      "sport_type": "TENNIS_COURTS",
      "description": "【Customer Profile】\r\nNorth Creek Community Center features meeting room, community rooms, swimming pool, tennis courts, pickleball courts, soccer court, a tot lot, nature study and walking paths. \r\n\r\n【Scope of work】\r\nMontgomery Village Foundation was looking to improve the lighting on the sports courts at this facility. The SolarOne design team came up with a lighting layout to meet IES recommended lighting levels while allowing for the Owners to reuse the existing poles and structures.\r\n\r\n【Solution】\r\nOnce again, our RT410FL-260W sports light proves why it is our banner product and the perfect LED retrofit solution for sports courts!",
      "results": "",
      "image": "images/projects/north-creek-community-center/ncc-tennis-03.webp",
      "order": 39,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/north-creek-community-center/ncc-tennis-01.webp",
        "images/projects/north-creek-community-center/ncc-tennis-02.webp",
        "images/projects/north-creek-community-center/ncc-tennis-03.webp"
      ],
      "pdf_url": "files/north_creek_community_center.pdf"
    },
    {
      "pk": 22,
      "title": "Pickle n Par club",
      "location": "United States",
      "slug": "pickle-n-par-club",
      "venue_type": "INDOOR",
      "sport_type": "TENNIS",
      "description": "【Customer Profile】\r\nPickle N Par is Long Island’s premier and only dedicated indoor pickleball facility. Renowned for its exceptional court surfaces and superb lighting, the venue provides an ideal setting for players of all levels. Featuring organized play sessions and top-tier instruction, it stands as the ultimate destination for pickleball enthusiasts in New York.\r\n\r\n【Scope of Work】\r\nIn the summer of 2019, our partners at Green Arc Energy Advisors engaged SolarOne to design an LED lighting solution for this new indoor facility. The primary objective was to deliver competition-level illumination while ensuring optimal visual comfort for both players and spectators. Our team developed a precision lighting layout and supplied high-performance fixtures to meet these exacting standards.\r\n\r\n【The Solution】\r\nThe RT400HB-100W Recreation Series high bay fixtures were selected as the perfect solution for this application. Delivering uniform, glare-free illumination, the system successfully achieved competition-grade lighting levels while maintaining exceptional visual comfort, elevating the overall playing experience.",
      "results": "",
      "image": "images/projects/pickle-n-par-club/pap-pickleball-01.webp",
      "order": 41,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/pickle-n-par-club/pap-pickleball-01.webp",
        "images/projects/pickle-n-par-club/pap-pickleball-02.webp",
        "images/projects/pickle-n-par-club/pap-pickleball-03.webp",
        "images/projects/pickle-n-par-club/pap-pickleball-04.webp",
        "images/projects/pickle-n-par-club/pap-pickleball-05.webp"
      ],
      "pdf_url": "files/pickle_n_par_club.pdf"
    },
    {
      "pk": 23,
      "title": "National Olympic Sports Center (Beijing) Tennis Courts",
      "location": "Beijing, China",
      "slug": "national-olympic-sports-center-beijing-tennis-cour",
      "venue_type": "OUTDOOR",
      "sport_type": "TENNIS_COURTS",
      "description": "【Customer Profile】\r\nLocated within the National Olympic Sports Center in Beijing, the Tennis Center is a premier facility featuring 20 high-standard indoor and outdoor courts. It serves as a vital training base for the Chinese National Tennis Team.\r\n\r\n【Scope of Work】\r\nThe project entailed a one-for-one LED upgrade of legacy 400W metal halide fixtures, seamlessly reusing the existing pole infrastructure. Absolute ball clarity, regardless of speed or position, is paramount for elite tennis. Delivering exceptional visibility for high-speed action requires striking contrast, calibrated illumination, and flawless court uniformity.\r\n\r\n【The Solution】\r\nThrough rigorous photometric modeling, we optimized glare control and light output, providing exact aiming directives for every fixture. The SolarOne Vision Smart 200W RT470 Flood Lights integrated effortlessly with the existing infrastructure. Our LED solution outperforms legacy metal halide systems by delivering exceptional aerial and on-court uniformity, while drastically reducing light spill and pollution.",
      "results": "",
      "image": "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-02.webp",
      "order": 43,
      "translations": {
        "fr": {},
        "es": {},
        "de": {},
        "ru": {},
        "ar": {}
      },
      "gallery": [
        "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-01.webp",
        "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-02.webp",
        "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-03.webp",
        "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-04.webp",
        "images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-05.webp"
      ],
      "pdf_url": "files/national_olympic_sports_center_beijing_tennis_cour.pdf"
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
    "social_facebook": "https://www.facebook.com/SolaroneEnergyTech",
    "social_instagram": "https://www.instagram.com/solaronevision/",
    "social_youtube": "https://www.youtube.com/@SolaroneVision",
    "social_tiktok": "https://www.tiktok.com/@solaroneledlighting?lang=zh-Hans",
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
  },
  "productspagecards": [
    {
      "title": "M Series",
      "subtitle": "Truly modular design — scalable from a single 1M (80W) module up to 16M (1280W) or beyond. Flexible combination configurations to precisely match any project requirement.",
      "image": "images/products_page/m-series-04.webp",
      "slug": "m-series",
      "link_url": "/products/m-series/",
      "order": 1,
      "is_active": True
    },
    {
      "title": "RT410 Series",
      "subtitle": "Professional LED floodlights designed for sports fields, arenas, and large-area illumination. Flicker-free drivers with broadcast-grade performance.",
      "image": "images/products_page/rt410-series.webp",
      "slug": "rt410-series",
      "link_url": "/products/rt410-series/",
      "order": 2,
      "is_active": True
    },
    {
      "title": "VSP series",
      "subtitle": "Vision Strobe Protection system for broadcast venues. Eliminates flicker in slow-motion replay with stable, high-frequency drive technology.",
      "image": "images/products_page/VSP9M-01.webp",
      "slug": "vsp-xxxxw-9m-yp",
      "link_url": "/products/vsp-xxxxw-9m-yp/",
      "order": 3,
      "is_active": True
    },
    {
      "title": "FLOOD LIGHTING",
      "subtitle": "RT180FS ~ RT420FS series flood lighting",
      "image": "images/products_page/flood-light-01.webp",
      "slug": "rt420fs-s",
      "link_url": "/products/rt420fs-s/",
      "order": 4,
      "is_active": True
    },
    {
      "title": "HIGHBAY",
      "subtitle": "Typical Applications High school, college , professional stadiums, Large area, Industrial Facilities, Building facades",
      "image": "images/products_page/highbay-01.webp",
      "slug": "rt400hb",
      "link_url": "/products/rt400hb/",
      "order": 5,
      "is_active": True
    },
    {
      "title": "Street Lighting",
      "subtitle": "Professional LED roadway lighting solution designed for streets, highways, and infrastructure projects. Delivers uniform illumination with energy-efficient performance.",
      "image": "images/products_page/street-lighting-series-01.webp",
      "slug": "rt600sl-t",
      "link_url": "/products/rt600sl-t/",
      "order": 6,
      "is_active": True
    }
  ]
}
