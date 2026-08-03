"""Update seed_data.json and pages/seed_data.py with missing M Series subseries.

The local SQLite DB contains FL1M/FL4M/FL6M/FL9M/FL12M/FL16M, but these are not
in the Vercel fallback seed data, causing 'Product Not Found' on Vercel.
This script reads pages/seed_data.py (the authoritative Vercel fallback),
adds the missing subseries, and syncs the result back to seed_data.json.
"""
import ast
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SUBSERIES = [
    {
        "pk": 101,
        "name": "FL1M",
        "slug": "fl1m",
        "category": "FLOODLIGHT",
        "description": "Single-module M Series floodlight — 80W compact LED solution for small courts, entry-level sports fields and area lighting.",
        "power": "80W",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl1m/fl1m-01.png",
        "banner_image": "images/products/fl1m/fl1m-bar-1.webp",
        "dimension_image": "",
        "order": 11,
        "parent_slug": "m-series",
        "translations": {},
    },
    {
        "pk": 104,
        "name": "FL4M",
        "slug": "fl4m",
        "category": "FLOODLIGHT",
        "description": "Four-module M Series floodlight — 320W high-output LED luminaire for medium-sized sports fields and commercial area lighting.",
        "power": "320W",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl4m/fl4m-01.png",
        "banner_image": "images/products/fl4m/fl4m-bar-1.webp",
        "dimension_image": "images/products/fl4m/fl4m-3d-view.png",
        "order": 12,
        "parent_slug": "m-series",
        "translations": {},
    },
    {
        "pk": 106,
        "name": "FL6M",
        "slug": "fl6m",
        "category": "FLOODLIGHT",
        "description": "Six-module M Series floodlight — 480W LED performance lighting for professional training facilities and mid-size stadiums.",
        "power": "480W",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl6m/fl6m-01.png",
        "banner_image": "images/products/fl6m/fl6m-bar-1.webp",
        "dimension_image": "",
        "order": 13,
        "parent_slug": "m-series",
        "translations": {},
    },
    {
        "pk": 109,
        "name": "FL9M",
        "slug": "fl9m",
        "category": "FLOODLIGHT",
        "description": "Nine-module M Series floodlight — 630W broadcast-grade LED sports light for football, baseball and multi-purpose arenas.",
        "power": "630W",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl9m/fl9m-01.png",
        "banner_image": "images/products/fl9m/fl9m-bar-1.webp",
        "dimension_image": "",
        "order": 14,
        "parent_slug": "m-series",
        "translations": {},
    },
    {
        "pk": 112,
        "name": "FL12M",
        "slug": "fl12m",
        "category": "FLOODLIGHT",
        "description": "Twelve-module M Series floodlight — 1000W high-power LED solution for large stadiums and professional sports venues.",
        "power": "1000W",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl12m/fl12m-01.png",
        "banner_image": "images/products/fl12m/fl12m-bar-1.webp",
        "dimension_image": "",
        "order": 15,
        "parent_slug": "m-series",
        "translations": {},
    },
    {
        "pk": 116,
        "name": "FL16M",
        "slug": "fl16m",
        "category": "FLOODLIGHT",
        "description": "Sixteen-module M Series floodlight — 1280W+ maximum output LED system for broadcast-ready stadiums and large-area illumination.",
        "power": "1280W+",
        "efficacy": "125lm/W",
        "output": "",
        "beam_angle": "",
        "protection": "",
        "image": "images/products/fl16m/fl16m-01.png",
        "banner_image": "images/products/fl16m/fl16m-bar-1.webp",
        "dimension_image": "",
        "order": 16,
        "parent_slug": "m-series",
        "translations": {},
    },
]


def load_seed_py():
    path = BASE_DIR / "pages" / "seed_data.py"
    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Extract the SEED_DATA dict using AST
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SEED_DATA":
                    return ast.literal_eval(node.value)
    raise RuntimeError("SEED_DATA not found in pages/seed_data.py")


def save_seed_py(data):
    path = BASE_DIR / "pages" / "seed_data.py"
    content = '''"""Seed data embedded as Python module for Vercel compatibility.

On Vercel, non-Python files (like seed_data.json) are not automatically included
in the serverless function bundle. Embedding the data here ensures it is always
available via a normal Python import.
"""

SEED_DATA = ''' + repr(data) + '''
'''
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def save_seed_json(data):
    path = BASE_DIR / "seed_data.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    data = load_seed_py()

    products = data["products"]
    existing_slugs = {p["slug"] for p in products}
    added = []
    for product in SUBSERIES:
        if product["slug"] not in existing_slugs:
            products.append(product)
            added.append(product["slug"])

    # Sort products by order to keep consistent layout
    products.sort(key=lambda p: p.get("order", 999))

    save_seed_py(data)
    save_seed_json(data)

    print("Added subseries:", added)
    print("Total products in seed data:", len(products))


if __name__ == "__main__":
    main()
