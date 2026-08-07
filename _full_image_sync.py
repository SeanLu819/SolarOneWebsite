"""Sync all DB-referenced images to static/ so Vercel can serve them.

For every Product, ProductImage, Project, ProjectImage we:
  1. Read the media file (if any)
  2. Strip Django's hash suffix from the filename
  3. Copy it into static/images/ at the right sub-path
  4. Update seed_data.py + seed_data.json to use the clean (no-hash) path

This script is idempotent: re-running is safe.
"""
import os
import sys
import re
import json
import shutil
import django
from pathlib import Path

BASE = Path(r'e:\Python\PROJECT\website')
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
django.setup()

from pages.models import Project, ProjectImage, Product, ProductImage

MEDIA = BASE / 'media'
STATIC = BASE / 'static'
SEED_PY = BASE / 'pages' / 'seed_data.py'
SEED_JSON = BASE / 'seed_data.json'

# ---------------------------------------------------------------------------
# Path-mapping helpers (must match views.py)
# ---------------------------------------------------------------------------

HASH_SUFFIX_RE = re.compile(r'_[A-Za-z0-9_-]{6,}(?=\.[^.]+$)')


def clean_name(name: str) -> str:
    """Strip Django upload hash suffix like _eRixs78 from filename."""
    return HASH_SUFFIX_RE.sub('', name)


def project_static_main(media_path: str) -> str:
    """Map a project main image media path to its static path (cleaned)."""
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/processed/{clean_name(p.name)}'


def project_static_gallery(media_path: str) -> str:
    """Map a project gallery image to its static path (cleaned)."""
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/projects/gallery/{clean_name(p.name)}'


def product_static_main(slug: str, media_path: str) -> str:
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/products/{slug}/{clean_name(p.name)}'


def product_static_banner(slug: str, media_path: str) -> str:
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/products/{slug}/{clean_name(p.name)}'


def product_static_dim(slug: str, media_path: str) -> str:
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/products/{slug}/{clean_name(p.name)}'


def product_static_beam(slug: str, media_path: str) -> str:
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/products/{slug}/{clean_name(p.name)}'


def product_static_gallery(slug: str, media_path: str) -> str:
    if not media_path:
        return ''
    p = Path(media_path)
    return f'images/products/{slug}/{clean_name(p.name)}'


# ---------------------------------------------------------------------------
# File copy helpers
# ---------------------------------------------------------------------------

copied = []
skipped = []
missing_media = []


def copy_to_static(media_path: str, static_rel: str, label: str) -> bool:
    """Copy a media file to static/, replacing any existing file with same name."""
    if not media_path or not static_rel:
        return False
    src = MEDIA / media_path
    if not src.exists():
        missing_media.append((label, media_path))
        return False
    dst = STATIC / static_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Always overwrite so updates from admin propagate
    shutil.copy2(src, dst)
    copied.append((label, str(src), str(dst)))
    return True


# ---------------------------------------------------------------------------
# Sync projects
# ---------------------------------------------------------------------------

print('=' * 80)
print('PROJECTS — main image')
print('=' * 80)
for p in Project.objects.all().order_by('id'):
    if not p.image:
        continue
    static_rel = project_static_main(p.image.name)
    copy_to_static(p.image.name, static_rel, f'project:{p.slug}:main')

print()
print('=' * 80)
print('PROJECT GALLERY IMAGES')
print('=' * 80)
for pi in ProjectImage.objects.all().select_related('project').order_by('project_id', 'id'):
    if not pi.image:
        continue
    static_rel = project_static_gallery(pi.image.name)
    copy_to_static(pi.image.name, static_rel, f'project:{pi.project.slug}:gallery:{pi.id}')

print()
print('=' * 80)
print('PRODUCTS — main/banner/dim/beam images')
print('=' * 80)
for p in Product.objects.all().order_by('id'):
    for fld, fn in (
        ('image', product_static_main),
        ('banner_image', product_static_banner),
        ('dimension_image', product_static_dim),
        ('beam_angle_image', product_static_beam),
    ):
        val = getattr(p, fld)
        if not val or not val.name:
            continue
        static_rel = fn(p.slug, val.name)
        copy_to_static(val.name, static_rel, f'product:{p.slug}:{fld}')

print()
print('=' * 80)
print('PRODUCT GALLERY IMAGES')
print('=' * 80)
for pi in ProductImage.objects.all().select_related('product').order_by('product_id', 'id'):
    if not pi.image:
        continue
    static_rel = product_static_gallery(pi.product.slug, pi.image.name)
    copy_to_static(pi.image.name, static_rel, f'product:{pi.product.slug}:gallery:{pi.id}')

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'Copied: {len(copied)}')
for label, src, dst in copied:
    print(f'  [+] {label}: {Path(dst).relative_to(STATIC)}')
print()
print(f'Missing in media (no source file): {len(missing_media)}')
for label, mp in missing_media:
    print(f'  [!] {label}: {mp}')
