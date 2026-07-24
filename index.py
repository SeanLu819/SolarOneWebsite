import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.core.management import call_command

# On Vercel cold start: ensure DB tables exist and static files are collected
if os.environ.get('VERCEL', '') == '1':
    try:
        # Create tables in /tmp SQLite
        call_command('migrate', '--run-syncdb', verbosity=0)
    except Exception:
        pass
    try:
        # Collect static files into STATIC_ROOT for WhiteNoise to serve
        # Only run if STATIC_ROOT is empty or doesn't have the expected files
        static_root = str(settings.STATIC_ROOT)
        if not os.path.isdir(static_root) or not os.listdir(static_root):
            call_command('collectstatic', '--noinput', verbosity=0)
    except Exception:
        pass

application = get_wsgi_application()

from whitenoise import WhiteNoise

# Ensure STATIC_ROOT exists for WhiteNoise
_whitenoise_root = str(settings.STATIC_ROOT)
if not os.path.isdir(_whitenoise_root):
    os.makedirs(_whitenoise_root, exist_ok=True)

application = WhiteNoise(application, root=_whitenoise_root, autorefresh=False, prefix='static/')
