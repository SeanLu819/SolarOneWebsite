import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

# Ensure database tables exist on each cold start (Vercel /tmp SQLite is ephemeral)
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.core.management import call_command

# Run migrations silently before starting the app
# This is safe for SQLite and ensures /tmp/db.sqlite3 has the required tables
try:
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception:
    pass  # If migrate fails, let the request handling surface the real error

application = get_wsgi_application()

from whitenoise import WhiteNoise

# WhiteNoise wraps the WSGI app and serves static files from STATIC_ROOT
application = WhiteNoise(application, root=settings.STATIC_ROOT, prefix='static/')
