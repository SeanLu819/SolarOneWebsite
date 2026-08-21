import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
import django
django.setup()

from pages.models import Product

print("=== Current Products in Database ===")
products = Product.objects.all().order_by('pk')
for p in products:
    print(f"pk={p.pk} | name={p.name} | slug={p.slug}")

print("\n=== Checking HB Series specifically ===")
hb_series = Product.objects.filter(slug='rt400-series').first()
rt400hb = Product.objects.filter(slug='rt400hb').first()

if hb_series:
    print(f"Found rt400-series: pk={hb_series.pk} name={hb_series.name}")
else:
    print("rt400-series NOT found (good!)")

if rt400hb:
    print(f"Found rt400hb: pk={rt400hb.pk} name={rt400hb.name}")
else:
    print("rt400hb NOT found")