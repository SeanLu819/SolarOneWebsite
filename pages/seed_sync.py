"""
Unified seed data sync tool — the single source of truth for generating
seed_data.json and pages/seed_data.py.

Supports two modes:
  1. DB mode (default):  Read from database, merge with existing seed image paths,
                        write both JSON and Python output.
                        Used by Django admin save_model / save_formset hooks.

  2. JSON mode:         Read from seed_data.json, write pages/seed_data.py.
                        Used by build.sh on Vercel (no DB available).

ALL product and project fields are handled — no more missing fields.
Image paths are always resolved against static/ so the seed contains
canonical paths like 'images/products/fl1m/fl1m-01.webp'.
"""
import json
import os
import re
import copy
import sys


def _strip_hash_suffix(filename):
    """Strip Django upload hash suffix like _abcX123 from a filename."""
    if not filename:
        return ''
    stem, ext = os.path.splitext(filename)
    m = re.search(r'_([a-zA-Z0-9]{7})$', stem)
    if m:
        return f'{stem[:m.start()]}{ext}'
    return filename


def _resolve_static_path(db_path, slug, asset_type='products'):
    """Resolve a DB upload path to the canonical static path.

    DB stores something like 'products/banners/fl1m-bar-1_abcX123.webp'
    We want: 'images/products/fl1m/fl1m-bar-1.webp'

    Strategy: try the most specific path first (per-slug dir, clean name),
    then fall back to progressively broader candidates.
    """
    if not db_path:
        return ''
    db_path = str(db_path).replace('\\', '/')
    raw_filename = os.path.basename(db_path)
    clean_filename = _strip_hash_suffix(raw_filename)

    candidates = [
        # Best: per-slug directory, clean filename
        f'images/{asset_type}/{slug}/{clean_filename}',
        # Per-slug directory, raw filename (with hash)
        f'images/{asset_type}/{slug}/{raw_filename}',
        # Flat products/ dir, clean filename
        f'images/{asset_type}/{clean_filename}',
        # Flat products/ dir, raw filename
        f'images/{asset_type}/{raw_filename}',
        # Direct images/ prefix
        f'images/{db_path}',
    ]

    for candidate in candidates:
        if _static_file_exists(candidate):
            return candidate

    # Fallback: return the most likely path (per-slug, clean name)
    return f'images/{asset_type}/{slug}/{clean_filename}'


_static_cache = None
_static_cache_base = None


def _static_file_exists(rel_path, base_dir=None):
    """Check if a file exists in any static directory (cached)."""
    global _static_cache, _static_cache_base
    if _static_cache is None or _static_cache_base != base_dir:
        _static_cache = _build_static_set(base_dir)
        _static_cache_base = base_dir
    return rel_path in _static_cache


def _build_static_set(base_dir=None):
    """Build a set of all static file paths.

    Works with or without Django:
    - With Django: uses STATIC_ROOT + STATICFILES_DIRS
    - Without Django: looks for ./static/ and ./staticfiles/ relative to base_dir
    """
    file_set = set()
    dirs = []

    try:
        from django.conf import settings
        static_root = str(getattr(settings, 'STATIC_ROOT', ''))
        if static_root and os.path.isdir(static_root):
            dirs.append(static_root)
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            d = str(d)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)
    except Exception:
        # No Django — scan standard directories relative to base_dir
        if base_dir is None:
            base_dir = os.getcwd()
        for subdir in ['static', 'staticfiles', 'public/static']:
            d = os.path.join(base_dir, subdir)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)

    for base in dirs:
        for root, _, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base).replace('\\', '/')
                file_set.add(rel)
    return file_set


def _product_gallery_paths(product):
    """Return list of canonical static paths for a product's gallery images."""
    paths = []
    try:
        for img in product.images.all().order_by('order', 'pk'):
            fname = getattr(img.image, 'name', '')
            if fname:
                resolved = _resolve_static_path(fname, product.slug, 'products')
                if resolved and resolved not in paths:
                    paths.append(resolved)
    except Exception:
        pass
    return paths


def _project_gallery_paths(project):
    """Return list of canonical static paths for a project's gallery images."""
    paths = []
    try:
        for img in project.images.all().order_by('order', 'pk'):
            fname = getattr(img.image, 'name', '')
            if fname:
                resolved = _resolve_static_path(fname, project.slug, 'projects')
                if resolved and resolved not in paths:
                    paths.append(resolved)
    except Exception:
        pass
    return paths


def _product_to_dict(product):
    """Convert a Product model instance to a seed dict with ALL fields."""
    slug = product.slug

    # Resolve all image fields
    image_fields = [
        'image', 'banner_image', 'dimension_image',
        'beam_angle_image', 'ordering_image', 'cert_image',
    ]
    resolved_images = {}
    for field in image_fields:
        f = getattr(product, field, None)
        fname = getattr(f, 'name', '') if f else ''
        resolved_images[field] = _resolve_static_path(fname, slug, 'products') if fname else ''

    gallery = _product_gallery_paths(product)

    return {
        'pk': product.pk,
        'name': product.name,
        'slug': slug,
        'category': product.category,
        'description': product.description,
        'power': product.power or '',
        'efficacy': product.efficacy or '',
        'output': product.output or '',
        'beam_angle': product.beam_angle or '',
        'protection': product.protection or '',
        'image': resolved_images['image'],
        'banner_image': resolved_images['banner_image'],
        'dimension_image': resolved_images['dimension_image'],
        'beam_angle_image': resolved_images['beam_angle_image'],
        'ordering_image': resolved_images['ordering_image'],
        'cert_image': resolved_images['cert_image'],
        'order': product.order,
        'parent_slug': product.parent.slug if product.parent else '',
        'translations': product.translations if isinstance(product.translations, dict) else {},
        'gallery': gallery,
        'specs': product.specs if isinstance(product.specs, list) else [],
        'energy_data': product.energy_data if isinstance(product.energy_data, list) else [],
        'model_number': product.model_number or '',
        'ordering_info': product.ordering_info if isinstance(product.ordering_info, list) else [],
    }


