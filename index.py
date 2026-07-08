import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from whitenoise import WhiteNoise

application = get_wsgi_application()

static_root = getattr(settings, 'STATIC_ROOT', os.path.join(BASE_DIR, 'staticfiles'))
if os.path.exists(static_root):
    application = WhiteNoise(application, root=static_root)
