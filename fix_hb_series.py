import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from pages.models import Product

# Find HB Series with old slug
hb_series = Product.objects.filter(slug='rt400-series').first()
rt400hb = Product.objects.filter(slug='rt400hb').first()

print(f"HB Series (rt400-series): pk={hb_series.pk} name={hb_series.name} if hb_series else 'Not found'")
print(f"RT400HB (rt400hb): pk={rt400hb.pk} name={rt400hb.name} if rt400hb else 'Not found'")

if hb_series:
    # Update HB Series to use rt400hb slug and copy data from RT400HB if exists
    if rt400hb:
        # Copy all data from RT400HB to HB Series
        hb_series.name = rt400hb.name
        hb_series.description = rt400hb.description
        hb_series.image = rt400hb.image
        hb_series.banner_image = rt400hb.banner_image
        hb_series.dimension_image = rt400hb.dimension_image
        hb_series.beam_angle_image = rt400hb.beam_angle_image
        hb_series.ordering_image = rt400hb.ordering_image
        hb_series.ordering_info = rt400hb.ordering_info
        hb_series.specs = rt400hb.specs
        hb_series.energy_data = rt400hb.energy_data
        hb_series.translations = rt400hb.translations
        hb_series.slug = 'rt400hb'
        hb_series.save()
        print(f"Updated HB Series with RT400HB data, slug changed to rt400hb")
        
        # Delete the old RT400HB entry
        rt400hb.delete()
        print(f"Deleted RT400HB entry (pk={rt400hb.pk})")
    else:
        # Just change the slug
        hb_series.slug = 'rt400hb'
        hb_series.save()
        print(f"Updated HB Series slug to rt400hb")
else:
    print("HB Series not found in database")