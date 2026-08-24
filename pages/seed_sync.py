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


def _resolve_static_path(db_path, slug, asset_type='products', field_name=''):
    """Resolve a DB upload path to the canonical static path.

    DB stores something like 'products/banners/fl1m-bar-1_abcX123.webp'
    We want: 'images/products/fl1m/fl1m-bar-1.webp'

    When field_name is 'image' (product card image) and the DB path
    looks like a banner ('bar'/'banner' in name), prefer non-banner files
    in the slug directory. This prevents banner images from leaking into
    the product card image slot.
    """
    if not db_path:
        return ''
    db_path = str(db_path).replace('\\', '/')
    raw_filename = os.path.basename(db_path)
    clean_filename = _strip_hash_suffix(raw_filename)

    is_banner_like = any(kw in clean_filename.lower() for kw in ('bar', 'banner', 'barnner'))

    candidates = []
    if field_name == 'image' and is_banner_like:
        dir_path = f'images/{asset_type}/{slug}/'
        files_in_dir = _list_static_dir(dir_path)
        non_banner = [f for f in files_in_dir
                      if not any(kw in f.lower() for kw in ('bar', 'banner', 'barnner', '3d-view', 'dimension', 'beamangle', 'ordering', 'cert'))]
        if non_banner:
            non_banner.sort(key=lambda f: (0 if clean_filename.split('.')[0].lower() in f.lower() else 1, f))
            candidates.append(f'{dir_path}{non_banner[0]}')
        candidates.extend([
            f'images/{asset_type}/{slug}/{clean_filename}',
            f'images/{asset_type}/{slug}/{raw_filename}',
            f'images/{asset_type}/{clean_filename}',
            f'images/{asset_type}/{raw_filename}',
            f'images/{db_path}',
        ])
    else:
        candidates = [
            f'images/{asset_type}/{slug}/{clean_filename}',
            f'images/{asset_type}/{slug}/{raw_filename}',
            f'images/{asset_type}/{clean_filename}',
            f'images/{asset_type}/{raw_filename}',
            f'images/{db_path}',
        ]

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _static_file_exists(candidate):
            return candidate

    return f'images/{asset_type}/{slug}/{clean_filename}'


def _list_static_dir(rel_dir):
    """List files in a static directory (cached)."""
    import os
    results = []
    try:
        from django.conf import settings
        dirs_to_check = []
        static_root = str(getattr(settings, 'STATIC_ROOT', ''))
        if static_root:
            dirs_to_check.append(os.path.join(static_root, rel_dir))
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            dirs_to_check.append(os.path.join(str(d), rel_dir))
    except Exception:
        dirs_to_check = [os.path.join('static', rel_dir)]

    for d in dirs_to_check:
        if os.path.isdir(d):
            try:
                for f in os.listdir(d):
                    if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                        results.append(f)
                break
            except OSError:
                pass
    return results


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
        resolved_images[field] = _resolve_static_path(fname, slug, 'products', field_name=field) if fname else ''

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


def _resolve_project_pdf(project, base_dir=None):
    """Resolve the PDF URL for a project.

    Priority:
    1. project.pdf_static (explicit static path set in admin)
    2. project.pdf_file (uploaded file, resolve to static if copied)
    3. Auto-discover in static/files/ using slug-based naming
    """
    slug = getattr(project, 'slug', '')
    if not slug:
        return ''

    # 1. Explicit pdf_static field
    pdf_static = getattr(project, 'pdf_static', '') or ''
    if pdf_static:
        return pdf_static

    # 2. Uploaded pdf_file - check if it exists in static files dir
    pdf_file = getattr(project, 'pdf_file', None)
    if pdf_file and getattr(pdf_file, 'name', ''):
        fname = os.path.basename(pdf_file.name)
        candidate = f'files/{fname}'
        if _static_file_exists(candidate, base_dir):
            return candidate

    # 3. Auto-discover: slug_underscored.pdf in files/
    auto_name = slug.replace('-', '_') + '.pdf'
    candidate = f'files/{auto_name}'
    if _static_file_exists(candidate, base_dir):
        return candidate

    return ''


