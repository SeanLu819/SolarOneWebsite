"""Fix script: copy ordering image to static dir, run collectstatic, and verify.

Run this in your own terminal (PowerShell or CMD):
  python fix_images.py
"""
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

MEDIA_SRC = os.path.join(BASE, 'media', 'products', 'ordering', 'sample-number.webp')
STATIC_DST_DIR = os.path.join(BASE, 'static', 'images', 'products', 'ordering')
STATIC_DST = os.path.join(STATIC_DST_DIR, 'sample-number.webp')

print(f"Source exists: {os.path.isfile(MEDIA_SRC)}")

if os.path.isfile(MEDIA_SRC):
    os.makedirs(STATIC_DST_DIR, exist_ok=True)
    shutil.copy2(MEDIA_SRC, STATIC_DST)
    print(f"Copied to: {STATIC_DST}")
    print(f"Dest exists: {os.path.isfile(STATIC_DST)}")
else:
    print(f"ERROR: Source not found: {MEDIA_SRC}")
    sys.exit(1)

print("\nRunning collectstatic...")
os.system(f'{sys.executable} manage.py collectstatic --noinput')

print("\nVerifying all M series images in staticfiles/...")
import glob
checks = [
    'images/products/fl1m/fl1m-3d-view.webp',
    'images/products/fl1m/beamangle-12183050_65Fg8YW.webp',
    'images/products/fl4m/fl4m-3d-view.webp',
    'images/products/fl4m/beamangle-12183050.webp',
    'images/products/fl6m/fl6m-3d-view.webp',
    'images/products/fl6m/beamangle-12183050_KcK84ZP.webp',
    'images/products/fl9m/fl9m-3d-view_DbaAklf.webp',
    'images/products/fl9m/beamangle-12183050_4BJ8mot.webp',
    'images/products/fl12m/fl12m-3d-view.webp',
    'images/products/fl12m/beamangle-12183050_RlTn9zd.webp',
    'images/products/fl16m/fl16m-3d-view.webp',
    'images/products/fl16m/beamangle-12183050_vxDZHMV.webp',
    'images/products/ordering/sample-number.webp',
]
for c in checks:
    sf = os.path.join(BASE, 'staticfiles', c)
    st = os.path.join(BASE, 'static', c)
    print(f"  {'OK' if os.path.isfile(sf) else 'MISSING in staticfiles'}: {c}"
          f" {'(static OK)' if os.path.isfile(st) else '(static MISSING)'}")

print("\nDone!")