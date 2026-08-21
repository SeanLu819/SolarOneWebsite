"""Merge gallery from backup (eaf8efa) with ordering_info/pdf_url from current HEAD."""
import json

# Load backup (has complete gallery) - restored via git checkout
with open('seed_data.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# Load current (has ordering_info/pdf_url but empty gallery)
with open('seed_data_current.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

# Build lookup maps
backup_products = {p['slug']: p for p in backup.get('products', [])}
current_products = {p['slug']: p for p in current.get('products', [])}

# Merge: use backup gallery, add current ordering_info
for slug, cp in current_products.items():
    bp = backup_products.get(slug)
    if bp:
        # Keep backup's gallery (it has the complete data)
        if 'gallery' not in cp or not cp.get('gallery'):
            cp['gallery'] = bp.get('gallery', [])
        # Keep current's ordering_info
        if 'ordering_info' in cp and cp['ordering_info']:
            bp['ordering_info'] = cp['ordering_info']
        # Keep current's translations (may have updates)
        if cp.get('translations'):
            bp['translations'] = cp['translations']

# Build merged products list - use backup as base, merge current additions
merged_products = []
for bp in backup.get('products', []):
    slug = bp.get('slug', '')
    cp = current_products.get(slug)
    if cp:
        # Merge: start with backup, overlay current fields
        merged = dict(bp)
        # Ensure gallery from backup
        if not merged.get('gallery'):
            merged['gallery'] = bp.get('gallery', [])
        # Add ordering_info from current
        if 'ordering_info' in cp:
            merged['ordering_info'] = cp['ordering_info']
        # Add model_number from current
        if 'model_number' in cp:
            merged['model_number'] = cp['model_number']
        # Add specs from current
        if 'specs' in cp:
            merged['specs'] = cp['specs']
        # Add energy_data from current
        if 'energy_data' in cp:
            merged['energy_data'] = cp['energy_data']
        # Add ordering_image from current
        if 'ordering_image' in cp:
            merged['ordering_image'] = cp['ordering_image']
        # Update translations from current
        if cp.get('translations'):
            merged['translations'] = cp['translations']
        merged_products.append(merged)
    else:
        merged_products.append(bp)

# Add any new products in current that aren't in backup
for slug, cp in current_products.items():
    if slug not in backup_products:
        merged_products.append(cp)

# Projects: merge pdf_url from current
backup_projects = {p['slug']: p for p in backup.get('projects', [])}
current_projects = {p['slug']: p for p in current.get('projects', [])}

merged_projects = []
for bp in backup.get('projects', []):
    slug = bp.get('slug', '')
    cp = current_projects.get(slug)
    if cp:
        merged = dict(bp)
        if cp.get('pdf_url'):
            merged['pdf_url'] = cp['pdf_url']
        if cp.get('gallery'):
            merged['gallery'] = cp['gallery']
        if cp.get('translations'):
            merged['translations'] = cp['translations']
        merged_projects.append(merged)
    else:
        merged_projects.append(bp)

for slug, cp in current_projects.items():
    if slug not in backup_projects:
        merged_projects.append(cp)

merged_data = {
    'products': merged_products,
    'projects': merged_projects,
}

with open('seed_data.json', 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)
    f.write('\n')

print(f'Merged {len(merged_products)} products, {len(merged_projects)} projects')

# Verify
for p in merged_products:
    slug = p.get('slug', '')
    gallery = p.get('gallery', [])
    has_ordering = 'ordering_info' in p and len(p['ordering_info']) > 0
    print(f'  {slug}: {len(gallery)} gallery, ordering_info: {has_ordering}')