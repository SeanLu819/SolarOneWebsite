"""Update seed_data.py and seed_data.json to use clean (no-hash) image paths
that match the static/ directory layout produced by _full_image_sync.py.
"""
import os
import re
import sys
import json
import django
from pathlib import Path

BASE = Path(r'e:\Python\PROJECT\website')
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
django.setup()

from pages.models import Project, ProjectImage, Product, ProductImage

HASH_SUFFIX_RE = re.compile(r'_[A-Za-z0-9_-]{6,}(?=\.[^.]+$)')


def clean_name(name: str) -> str:
    return HASH_SUFFIX_RE.sub('', name)


# ---------------------------------------------------------------------------
# Build expected static paths from DB
# ---------------------------------------------------------------------------

projects_data = {}
for p in Project.objects.all().order_by('id'):
    main = ''
    if p.image and p.image.name:
        if p.image.name.startswith('images/'):
            main = p.image.name
        else:
            main = f'images/processed/{clean_name(Path(p.image.name).name)}'
    gallery = []
    for pi in p.images.all().order_by('id'):
        if not pi.image:
            continue
        gallery.append(f'images/projects/gallery/{clean_name(Path(pi.image.name).name)}')
    translations = {}
    for lang, t in (p.translations or {}).items():
        translations[lang] = {
            'title': t.get('title', ''),
            'description': t.get('description', ''),
            'location': t.get('location', ''),
            'results': t.get('results', ''),
        }
    projects_data[p.slug] = {
        'pk': p.pk,
        'title': p.title,
        'location': p.location,
        'venue_type': p.venue_type,
        'sport_type': p.sport_type,
        'description': p.description,
        'results': p.results,
        'image': main,
        'order': p.order,
        'gallery': gallery,
        'translations': translations,
    }

products_data = {}
for p in Product.objects.all().order_by('id'):
    main = ''
    if p.image and p.image.name:
        main = f'images/products/{p.slug}/{clean_name(Path(p.image.name).name)}'
    banner = ''
    if p.banner_image and p.banner_image.name:
        banner = f'images/products/{p.slug}/{clean_name(Path(p.banner_image.name).name)}'
    dim = ''
    if p.dimension_image and p.dimension_image.name:
        dim = f'images/products/{p.slug}/{clean_name(Path(p.dimension_image.name).name)}'
    beam = ''
    if p.beam_angle_image and p.beam_angle_image.name:
        beam = f'images/products/{p.slug}/{clean_name(Path(p.beam_angle_image.name).name)}'
    gallery = []
    for pi in p.images.all().order_by('id'):
        if not pi.image:
            continue
        gallery.append(f'images/products/{p.slug}/{clean_name(Path(pi.image.name).name)}')
    products_data[p.slug] = {
        'pk': p.pk,
        'name': p.name,
        'category': p.category,
        'description': p.description,
        'image': main,
        'banner_image': banner,
        'dimension_image': dim,
        'beam_angle_image': beam,
        'gallery': gallery,
        'order': p.order,
        'parent_slug': p.parent.slug if p.parent else '',
    }

print('=' * 80)
print('PROJECTS — main image + gallery from DB')
print('=' * 80)
for slug, data in projects_data.items():
    print(f"{slug:45s} main={data['image']}")
    for g in data['gallery']:
        print(f"    gallery: {g}")

print()
print('=' * 80)
print('PRODUCTS — image/banner/dim/beam from DB')
print('=' * 80)
for slug, data in products_data.items():
    print(f"{slug:30s}")
    for fld in ('image', 'banner_image', 'dimension_image', 'beam_angle_image'):
        if data[fld]:
            print(f"  {fld:18s}: {data[fld]}")
    if data['gallery']:
        for g in data['gallery']:
            print(f"  gallery: {g}")

# Save to JSON for reference
out_json = BASE / '_db_image_paths.json'
out_json.write_text(json.dumps({'projects': projects_data, 'products': products_data}, indent=2), encoding='utf-8')
print(f'\nSaved DB-mapped paths to {out_json}')
