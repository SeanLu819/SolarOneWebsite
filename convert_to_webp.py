"""Batch convert PNG/JPG images to WebP format in static/ and media/ directories.

Usage: python convert_to_webp.py [--dry-run]
    --dry-run: show what would be converted without writing files.
"""
import os
import sys
from pathlib import Path
from PIL import Image

DRY_RUN = '--dry-run' in sys.argv
QUALITY = 82

STATIC_DIR = Path('static')
MEDIA_DIR = Path('media')
SKIP_DIRS = {'import_tmp', '__pycache__', 'node_modules', '.git', '.venv', 'venv'}

# Only convert images larger than this (bytes)
MIN_SIZE = 20 * 1024

converted = []
skipped = []
errors = []


def convert_image(src_path: Path) -> bool:
    """Convert a single image to WebP. Returns True if converted."""
    dst_path = src_path.with_suffix('.webp')
    if dst_path.exists() and dst_path.stat().st_mtime >= src_path.stat().st_mtime:
        return False

    try:
        with Image.open(src_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')

            if DRY_RUN:
                src_size = src_path.stat().st_size
                return True

            img.save(dst_path, 'WEBP', quality=QUALITY, method=6)
            src_size = src_path.stat().st_size
            dst_size = dst_path.stat().st_size
            ratio = (1 - dst_size / src_size) * 100 if src_size else 0
            print(f'  {src_path}  {src_size//1024}KB -> {dst_path.name}  {dst_size//1024}KB  ({ratio:.0f}% smaller)')
            return True
    except Exception as e:
        errors.append((src_path, str(e)))
        return False


def process_dir(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in sorted(filenames):
            ext = Path(fname).suffix.lower()
            if ext not in ('.png', '.jpg', '.jpeg'):
                continue

            src_path = Path(dirpath) / fname

            if src_path.stat().st_size < MIN_SIZE:
                skipped.append(src_path)
                continue

            if convert_image(src_path):
                converted.append(src_path)


print(f'=== WebP Converter (QUALITY={QUALITY}, MIN_SIZE={MIN_SIZE//1024}KB) ===')
if DRY_RUN:
    print('*** DRY RUN — no files will be written ***\n')

print('\n--- Processing static/ ---')
process_dir(STATIC_DIR)

print('\n--- Processing media/ ---')
process_dir(MEDIA_DIR)

print(f'\n=== Summary ===')
print(f'Converted: {len(converted)}')
print(f'Skipped (too small): {len(skipped)}')
if errors:
    print(f'Errors: {len(errors)}')
    for p, err in errors:
        print(f'  {p}: {err}')

if DRY_RUN and converted:
    total_old = sum(p.stat().st_size for p in converted)
    print(f'\nWould convert {len(converted)} images (~{total_old//1024}KB)')