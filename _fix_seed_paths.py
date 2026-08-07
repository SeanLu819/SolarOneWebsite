"""Auto-fix image paths in seed_data.py and seed_data.json.

Reads the DB-mapped paths from _db_image_paths.json (built by
_build_seed_paths.py) and rewrites both files so every image-related
string points to a file that actually exists under static/.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(r'e:\Python\PROJECT\website')
SEED_PY = BASE / 'pages' / 'seed_data.py'
SEED_JSON = BASE / 'seed_data.json'
PATHS_JSON = BASE / '_db_image_paths.json'

# ---------------------------------------------------------------------------
# Load DB-derived canonical paths
# ---------------------------------------------------------------------------

paths = json.loads(PATHS_JSON.read_text(encoding='utf-8'))
project_map = paths['projects']     # slug -> dict
product_map = paths['products']     # slug -> dict


def project_static_main(slug):
    return project_map.get(slug, {}).get('image', '')


def project_static_gallery(slug):
    return project_map.get(slug, {}).get('gallery', [])


def product_field(slug, field):
    return product_map.get(slug, {}).get(field, '')


def product_gallery(slug):
    return product_map.get(slug, {}).get('gallery', [])


# ---------------------------------------------------------------------------
# Fix seed_data.json (simple JSON-based replacement)
# ---------------------------------------------------------------------------

data = json.loads(SEED_JSON.read_text(encoding='utf-8'))

# Map slug -> index in data['projects'] using slug/title
for proj in data.get('projects', []):
    slug = proj.get('slug', '')
    if not slug:
        continue
    if slug in project_map:
        new_main = project_map[slug].get('image', '')
        if new_main:
            proj['image'] = new_main
        new_gallery = project_map[slug].get('gallery', [])
        if new_gallery:
            proj['gallery'] = new_gallery

for prod in data.get('products', []):
    slug = prod.get('slug', '')
    if not slug or slug not in product_map:
        continue
    canon = product_map[slug]
    for fld in ('image', 'banner_image', 'dimension_image', 'beam_angle_image'):
        v = canon.get(fld, '')
        if v:
            prod[fld] = v
    if canon.get('gallery'):
        prod['gallery'] = canon['gallery']

SEED_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Wrote {SEED_JSON}')

# ---------------------------------------------------------------------------
# Fix seed_data.py (Python-source rewriting — careful with quoting)
# ---------------------------------------------------------------------------
# The file contains a single SEED_DATA = { ... } literal as a JSON-shaped
# Python dict. We rewrite the file by parsing via json after stripping
# the SEED_DATA = assignment.

src_text = SEED_PY.read_text(encoding='utf-8')

# Find SEED_DATA = { ... } block
m = re.search(r'^(SEED_DATA\s*=\s*)(\{.*\})(\s*)$', src_text, re.DOTALL | re.MULTILINE)
if not m:
    print('Could not locate SEED_DATA block in seed_data.py — aborting')
    sys.exit(1)

prefix, block, suffix = m.group(1), m.group(2), m.group(3)
# The block is JSON-compatible (uses true/false/null, but we use string values
# only here). Try to load as JSON; on failure fall back to ast.
try:
    block_data = json.loads(block)
except Exception:
    import ast
    # Replace true/false/null with python literals before ast
    py_block = re.sub(r'\btrue\b', 'True', block)
    py_block = re.sub(r'\bfalse\b', 'False', py_block)
    py_block = re.sub(r'\bnull\b', 'None', py_block)
    block_data = ast.literal_eval(py_block)

# Apply same fixes
for proj in block_data.get('projects', []):
    slug = proj.get('slug', '')
    if not slug or slug not in project_map:
        continue
    new_main = project_map[slug].get('image', '')
    if new_main:
        proj['image'] = new_main
    new_gallery = project_map[slug].get('gallery', [])
    if new_gallery:
        proj['gallery'] = new_gallery

for prod in block_data.get('products', []):
    slug = prod.get('slug', '')
    if not slug or slug not in product_map:
        continue
    canon = product_map[slug]
    for fld in ('image', 'banner_image', 'dimension_image', 'beam_angle_image'):
        v = canon.get(fld, '')
        if v:
            prod[fld] = v
    if canon.get('gallery'):
        prod['gallery'] = canon['gallery']

# Serialize back. Use json.dumps with same indent as original (2 spaces),
# but write as Python-style (True/False/None) for consistency.
out = json.dumps(block_data, ensure_ascii=False, indent=2)
# Convert JSON booleans/nulls to Python literals so the .py file remains valid
out = re.sub(r'\btrue\b', 'True', out)
out = re.sub(r'\bfalse\b', 'False', out)
out = re.sub(r'\bnull\b', 'None', out)

new_src = src_text[:m.start()] + prefix + out + suffix + src_text[m.end():]
SEED_PY.write_text(new_src, encoding='utf-8')
print(f'Wrote {SEED_PY}')

print()
print('Done.')
