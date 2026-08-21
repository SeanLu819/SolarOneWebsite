"""Regenerate seed_data.py from seed_data.json (which has been restored from eaf8efa with gallery)."""
import json
import re

def escape_json_string(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

def main():
    with open('seed_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lines = []
    lines.append('"""Seed data embedded as Python module for Vercel compatibility."""')
    lines.append('')
    lines.append('SEED_DATA = {')
    lines.append('  "products": [')
    
    products = data.get('products', [])
    for i, p in enumerate(products):
        lines.append('    {')
        lines.append(f'      "pk": {p.get("pk", i+1)},')
        lines.append(f'      "name": "{escape_json_string(p.get("name", ""))}",')
        lines.append(f'      "slug": "{escape_json_string(p.get("slug", ""))}",')
        lines.append(f'      "category": "{escape_json_string(p.get("category", ""))}",')
        lines.append(f'      "description": "{escape_json_string(p.get("description", ""))}",')
        lines.append(f'      "power": "{escape_json_string(p.get("power", ""))}",')
        lines.append(f'      "efficacy": "{escape_json_string(p.get("efficacy", ""))}",')
        lines.append(f'      "output": "{escape_json_string(p.get("output", ""))}",')
        lines.append(f'      "beam_angle": "{escape_json_string(p.get("beam_angle", ""))}",')
        lines.append(f'      "protection": "{escape_json_string(p.get("protection", ""))}",')
        lines.append(f'      "image": "{escape_json_string(p.get("image", ""))}",')
        lines.append(f'      "banner_image": "{escape_json_string(p.get("banner_image", ""))}",')
        lines.append(f'      "dimension_image": "{escape_json_string(p.get("dimension_image", ""))}",')
        lines.append(f'      "beam_angle_image": "{escape_json_string(p.get("beam_angle_image", ""))}",')
        lines.append(f'      "ordering_image": "{escape_json_string(p.get("ordering_image", ""))}",')
        lines.append(f'      "cert_image": "{escape_json_string(p.get("cert_image", ""))}",')
        lines.append(f'      "order": {p.get("order", 0)},')
        lines.append(f'      "parent_slug": "{escape_json_string(p.get("parent_slug", ""))}",')
        
        lines.append('      "translations": {')
        trans = p.get('translations', {})
        for lang, tdata in trans.items():
            lines.append(f'        "{lang}": {{')
            for k, v in tdata.items():
                lines.append(f'          "{k}": "{escape_json_string(v)}",')
            lines.append('        },')
        lines.append('      },')
        
        gallery = p.get('gallery', [])
        if gallery:
            lines.append('      "gallery": [')
            for g in gallery:
                lines.append(f'        "{escape_json_string(g)}",')
            lines.append('      ],')
        else:
            lines.append('      "gallery": [],')
        
        ordering_info = p.get('ordering_info', [])
        if ordering_info:
            lines.append('      "ordering_info": [')
            for oi in ordering_info:
                lines.append(f'        "{escape_json_string(oi)}",')
            lines.append('      ],')
        
        specs = p.get('specs', [])
        if specs:
            lines.append('      "specs": [')
            for s in specs:
                lines.append('        {')
                lines.append(f'          "label": "{escape_json_string(s.get("label", ""))}",')
                lines.append(f'          "value": "{escape_json_string(s.get("value", ""))}"')
                lines.append('        },')
            lines.append('      ],')
        else:
            lines.append('      "specs": [],')
        
        energy = p.get('energy_data', [])
        if energy:
            lines.append('      "energy_data": [')
            for e in energy:
                lines.append('        {')
                lines.append(f'          "label": "{escape_json_string(e.get("label", ""))}",')
                lines.append(f'          "value": "{escape_json_string(e.get("value", ""))}"')
                lines.append('        },')
            lines.append('      ],')
        else:
            lines.append('      "energy_data": [],')
        
        lines.append(f'      "model_number": "{escape_json_string(p.get("model_number", ""))}",')
        
        comma = ',' if i < len(products) - 1 else ''
        lines.append(f'    }}{comma}')
    
    lines.append('  ],')
    
    lines.append('  "projects": [')
    projects = data.get('projects', [])
    for i, proj in enumerate(projects):
        lines.append('    {')
        lines.append(f'      "pk": {proj.get("pk", i+1)},')
        lines.append(f'      "title": "{escape_json_string(proj.get("title", ""))}",')
        lines.append(f'      "location": "{escape_json_string(proj.get("location", ""))}",')
        lines.append(f'      "slug": "{escape_json_string(proj.get("slug", ""))}",')
        lines.append(f'      "venue_type": "{escape_json_string(proj.get("venue_type", ""))}",')
        lines.append(f'      "sport_type": "{escape_json_string(proj.get("sport_type", ""))}",')
        lines.append(f'      "description": "{escape_json_string(proj.get("description", ""))}",')
        lines.append(f'      "results": "{escape_json_string(proj.get("results", ""))}",')
        lines.append(f'      "image": "{escape_json_string(proj.get("image", ""))}",')
        lines.append(f'      "order": {proj.get("order", 0)},')
        lines.append(f'      "pdf_url": "{escape_json_string(proj.get("pdf_url", ""))}",')
        
        gallery = proj.get('gallery', [])
        if gallery:
            lines.append('      "gallery": [')
            for g in gallery:
                lines.append(f'        "{escape_json_string(g)}",')
            lines.append('      ],')
        else:
            lines.append('      "gallery": [],')
        
        lines.append('      "translations": {')
        trans = proj.get('translations', {})
        for lang, tdata in trans.items():
            lines.append(f'        "{lang}": {{')
            for k, v in tdata.items():
                lines.append(f'          "{k}": "{escape_json_string(v)}",')
            lines.append('        },')
        lines.append('      },')
        
        comma = ',' if i < len(projects) - 1 else ''
        lines.append(f'    }}{comma}')
    
    lines.append('  ],')
    lines.append('}')
    
    content = '\n'.join(lines)
    with open('pages/seed_data.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'seed_data.py regenerated: {len(products)} products, {len(projects)} projects')
    for p in products:
        slug = p.get('slug', '')
        gallery = p.get('gallery', [])
        has_ordering = 'ordering_info' in p and len(p['ordering_info']) > 0
        if gallery or has_ordering:
            print(f'  {slug}: {len(gallery)} gallery, ordering_info: {has_ordering}')

if __name__ == '__main__':
    main()