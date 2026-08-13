import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

if os.environ.get('VERCEL', '') == '1' and 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static (+ media shadow) files directly on Vercel.
#
# Priority order:
#   1. STATIC_ROOT  (collectstatic output, vercel.json distDir)
#   2. STATICFILES_DIRS  (committed source static/, includes images/projects/*)
#   3. Extra /media/ prefix mapped into static/media/ so images copied there
#      by the post-save signal (or manually committed) remain reachable at
#      the canonical MEDIA_URL even on serverless.
import whitenoise

_sr = str(settings.STATIC_ROOT)
if os.path.isdir(_sr):
    application = whitenoise.WhiteNoise(application, root=_sr, autorefresh=False, prefix='/static/')
else:
    for d in settings.STATICFILES_DIRS:
        _d = str(d)
        if os.path.isdir(_d):
            application = whitenoise.WhiteNoise(application, root=_d, autorefresh=False, prefix='/static/')
            break

_media_shadow = os.path.join(str(BASE_DIR), 'static', 'media')
if os.path.isdir(_media_shadow) and isinstance(application, whitenoise.WhiteNoise):
    application.add_files(_media_shadow, prefix='/media/')

_media_legacy = os.path.join(str(BASE_DIR), 'media')
if os.path.isdir(_media_legacy) and isinstance(application, whitenoise.WhiteNoise):
    try:
        application.add_files(_media_legacy, prefix='/media/')
    except Exception:
        pass