import json
import sys

with open('seed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Products: {len(data['products'])}")
print(f"Projects: {len(data['projects'])}")

py_repr = repr(data)

with open('pages/seed_data.py', 'w', encoding='utf-8') as f:
    f.write('"""Seed data embedded as Python module for Vercel compatibility.\n')
    f.write('\n')
    f.write('On Vercel, non-Python files (like seed_data.json) are not automatically included\n')
    f.write('in the serverless function bundle. Embedding the data here ensures it is always\n')
    f.write('available via a normal Python import.\n')
    f.write('\n')
    f.write('AUTO-GENERATED from seed_data.json — do not edit manually.\n')
    f.write('Run: python _regen_seed.py\n')
    f.write('"""\n\n')
    f.write('SEED_DATA = ')
    f.write(py_repr)
    f.write('\n')

print("seed_data.py regenerated successfully!")