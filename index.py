import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static files directly on Vercel
# Vercel's Python runtime can read the source static/ directory,
# so we serve from STATICFILES_DIRS (not collectstatic output)
import whitenoise

# Find the first available static files directory
_serve_root = None
for d in settings.STATICFILES_DIRS:
    _d = str(d)
    if os.path.isdir(_d):
        _serve_root = _d
        break

if _serve_root:
    # WhiteNoise wraps the WSGI app once, serving /static/* from the source dir
    application = whitenoise.WhiteNoise(application, root=_serve_root, autorefresh=False, prefix='static/')
else:
    # Last resort: use STATIC_ROOT
    _sr = str(settings.STATIC_ROOT)
    if os.path.isdir(_sr):
        application = whitenoise.WhiteNoise(application, root=_sr, autorefresh=False, prefix='static/')
