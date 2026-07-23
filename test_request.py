"""Test via actual Django request simulation"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory
from pages.views import about

factory = RequestFactory()
request = factory.get('/fr/about/')
request.LANGUAGE_CODE = 'fr'

# Simulate LocaleMiddleware setting the language
from django.utils.translation import activate
activate('fr')

response = about(request)
content = response.content.decode('utf-8')

# Check for the two problematic strings
for line in content.split('\n'):
    if 'Higher light' in line:
        print(f"FOUND ENGLISH: {line.strip()[:80]}")
    if 'Flux lumineux' in line:
        print(f"FOUND FRENCH: {line.strip()[:80]}")
    if 'Proprietary glass achieves' in line:
        print(f"FOUND ENGLISH: {line.strip()[:80]}")
    if 'Le verre propriétaire' in line:
        print(f"FOUND FRENCH: {line.strip()[:80]}")
