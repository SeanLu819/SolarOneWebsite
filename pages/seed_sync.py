"""
Merge-sync database text content into seed_data.py and seed_data.json.

Only updates text fields (description, specs, energy_data, translations,
results) from the database. Image paths, gallery paths, and other static
file references are preserved from the existing seed files, because the
DB stores upload paths like 'products/fl4m-01_abc123.webp' while the seed
files need curated paths like 'images/products/fl4m/fl4m-01.webp'.
"""
import json
import os
import copy
import importlib
from django.conf import settings
from django.contrib.staticfiles import finders


# Fields to sync from DB (text content that changes frequently)
_PRODUCT_TEXT_FIELDS = [
    'description', 'power', 'efficacy', 'output', 'beam_angle',
    'protection', 'specs', 'energy_data', 'translations',
    'ordering_info', 'model_number',
]

_PROJECT_TEXT_FIELDS = [
    'description', 'results', 'translations',
]

# Fields that are image/path references — keep from existing seed
_IMAGE_FIELDS = [
    'image', 'banner_image', 'dimension_image', 'beam_angle_image',
    'gallery', 'pdf_url',
]

# Image fields that can be synced from DB when seed value is empty
_SYNCABLE_IMAGE_FIELDS = [
    'image', 'banner_image', 'dimension_image', 'beam_angle_image',
    'ordering_image',
]


def _find_seed_item(items, slug):
    """Find an item in seed list by slug, return (index, item) or (None, None)."""
    for i, item in enumerate(items):
        if item.get('slug') == slug:
            return i, item
    return None, None


def _resolve_static_path(db_value, slug):
    """Resolve a DB upload path to the correct static path.
    
    DB stores upload paths like 'products/dimensions/fl1m-3d-view.webp'
    but the seed needs curated paths like 'images/products/fl1m/fl1m-3d-view.webp'.
    """
    if not db_value or not slug:
        return db_value
    db_value = db_value.replace('\\', '/')
    filename = db_value.split('/')[-1]
    candidates = [
        f'images/products/{slug}/{filename}',
        f'images/products/{filename}',
        f'images/{db_value}',
    ]
    for candidate in candidates:
        if finders.find(candidate):
            return candidate
        static_root = str(settings.STATIC_ROOT)
        full = os.path.join(static_root, candidate)
        if os.path.isfile(full):
            return candidate
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            full = os.path.join(str(d), candidate)
            if os.path.isfile(full):
                return candidate
    return db_value


def _merge_product(db_product, seed_item):
    """Merge DB text fields into existing seed product item."""
    for field in _PRODUCT_TEXT_FIELDS:
        db_val = getattr(db_product, field, None)
        if db_val is not None:
            seed_item[field] = db_val
    # For image fields, resolve DB upload paths to curated static paths
    for field in _SYNCABLE_IMAGE_FIELDS:
        current = seed_item.get(field, '')
        if not current or not current.startswith('images/'):
            db_field = getattr(db_product, field, None)
            if db_field and getattr(db_field, 'name', ''):
                resolved = _resolve_static_path(db_field.name, db_product.slug)
                seed_item[field] = resolved


def _merge_project(db_project, seed_item):
    """Merge DB text fields into existing seed project item."""
    for field in _PROJECT_TEXT_FIELDS:
        db_val = getattr(db_project, field, None)
        if db_val is not None:
            seed_item[field] = db_val


def sync_seed_data():
    """
    Merge-sync database text content into seed_data.py and seed_data.json.
    Preserves existing image paths and gallery references.
    Returns True on success, False on failure.
    """
    try:
        from pages.models import Product, Project, SiteConfig

        # Load existing seed data to preserve image paths
        seed_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')
        existing_seed = {}
        try:
            # Import the current seed_data module to get existing data
            import importlib
            import pages.seed_data
            importlib.reload(pages.seed_data)
            existing_seed = copy.deepcopy(pages.seed_data.SEED_DATA)
        except Exception:
            pass

        products_seed = existing_seed.get('products', [])
        projects_seed = existing_seed.get('projects', [])
        siteconfig_seed = existing_seed.get('siteconfig', {})

        # Merge products: update text fields from DB, keep image paths from seed
        for product in Product.objects.all().order_by('order'):
            idx, seed_item = _find_seed_item(products_seed, product.slug)
            if idx is not None:
                _merge_product(product, seed_item)
                products_seed[idx] = seed_item
            else:
                # New product not in seed — add it (image paths will be raw DB paths)
                products_seed.append({
                    'pk': product.pk,
                    'name': product.name,
                    'slug': product.slug,
                    'category': product.category,
                    'description': product.description,
                    'power': product.power,
                    'efficacy': product.efficacy,
                    'output': product.output,
                    'beam_angle': product.beam_angle,
                    'protection': product.protection,
                    'image': product.image.name if product.image else '',
                    'banner_image': product.banner_image.name if product.banner_image else '',
                    'dimension_image': product.dimension_image.name if product.dimension_image else '',
                    'beam_angle_image': product.beam_angle_image.name if product.beam_angle_image else '',
                    'ordering_image': product.ordering_image.name if product.ordering_image else '',
                    'order': product.order,
                    'parent_slug': product.parent.slug if product.parent else '',
                    'translations': product.translations if isinstance(product.translations, dict) else {},
                    'gallery': [],
                    'specs': product.specs if isinstance(product.specs, list) else [],
                    'energy_data': product.energy_data if isinstance(product.energy_data, list) else [],
                })

        # Merge projects: update text fields from DB, keep image paths from seed
        for project in Project.objects.all().order_by('order'):
            idx, seed_item = _find_seed_item(projects_seed, project.slug)
            if idx is not None:
                _merge_project(project, seed_item)
                projects_seed[idx] = seed_item
            else:
                # New project not in seed — add it
                projects_seed.append({
                    'pk': project.pk,
                    'title': project.title,
                    'location': project.location,
                    'slug': project.slug,
                    'venue_type': project.venue_type,
                    'sport_type': project.sport_type,
                    'description': project.description,
                    'results': project.results,
                    'image': project.image.name if project.image else '',
                    'order': project.order,
                    'translations': project.translations if isinstance(project.translations, dict) else {},
                    'gallery': [],
                    'pdf_url': '',
                })

        # Build final seed data
        seed_data = {
            'products': products_seed,
            'projects': projects_seed,
            'siteconfig': siteconfig_seed,
        }

        # Write to seed_data.json
        json_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)

        # Write to seed_data.py
        py_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write('"""Seed data embedded as Python module for Vercel compatibility.\n')
            f.write('\n')
            f.write('On Vercel, non-Python files (like seed_data.json) are not automatically included\n')
            f.write('in the serverless function bundle. Embedding the data here ensures it is always\n')
            f.write('available via a normal Python import.\n')
            f.write('"""\n\n')
            f.write('SEED_DATA = ')
            f.write(json.dumps(seed_data, ensure_ascii=False, indent=2))
            f.write('\n')

        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to sync seed data: {e}', exc_info=True)
        return False