"""Final verification: every image path in seed_data.py must point to a file
under static/. Lists any missing paths and exits non-zero on failures.
"""
import os, sys, re
from pathlib import Path

BASE = Path(r'e:\Python\PROJECT\website')
STATIC = BASE / 'static'
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

import django
django.setup()

from pages.seed_data import SEED_DATA

missing = []
total = 0
for kind, items, fld, gallery_fld in (
    ('product', SEED_DATA.get('products', []),
     ('image', 'banner_image', 'dimension_image', 'beam_angle_image'),
     'gallery'),
    ('project', SEED_DATA.get('projects', []),
     ('image',), 'gallery'),
):
    for item in items:
        for f in fld:
            v = item.get(f, '')
            if v:
                total += 1
                p = STATIC / v
                if not p.exists():
                    missing.append((kind, item.get('slug', '?'), f, v))
        for g in item.get(gallery_fld, []) or []:
            total += 1
            p = STATIC / g
            if not p.exists():
                missing.append((kind, item.get('slug', '?'), 'gallery', g))

print(f'Total image refs: {total}')
print(f'Missing:          {len(missing)}')
if missing:
    print('---')
    for kind, slug, fld, v in missing:
        print(f'  {kind}:{slug}  {fld}  {v}')
    sys.exit(1)
else:
    print('All paths OK')
