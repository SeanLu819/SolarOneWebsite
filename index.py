import os
import sys
import json
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static files directly on Vercel
import whitenoise

_serve_root = None
for d in settings.STATICFILES_DIRS:
    _d = str(d)
    if os.path.isdir(_d):
        _serve_root = _d
        break

if _serve_root:
    application = whitenoise.WhiteNoise(application, root=_serve_root, autorefresh=False, prefix='static/')
else:
    _sr = str(settings.STATIC_ROOT)
    if os.path.isdir(_sr):
        application = whitenoise.WhiteNoise(application, root=_sr, autorefresh=False, prefix='static/')

# ---- Seed database on Vercel (ephemeral SQLite — repopulate on each cold start) ----
_seed_done = False

def _seed_database():
    """Ensure DB tables exist and seed data if empty (for Vercel ephemeral SQLite)."""
    global _seed_done
    if _seed_done:
        return
    _seed_done = True

    logger = logging.getLogger('index.seed')

    # 1. Ensure database tables exist
    try:
        from django.core.management import call_command
        call_command('migrate', '--run-syncdb', verbosity=0)
        logger.info('Database migration complete')
    except Exception as e:
        logger.warning('Migration error: %s', e, exc_info=True)

    # 2. Read seed data
    seed_path = os.path.join(BASE_DIR, 'seed_data.json')
    if not os.path.isfile(seed_path):
        logger.warning('seed_data.json not found at %s', seed_path)
        return

    with open(seed_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 3. Check if already seeded
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM pages_product")
        product_count = cursor.fetchone()[0]

    if product_count > 0:
        logger.info('Database already has %d products, skipping seed', product_count)
        return

    # 4. Seed using raw SQL (bypasses ImageField validation entirely)
    try:
        with connection.cursor() as cursor:
            # --- Seed SiteConfig ---
            cfg = data.get('siteconfig', {})
            if cfg:
                cursor.execute("""
                    INSERT INTO pages_siteconfig
                        (hero_title, hero_subtitle, hero_background, stat_projects, stat_projects_label,
                         stat_countries, stat_countries_label, stat_energy, stat_energy_label,
                         stat_support, stat_support_label, about_title, about_text_1, about_text_2,
                         about_stat_years, about_stat_years_label, about_stat_projects, about_stat_projects_label,
                         about_stat_countries, about_stat_countries_label, about_stat_clients, about_stat_clients_label,
                         products_title, products_subtitle, projects_title, projects_subtitle,
                         contact_title, contact_subtitle, contact_email, contact_phone_1, contact_phone_2,
                         contact_whatsapp, contact_address, social_facebook, social_instagram,
                         social_youtube, social_tiktok, social_linkedin, footer_description,
                         brand_name, logo, meta_title, meta_description, og_image,
                         font_family_body, font_family_heading, font_size_base, font_size_nav,
                         font_size_hero_title, font_size_hero_subtitle, font_size_section_title,
                         font_size_body, font_size_card_title, font_size_card_desc, accent_color)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, [
                    cfg.get('hero_title', ''), cfg.get('hero_subtitle', ''), cfg.get('hero_background', ''),
                    cfg.get('stat_projects', '500+'), cfg.get('stat_projects_label', 'Projects'),
                    cfg.get('stat_countries', '50+'), cfg.get('stat_countries_label', 'Countries'),
                    cfg.get('stat_energy', '60%'), cfg.get('stat_energy_label', 'Energy Save'),
                    cfg.get('stat_support', '24/7'), cfg.get('stat_support_label', 'Support'),
                    cfg.get('about_title', ''), cfg.get('about_text_1', ''), cfg.get('about_text_2', ''),
                    cfg.get('about_stat_years', ''), cfg.get('about_stat_years_label', ''),
                    cfg.get('about_stat_projects', ''), cfg.get('about_stat_projects_label', ''),
                    cfg.get('about_stat_countries', ''), cfg.get('about_stat_countries_label', ''),
                    cfg.get('about_stat_clients', ''), cfg.get('about_stat_clients_label', ''),
                    cfg.get('products_title', ''), cfg.get('products_subtitle', ''),
                    cfg.get('projects_title', ''), cfg.get('projects_subtitle', ''),
                    cfg.get('contact_title', ''), cfg.get('contact_subtitle', ''),
                    cfg.get('contact_email', ''), cfg.get('contact_phone_1', ''),
                    cfg.get('contact_phone_2', ''), cfg.get('contact_whatsapp', ''),
                    cfg.get('contact_address', ''), cfg.get('social_facebook', ''),
                    cfg.get('social_instagram', ''), cfg.get('social_youtube', ''),
                    cfg.get('social_tiktok', ''), cfg.get('social_linkedin', ''),
                    cfg.get('footer_description', ''), cfg.get('brand_name', 'SolarOne'),
                    cfg.get('logo', ''), cfg.get('meta_title', ''), cfg.get('meta_description', ''),
                    cfg.get('og_image', ''), cfg.get('font_family_body', ''),
                    cfg.get('font_family_heading', ''), cfg.get('font_size_base', ''),
                    cfg.get('font_size_nav', ''), cfg.get('font_size_hero_title', ''),
                    cfg.get('font_size_hero_subtitle', ''), cfg.get('font_size_section_title', ''),
                    cfg.get('font_size_body', ''), cfg.get('font_size_card_title', ''),
                    cfg.get('font_size_card_desc', ''), cfg.get('accent_color', ''),
                ])
                logger.info('Seeded SiteConfig via raw SQL')

            # --- Seed Products ---
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            for item in data.get('products', []):
                cursor.execute("""
                    INSERT INTO pages_product
                        (name, category, slug, description, power, efficacy, protection,
                         output, beam_angle, image, "order", translations, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, [
                    item.get('name', ''), item.get('category', ''), item.get('slug', ''),
                    item.get('description', ''), item.get('power', ''), item.get('efficacy', ''),
                    item.get('protection', ''), item.get('output', ''), item.get('beam_angle', ''),
                    item.get('image', ''), item.get('order', 0),
                    json.dumps(item.get('translations', {})), now,
                ])
            product_count = len(data.get('products', []))
            if product_count:
                logger.info('Seeded %d products via raw SQL', product_count)

            # --- Seed Projects ---
            for item in data.get('projects', []):
                cursor.execute("""
                    INSERT INTO pages_project
                        (title, location, slug, venue_type, sport_type, description,
                         results, image, "order", translations, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, [
                    item.get('title', ''), item.get('location', ''), item.get('slug', ''),
                    item.get('venue_type', ''), item.get('sport_type', ''),
                    item.get('description', ''), item.get('results', ''),
                    item.get('image', ''), item.get('order', 0),
                    json.dumps(item.get('translations', {})), now,
                ])
            project_count = len(data.get('projects', []))
            if project_count:
                logger.info('Seeded %d projects via raw SQL', project_count)

    except Exception as e:
        logger.warning('Seed error: %s', e, exc_info=True)

_seed_database()
