#!/usr/bin/env python
"""Generate docs/i18n_p0_draft.csv — the P0 (SEO) machine-translation DRAFT.

These are MACHINE-TRANSLATION DRAFTS for native-speaker proofreading
(see docs/i18n_翻译工作指引.md). Rules applied:
  * Brand 'SolarOne' is never translated.
  * Proper nouns keep their localized exonym where one is standard (Beijing -> Peking / Pékin /
    Pekín / Пекин / بكين).
  * Model codes (FL1M etc.) never appear in P0 SEO copy, so no code handling needed here.

Output is consumed by scripts/import_i18n_csv.py.
"""
import csv
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO_ROOT, "docs", "i18n_p0_draft.csv")

COLS = ["key", "en", "fr", "es", "de", "ru", "ar", "note"]

ROWS = [
    # ---- Global SiteConfig defaults (mechanism ② -> _SIDEBAR_I18N via overrides) ----
    dict(
        key="siteconfig.meta_title",
        en="SolarOne — Precision LED Lighting Systems",
        fr="SolarOne — Systèmes d'éclairage LED de précision",
        es="SolarOne — Sistemas de iluminación LED de precisión",
        de="SolarOne — Präzise LED-Beleuchtungssysteme",
        ru="SolarOne — Прецизионные системы светодиодного освещения",
        ar="SolarOne — أنظمة إضاءة LED دقيقة",
        note="Global default for every page <title> / og:title (base.html)",
    ),
    dict(
        key="siteconfig.meta_description",
        en="Professional LED sports lighting, high bay, and modular luminaire solutions. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.",
        fr="Solutions professionnelles d'éclairage LED pour le sport, haute baie et luminaires modulaires. Conçues à Pékin depuis 2007, reconnues dans plus de 50 pays.",
        es="Soluciones profesionales de iluminación LED deportiva, alta bahía y luminarias modulares. Diseñadas en Pekín desde 2007, con la confianza de más de 50 países.",
        de="Professionelle LED-Sportbeleuchtung, High-Bay und modulare Leuchtenlösungen. Entwickelt in Peking seit 2007, weltweit in über 50 Ländern vertraut.",
        ru="Профессиональные решения светодиодного спортивного освещения, высокого пролёта и модульных светильников. Разработаны в Пекине с 2007 года, доверие более чем 50 стран.",
        ar="حلول احترافية للإضاءة الرياضية بتقنية LED، وإضاءة عالية، ومصابيح معيارية. صُممت في بكين منذ 2007، وتحظى بثقة أكثر من 50 دولة.",
        note="Global default for every page meta description",
    ),
    # ---- Per-page <title> (mechanism ① -> gettext) ----
    dict(
        key="template.home_title",
        en="SolarOne — Professional LED Sports Lighting Solutions Since 2007",
        fr="SolarOne — Solutions d'éclairage LED sportif professionnelles depuis 2007",
        es="SolarOne — Soluciones profesionales de iluminación LED deportiva desde 2007",
        de="SolarOne — Professionelle LED-Sportbeleuchtungslösungen seit 2007",
        ru="SolarOne — Профессиональные решения светодиодного спортивного освещения с 2007 года",
        ar="SolarOne — حلول إضاءة رياضية احترافية بتقنية LED منذ 2007",
        note="home.html <title>",
    ),
    dict(
        key="template.about_title",
        en="About SolarOne — LED Lighting Manufacturer Since 2007",
        fr="À propos de SolarOne — Fabricant d'éclairage LED depuis 2007",
        es="Acerca de SolarOne — Fabricante de iluminación LED desde 2007",
        de="Über SolarOne — LED-Beleuchtungshersteller seit 2007",
        ru="О SolarOne — Производитель светодиодного освещения с 2007 года",
        ar="حول SolarOne — مصنّع إضاءة LED منذ 2007",
        note="about.html <title>",
    ),
    dict(
        key="template.contact_title",
        en="Contact SolarOne — Get a LED Lighting Quote Today",
        fr="Contactez SolarOne — Obtenez un devis d'éclairage LED dès aujourd'hui",
        es="Contacte con SolarOne — Solicite un presupuesto de iluminación LED hoy",
        de="Kontaktieren Sie SolarOne — Fordern Sie heute ein LED-Beleuchtungsangebot an",
        ru="Свяжитесь с SolarOne — Получите расчёт LED-освещения уже сегодня",
        ar="تواصل مع SolarOne — احصل على عرض أسعار للإضاءة LED اليوم",
        note="contact.html <title>",
    ),
    dict(
        key="template.news_title",
        en="News — SolarOne LED Lighting Updates",
        fr="Actualités — Nouveautés de l'éclairage LED SolarOne",
        es="Noticias — Novedades de iluminación LED de SolarOne",
        de="News — SolarOne LED-Beleuchtungs-Updates",
        ru="Новости — Обновления светодиодного освещения SolarOne",
        ar="الأخبار — مستجدات إضاءة LED من SolarOne",
        note="news.html <title>",
    ),
    dict(
        key="template.products_title",
        en="LED Lighting Products — SolarOne Professional Lighting Solutions",
        fr="Produits d'éclairage LED — Solutions d'éclairage professionnelles SolarOne",
        es="Productos de iluminación LED — Soluciones de iluminación profesional SolarOne",
        de="LED-Beleuchtungsprodukte — Professionelle SolarOne Beleuchtungslösungen",
        ru="Продукция светодиодного освещения — Профессиональные решения освещения SolarOne",
        ar="منتجات الإضاءة LED — حلول إضاءة احترافية من SolarOne",
        note="products.html <title>",
    ),
    dict(
        key="template.projects_title",
        en="LED Lighting Projects — SolarOne Projects Worldwide",
        fr="Projets d'éclairage LED — Projets SolarOne dans le monde",
        es="Proyectos de iluminación LED — Proyectos SolarOne en todo el mundo",
        de="LED-Beleuchtungsprojekte — SolarOne Projekte weltweit",
        ru="Проекты светодиодного освещения — Проекты SolarOne по всему миру",
        ar="مشاريع إضاءة LED — مشاريع SolarOne حول العالم",
        note="projects.html <title>",
    ),
    # ---- Per-page <meta name="description"> (mechanism ① -> gettext) ----
    dict(
        key="template.home_meta",
        en="SolarOne designs and manufactures professional LED sports lighting, high bay, and industrial lighting systems. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.",
        fr="SolarOne conçoit et fabrique des systèmes d'éclairage LED sportif, haute baie et industriel professionnels. Conçus à Pékin depuis 2007, ils sont adoptés dans plus de 50 pays.",
        es="SolarOne diseña y fabrica sistemas de iluminación LED deportiva, alta bahía e industrial profesionales. Desarrollados en Pekín desde 2007, con la confianza de más de 50 países.",
        de="SolarOne entwickelt und fertigt professionelle LED-Sport-, High-Bay- und Industriebeleuchtungssysteme. In Peking seit 2007 entwickelt, weltweit in über 50 Ländern vertraut.",
        ru="SolarOne проектирует и производит профессиональные системы светодиодного спортивного, высокого пролёта и промышленного освещения. Разработаны в Пекине с 2007 года, доверие более чем 50 стран.",
        ar="تصمم SolarOne وتصنع أنظمة إضاءة رياضية وصناعية وعالية احترافية بتقنية LED. صُممت في بكين منذ 2007، وتحظى بثقة أكثر من 50 دولة.",
        note="home.html meta description",
    ),
    dict(
        key="template.about_meta",
        en="Learn about SolarOne, a professional LED lighting manufacturer since 2007. Specializing in sports lighting, high bay, roadway, and industrial lighting solutions for 50+ countries.",
        fr="Découvrez SolarOne, fabricant d'éclairage LED professionnel depuis 2007. Spécialiste de l'éclairage sportif, haute baie, routier et industriel pour plus de 50 pays.",
        es="Conozca SolarOne, fabricante de iluminación LED profesional desde 2007. Especialistas en iluminación deportiva, alta bahía, vial e industrial para más de 50 países.",
        de="Lernen Sie SolarOne kennen, professioneller LED-Beleuchtungshersteller seit 2007. Spezialisiert auf Sport-, High-Bay-, Straßen- und Industriebeleuchtung für über 50 Länder.",
        ru="Узнайте о SolarOne — профессиональном производителе светодиодного освещения с 2007 года. Специализация: спортивное, высокого пролёта, дорожное и промышленное освещение для более чем 50 стран.",
        ar="تعرّف على SolarOne، مصنّع إضاءة LED احترافي منذ 2007. متخصصون في الإضاءة الرياضية والعالية والطرقية والصناعية لأكثر من 50 دولة.",
        note="about.html meta description",
    ),
    dict(
        key="template.contact_meta",
        en="Contact SolarOne's engineering team for professional LED lighting solutions. Get a full photometric proposal within 48 hours. Beijing, China headquarters.",
        fr="Contactez l'équipe d'ingénierie de SolarOne pour des solutions d'éclairage LED professionnelles. Recevez une proposition photométrique complète sous 48 heures. Siège à Pékin, Chine.",
        es="Contacte con el equipo de ingeniería de SolarOne para soluciones de iluminación LED profesionales. Reciba una propuesta fotométrica completa en 48 horas. Sede en Pekín, China.",
        de="Kontaktieren Sie das SolarOne-Engineering-Team für professionelle LED-Beleuchtungslösungen. Erhalten Sie ein vollständiges photometrisches Angebot innerhalb von 48 Stunden. Hauptsitz Peking, China.",
        ru="Свяжитесь с инженерной командой SolarOne за профессиональными решениями светодиодного освещения. Получите полное фотометрическое предложение в течение 48 часов. Штаб-квартира в Пекине, Китай.",
        ar="تواصل مع فريق هندسة SolarOne لحلول إضاءة LED احترافية. احصل على مقترح فوتومتري كامل خلال 48 ساعة. المقر الرئيسي في بكين، الصين.",
        note="contact.html meta description",
    ),
    dict(
        key="template.news_meta",
        en="Latest news, product launches, and insights from SolarOne. Stay updated on LED lighting innovations and the latest industry developments.",
        fr="Dernières actualités, lancements de produits et analyses de SolarOne. Restez informé des innovations en éclairage LED et des dernières avancées du secteur.",
        es="Últimas noticias, lanzamientos de productos y análisis de SolarOne. Manténgase al día con las innovaciones en iluminación LED y la evolución del sector.",
        de="Neueste Nachrichten, Produkteinführungen und Einblicke von SolarOne. Bleiben Sie über LED-Beleuchtungsinnovationen und Branchenentwicklungen auf dem Laufenden.",
        ru="Последние новости, запуски продуктов и аналитика от SolarOne. Следите за инновациями в светодиодном освещении и последними отраслевыми событиями.",
        ar="أحدث الأخبار وإطلاقات المنتجات ورؤى SolarOne. ابقَ على اطلاع بابتكارات إضاءة LED وأحدث تطورات القطاع.",
        note="news.html meta description",
    ),
    dict(
        key="template.products_meta",
        en="Explore SolarOne's range of LED lighting products: sports lighting, flood lighting, high bay, roadway, and area lighting. Precision optics, modular architecture, field-proven reliability.",
        fr="Découvrez la gamme de produits d'éclairage LED SolarOne : éclairage sportif, projecteurs, haute baie, routier et d'aire. Optiques de précision, architecture modulaire, fiabilité éprouvée sur le terrain.",
        es="Explore la gama de productos de iluminación LED de SolarOne: iluminación deportiva, de proyectores, alta bahía, vial y de área. Óptica de precisión, arquitectura modular, fiabilidad probada.",
        de="Entdecken Sie das Sortiment der LED-Beleuchtungsprodukte von SolarOne: Sportbeleuchtung, Flutlicht, High-Bay, Straßen- und Arealbeleuchtung. Präzisionsoptik, modulare Architektur, bewährte Zuverlässigkeit.",
        ru="Изучите ассортимент продукции светодиодного освещения SolarOne: спортивное, прожекторное, высокого пролёта, дорожное и локальное освещение. Прецизионная оптика, модульная архитектура, проверенная надёжность.",
        ar="استكشف تشكيلة منتجات إضاءة LED من SolarOne: إضاءة رياضية، فيضانية، عالية، طرقية، ومكانية. بصريات دقيقة، وبنية معيارية، وموثوقية مثبتة ميدانياً.",
        note="products.html meta description",
    ),
    dict(
        key="template.projects_meta",
        en="Browse SolarOne's portfolio of 500+ LED lighting projects across 50+ countries. Sports venues, airports, seaports, and industrial facilities worldwide.",
        fr="Parcourez le portefeuille de plus de 500 projets d'éclairage LED SolarOne dans plus de 50 pays. Installations sportives, aéroports, ports maritimes et sites industriels dans le monde entier.",
        es="Explore el portfolio de más de 500 proyectos de iluminación LED de SolarOne en más de 50 países. Instalaciones deportivas, aeropuertos, puertos marítimos y centros industriales en todo el mundo.",
        de="Durchstöbern Sie das Portfolio von über 500 LED-Beleuchtungsprojekten von SolarOne in mehr als 50 Ländern. Sportstätten, Flughäfen, Seehäfen und Industrieanlagen weltweit.",
        ru="Изучите портфолио из более чем 500 проектов светодиодного освещения SolarOne в более чем 50 странах. Спортивные объекты, аэропорты, морские порты и промышленные предприятия по всему миру.",
        ar="تصفّح محفظة SolarOne التي تضم أكثر من 500 مشروع إضاءة LED في أكثر من 50 دولة. منشآت رياضية ومطارات وموانئ ومنشآت صناعية حول العالم.",
        note="projects.html meta description",
    ),
]


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows -> {OUT}")


if __name__ == "__main__":
    main()
