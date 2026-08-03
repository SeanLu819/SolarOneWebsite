"""Regenerate seed_data.json and pages/seed_data.py from local SQLite DB.

Maps DB media paths (relative to MEDIA_ROOT) to static file paths so the
Vercel fallback uses files that are actually committed in the repo.
"""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / 'seed_data.json'
PY_PATH = BASE_DIR / 'pages' / 'seed_data.py'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
import django
django.setup()

from pages.models import Product, ProductImage, Project, ProjectImage, SiteConfig


def media_name(field):
    return field.name if field and field.name else ''


def map_product_image(slug: str, db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    if name in ('rt200-m.webp', 'floodlight.webp', 'HB.webp'):
        return f'images/processed/{name}'
    if slug.startswith('vsp'):
        if name.startswith('vsp12m'):
            return f'images/products/vsp12m/{name}'
        return f'images/products/vsp/{name}'
    if slug in ('fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m'):
        return f'images/products/{slug}/{name}'
    if slug == 'm-series' and name == 'rt200-m.webp':
        return 'images/processed/rt200-m.webp'
    if slug == 'rt410-series':
        return 'images/processed/floodlight.webp'
    if slug == 'rt400-series':
        return 'images/processed/HB.webp'
    return f'images/products/{slug}/{name}'


def map_banner_image(slug: str, db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    stem = name.rsplit('.', 1)[0]
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]
    ext = name.rsplit('.', 1)[-1]
    clean_name = f'{stem}.{ext}'
    if slug.startswith('vsp'):
        return 'images/products/vsp/vsp-bar-1.webp'
    if slug in ('fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m'):
        return f'images/products/{slug}/{clean_name}'
    if slug == 'm-series':
        return 'images/products/m-series/m-series-bar-1.webp'
    if slug == 'rt410-series':
        return 'images/products/rt410/rt410-bar-1.webp'
    return f'images/products/{slug}/{clean_name}'


def map_gallery_image(slug: str, db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    stem = name.rsplit('.', 1)[0]
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]
    ext = name.rsplit('.', 1)[-1]
    clean_name = f'{stem}.{ext}'
    if slug.startswith('vsp'):
        if clean_name.lower().startswith('vsp9m-'):
            idx = clean_name.split('-', 1)[1]
            return f'images/products/vsp12m/vsp12m-{idx}'
        if clean_name.lower().startswith('vsp12m-'):
            return f'images/products/vsp12m/{clean_name}'
        return f'images/products/vsp12m/{clean_name}'
    if slug in ('fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m'):
        return f'images/products/{slug}/{clean_name}'
    if slug == 'm-series':
        return f'images/products/m-series/{clean_name}'
    if slug == 'rt410-series':
        return f'images/products/rt410/{clean_name}'
    return f'images/products/{slug}/{clean_name}'


def map_dimension_image(slug: str, db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    if slug in ('fl1m', 'fl4m', 'fl6m', 'fl9m', 'fl12m', 'fl16m'):
        return f'images/products/{slug}/{name}'
    return f'images/products/{slug}/{name}'


def map_project_image(db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    stem = name.rsplit('.', 1)[0]
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]
    ext = name.rsplit('.', 1)[-1]
    clean_name = f'{stem}.{ext}'
    if clean_name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        return f'images/processed/{clean_name}'
    if clean_name in ('home-project.webp',):
        return f'images/{clean_name}'
    return f'images/processed/{clean_name}'


def map_project_gallery(db_path: str) -> str:
    if not db_path:
        return ''
    if db_path.startswith('images/'):
        return db_path
    name = Path(db_path).name
    stem = name.rsplit('.', 1)[0]
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]
    ext = name.rsplit('.', 1)[-1]
    clean_name = f'{stem}.{ext}'
    if clean_name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        return f'images/processed/{clean_name}'
    if clean_name in ('home-project.webp',):
        return f'images/{clean_name}'
    return f'images/processed/{clean_name}'


def dump_products():
    products = []
    for p in Product.objects.all().order_by('order', 'pk'):
        item = {
            'pk': p.pk,
            'name': p.name,
            'slug': p.slug,
            'category': p.category,
            'description': p.description,
            'power': p.power or '',
            'efficacy': p.efficacy or '',
            'output': p.output or '',
            'beam_angle': p.beam_angle or '',
            'protection': p.protection or '',
            'image': map_product_image(p.slug, media_name(p.image)),
            'banner_image': map_banner_image(p.slug, media_name(p.banner_image)),
            'dimension_image': map_dimension_image(p.slug, media_name(p.dimension_image)),
            'order': p.order,
            'parent_slug': p.parent.slug if p.parent else '',
            'translations': p.translations or {},
            'gallery': [map_gallery_image(p.slug, i.image.name) for i in p.images.all().order_by('order', 'pk')],
            'specs': p.specs or [],
        }
        products.append(item)
    return products


def dump_projects():
    projects = []
    for p in Project.objects.all().order_by('order', 'pk'):
        item = {
            'pk': p.pk,
            'title': p.title,
            'location': p.location,
            'slug': p.slug,
            'venue_type': p.venue_type,
            'sport_type': p.sport_type,
            'description': p.description,
            'results': p.results or '',
            'image': map_project_image(media_name(p.image)),
            'order': p.order,
            'translations': p.translations or {},
            'gallery': [map_project_gallery(i.image.name) for i in p.images.all().order_by('order', 'pk')],
        }
        projects.append(item)
    return projects


def dump_siteconfig():
    cfg = SiteConfig.objects.first()
    if not cfg:
        return {}
    fields = {f.name: getattr(cfg, f.name) for f in SiteConfig._meta.fields
              if f.name not in ('id', 'pk')}
    for key in list(fields.keys()):
        val = fields[key]
        if hasattr(val, 'name'):
            fields[key] = val.name if val.name else ''
    return fields


def regenerate():
    data = {
        'products': dump_products(),
        'projects': dump_projects(),
        'siteconfig': dump_siteconfig(),
    }
    data['products'].sort(key=lambda p: p.get('order', 999))
    data['projects'].sort(key=lambda p: p.get('order', 999))

    with JSON_PATH.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    py_content = '''"""Seed data embedded as Python module for Vercel compatibility.

On Vercel, non-Python files (like seed_data.json) are not automatically included
in the serverless function bundle. Embedding the data here ensures it is always
available via a normal Python import.
"""

SEED_DATA = ''' + repr(data) + '''
'''
    with PY_PATH.open('w', encoding='utf-8') as f:
        f.write(py_content)

    print(f'Regenerated {JSON_PATH} and {PY_PATH}')
    print(f'Products: {len(data["products"])}, Projects: {len(data["projects"])}')
    for p in data['products']:
        print(f'  {p["slug"]}: specs={len(p["specs"])}, banner={p["banner_image"]}, gallery={len(p["gallery"])}')


if __name__ == '__main__':
    regenerate()
