import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from whitenoise import WhiteNoise

application = get_wsgi_application()

# WhiteNoise wraps the WSGI app and serves static files from STATIC_ROOT
# After collectstatic runs during build, STATIC_ROOT will have all assets
application = WhiteNoise(application, root=settings.STATIC_ROOT, prefix='static/')
