import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

# On Vercel, use a writable ephemeral SQLite path so Django can at least
# create tables if needed. Product/project data is served from seed_data.json
# via the JSON fallback in pages/views.py — DB writes are not relied upon.
if os.environ.get('VERCEL', '') == '1' and 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static files directly on Vercel
import whitenoise

_serve_root = None
for d in settings.STATICFILES_DIRS:
    _d = str(d)
    if os.path.isdir(_d):
        _serve_root = _d
        break

if _serve_root:
    application = whitenoise.WhiteNoise(application, root=_serve_root, autorefresh=False, prefix='static/')
else:
    _sr = str(settings.STATIC_ROOT)
    if os.path.isdir(_sr):
        application = whitenoise.WhiteNoise(application, root=_sr, autorefresh=False, prefix='static/')