def _project_to_dict(project):
    """Convert a Project model instance to a seed dict with ALL fields."""
    slug = project.slug

    img = getattr(project, 'image', None)
    image_path = ''
    if img and getattr(img, 'name', ''):
        image_path = _resolve_static_path(img.name, slug, 'projects')

    gallery = _project_gallery_paths(project)
    pdf_url = _resolve_project_pdf(project)

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
        'pdf_url': pdf_url,
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


def _discover_project_cover(slug, seed_image='', base_dir=None):
    """Find the best cover image for a project, mirroring _find_project_cover_path logic.

    Priority:
    1. Per-slug directory (first image, excluding old/new comparison shots)
    2. images/processed/ fallback for known legacy placeholders
    3. Gallery directory match by slug token
    4. Flat projects/ directory
    """
    import os

    def _list_dir(rel_dir):
        rel_dir = rel_dir.replace('\\', '/')
        full_dir = None
        # Check in each static dir
        if base_dir:
            for sub in ['static', 'staticfiles', 'public/static']:
                d = os.path.join(base_dir, sub, rel_dir)
                if os.path.isdir(d):
                    full_dir = d
                    break
        if not full_dir:
            return []
        try:
            return [f for f in os.listdir(full_dir)
                    if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif'))]
        except OSError:
            return []

    slug_dir = f'images/projects/{slug}'
    slug_files = _list_dir(slug_dir)
    exclude = {'old-hid-lighting.webp', 'new-led-lighting.webp'}

    if slug_files:
        slug_files_sorted = sorted(slug_files)
        # Skip excluded files, pick first valid image
        for f in slug_files_sorted:
            if f.lower() not in exclude:
                return f'{slug_dir}/{f}'

    # Legacy processed/ fallback
    name = os.path.basename(seed_image) if seed_image else ''
    if name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        processed = f'images/processed/{name}'
        if _static_file_exists(processed, base_dir):
            return processed

    # Gallery directory fallback
    gallery_files = _list_dir('images/projects/gallery')
    if gallery_files:
        slug_tokens = set(slug.replace('-', ' ').lower().split())
        for f in sorted(gallery_files):
            f_lower = f.lower()
            if any(tok in f_lower for tok in slug_tokens if len(tok) > 3):
                return f'images/projects/gallery/{f}'

    return seed_image  # keep original as last resort


def sync_seed_from_json(base_dir=None):
    """JSON → Python sync. Reads seed_data.json, writes pages/seed_data.py.

    Used by build.sh on Vercel where there's no DB.
    Also validates image paths and prints warnings for missing files.
    Auto-discovers PDF files and fixes project cover paths.
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

    # Auto-discover PDF files for projects with empty pdf_url
    pdf_discovered = 0
    for p in seed_data.get('projects', []):
        if not p.get('pdf_url', ''):
            slug = p.get('slug', '')
            auto_name = slug.replace('-', '_') + '.pdf'
            candidate = f'files/{auto_name}'
            if _static_file_exists(candidate, base_dir):
                p['pdf_url'] = candidate
                pdf_discovered += 1

    # Auto-fix project cover paths that don't resolve
    covers_fixed = 0
    for p in seed_data.get('projects', []):
        current = p.get('image', '')
        if current and not _static_file_exists(current, base_dir):
            slug = p.get('slug', '')
            new_path = _discover_project_cover(slug, current, base_dir)
            if new_path and new_path != current and _static_file_exists(new_path, base_dir):
                p['image'] = new_path
                covers_fixed += 1

    # Validate image + PDF paths (informational)
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
        if p.get('pdf_url') and not _static_file_exists(p['pdf_url'], base_dir):
            missing.append(f"  project {p['slug']}.pdf_url: {p['pdf_url']}")

    if missing:
        print(f'[seed_sync] WARNING: {len(missing)} path(s) not found in static/:')
        for m in missing[:20]:
            print(m)
        if len(missing) > 20:
            print(f'  ... and {len(missing) - 20} more')

    if pdf_discovered:
        print(f'[seed_sync] Auto-discovered {pdf_discovered} PDF file(s) for projects')
    if covers_fixed:
        print(f'[seed_sync] Fixed {covers_fixed} project cover image path(s)')

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