def _project_to_dict(project):
    """Convert a Project model instance to a seed dict with ALL fields."""
    slug = project.slug

    img = getattr(project, 'image', None)
    image_path = ''
    if img and getattr(img, 'name', ''):
        image_path = _resolve_static_path(img.name, slug, 'projects')

    gallery = _project_gallery_paths(project)

    return {
        'pk': project.pk,
        'title': project.title,
        'location': project.location,
        'slug': slug,
        'venue_type': project.venue_type,
        'sport_type': project.sport_type,
        'description': project.description,
        'results': project.results or '',
        'image': image_path,
        'order': project.order,
        'translations': project.translations if isinstance(project.translations, dict) else {},
        'gallery': gallery,
        'pdf_url': getattr(project, 'pdf_url', '') or '',
    }


def _write_seed_files(seed_data, base_dir=None):
    """Write seed_data.json and pages/seed_data.py from a seed dict."""
    if base_dir is None:
        try:
            from django.conf import settings
            base_dir = str(settings.BASE_DIR)
        except Exception:
            base_dir = os.getcwd()

    json_path = os.path.join(base_dir, 'seed_data.json')
    py_path = os.path.join(base_dir, 'pages', 'seed_data.py')

    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    # Write Python module
    lines = [
        '"""Seed data embedded as Python module for Vercel compatibility.',
        '',
        'On Vercel, non-Python files (like seed_data.json) are not automatically included',
        'in the serverless function bundle. Embedding the data here ensures it is always',
        'available via a normal Python import.',
        '"""',
        '',
        'SEED_DATA = ' + json.dumps(seed_data, ensure_ascii=False, indent=2),
        '',
    ]
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return json_path, py_path


def sync_seed_from_db():
    """Full DB → seed sync. Reads all products + projects from DB,
    resolves image paths against static/, writes both JSON and Python.

    This is the authoritative sync — called from Django admin hooks.
    Returns True on success, False on failure.
    """
    try:
        from pages.models import Product, Project

        products = [
            _product_to_dict(p)
            for p in Product.objects.all().order_by('order', 'pk')
        ]
        projects = [
            _project_to_dict(p)
            for p in Project.objects.all().order_by('order', 'pk')
        ]

        seed_data = {
            'products': products,
            'projects': projects,
            'siteconfig': {},
        }

        json_path, py_path = _write_seed_files(seed_data)

        product_count = len(products)
        project_count = len(projects)
        gallery_count = sum(len(p['gallery']) for p in products)
        print(f'[seed_sync] DB → seed: {product_count} products ({gallery_count} gallery images), {project_count} projects')
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to sync seed from DB: {e}', exc_info=True)
        return False


def sync_seed_from_json(base_dir=None):
    """JSON → Python sync. Reads seed_data.json, writes pages/seed_data.py.

    Used by build.sh on Vercel where there's no DB.
    Also validates image paths and prints warnings for missing files.
    Returns True on success, False on failure.
    """
    if base_dir is None:
        base_dir = os.getcwd()

    json_path = os.path.join(base_dir, 'seed_data.json')
    if not os.path.isfile(json_path):
        print(f'[seed_sync] ERROR: {json_path} not found')
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            seed_data = json.load(f)
    except Exception as e:
        print(f'[seed_sync] ERROR reading JSON: {e}')
        return False

    # Validate image paths (informational)
    missing = []
    for p in seed_data.get('products', []):
        for field in ['image', 'banner_image', 'dimension_image', 'beam_angle_image', 'ordering_image', 'cert_image']:
            val = p.get(field, '')
            if val and not _static_file_exists(val, base_dir):
                missing.append(f"  product {p['slug']}.{field}: {val}")
        for g in p.get('gallery', []):
            if g and not _static_file_exists(g, base_dir):
                missing.append(f"  product {p['slug']} gallery: {g}")

    for p in seed_data.get('projects', []):
        if p.get('image') and not _static_file_exists(p['image'], base_dir):
            missing.append(f"  project {p['slug']}.image: {p['image']}")
        for g in p.get('gallery', []):
            if g and not _static_file_exists(g, base_dir):
                missing.append(f"  project {p['slug']} gallery: {g}")

    if missing:
        print(f'[seed_sync] WARNING: {len(missing)} image path(s) not found in static/:')
        for m in missing[:20]:
            print(m)
        if len(missing) > 20:
            print(f'  ... and {len(missing) - 20} more')

    _write_seed_files(seed_data, base_dir)

    product_count = len(seed_data.get('products', []))
    project_count = len(seed_data.get('projects', []))
    print(f'[seed_sync] JSON → seed: {product_count} products, {project_count} projects')
    return True


# Backward-compatible alias (admin.py calls sync_seed_data())
sync_seed_data = sync_seed_from_db


if __name__ == '__main__':
    """CLI entry point.

    Usage:
      python pages/seed_sync.py           # DB mode (default, needs Django)
      python pages/seed_sync.py --json    # JSON mode (no Django needed)
    """
    import argparse
    parser = argparse.ArgumentParser(description='Sync seed data')
    parser.add_argument('--json', action='store_true', help='JSON mode: read seed_data.json, write seed_data.py')
    args = parser.parse_args()

    if args.json:
        ok = sync_seed_from_json()
        sys.exit(0 if ok else 1)
    else:
        # DB mode: need Django setup
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
        import django
        django.setup()
        ok = sync_seed_from_db()
        sys.exit(0 if ok else 1)
