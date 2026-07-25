import os
import sys
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static files directly on Vercel
# Vercel's Python runtime can read the source static/ directory,
# so we serve from STATICFILES_DIRS (not collectstatic output)
import whitenoise

# Find the first available static files directory
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

# Seed database on Vercel (ephemeral SQLite — repopulate on each cold start)
_seed_done = False

# Fields that are ImageField — need special handling (can't create with a string path directly)
_IMAGE_FIELDS = {
    'Product': ['image'],
    'Project': ['image'],
    'SiteConfig': ['hero_background', 'logo', 'og_image'],
}

def _seed_model(Model, items, model_name):
    """Create model instances, handling ImageFields by setting them via update() after create."""
    img_fields = _IMAGE_FIELDS.get(model_name, [])
    for item in items:
        # Separate image fields from regular fields
        img_values = {}
        clean_item = {}
        for k, v in item.items():
            if k in img_fields:
                img_values[k] = v
            else:
                clean_item[k] = v

        obj = Model.objects.create(**clean_item)

        # Set ImageField paths via update() (bypasses file existence check)
        if img_values:
            Model.objects.filter(pk=obj.pk).update(**img_values)

def _seed_database():
    """Ensure DB tables exist and seed data if empty (for Vercel ephemeral SQLite)."""
    global _seed_done
    if _seed_done:
        return
    _seed_done = True

    _logger = logging.getLogger(__name__)

    # Ensure database tables exist (Vercel starts with empty /tmp SQLite)
    try:
        from django.core.management import call_command
        call_command('migrate', '--run-syncdb', verbosity=0)
    except Exception as e:
        _logger.warning('Migration failed: %s', e)

    # Load seed data if database is empty
    seed_path = os.path.join(BASE_DIR, 'seed_data.json')
    if not os.path.isfile(seed_path):
        return

    try:
        from pages.models import Product, Project, SiteConfig

        # Skip if data already exists
        if Product.objects.exists() or Project.objects.exists() or SiteConfig.objects.exists():
            return

        with open(seed_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Seed SiteConfig
        cfg = data.get('siteconfig', {})
        if cfg and not SiteConfig.objects.exists():
            _seed_model(SiteConfig, [cfg], 'SiteConfig')
            _logger.info('Seeded SiteConfig from seed_data.json')

        # Seed Products
        products = data.get('products', [])
        if products:
            _seed_model(Product, products, 'Product')
            _logger.info('Seeded %d products from seed_data.json', len(products))

        # Seed Projects
        projects = data.get('projects', [])
        if projects:
            _seed_model(Project, projects, 'Project')
            _logger.info('Seeded %d projects from seed_data.json', len(projects))

    except Exception as e:
        _logger.warning('Failed to seed database: %s', e)

_seed_database()
