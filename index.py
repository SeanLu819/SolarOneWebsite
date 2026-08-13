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

import whitenoise

STATIC_ROOT_VAL = str(settings.STATIC_ROOT)
_STATICFILES_DIRS = list(getattr(settings, 'STATICFILES_DIRS', []))

_roots = []
if os.path.isdir(STATIC_ROOT_VAL):
    _roots.append(STATIC_ROOT_VAL)
for d in _STATICFILES_DIRS:
    _d = str(d)
    if os.path.isdir(_d) and _d not in _roots:
        _roots.append(_d)

if _roots:
    _primary = _roots[0]
    application = whitenoise.WhiteNoise(application, root=_primary, autorefresh=False, prefix='/static/')
    for _extra in _roots[1:]:
        try:
            application.add_files(_extra, prefix='/static/')
        except Exception as exc:
            sys.stderr.write(f'[whitenoise] WARN skip add_files {_extra}: {exc}\n')
else:
    application = whitenoise.WhiteNoise(application, autorefresh=False, prefix='/static/')

_media_root = str(settings.MEDIA_ROOT)
if os.path.isdir(_media_root):
    try:
        application.add_files(_media_root, prefix='/media/')
    except Exception as exc:
        sys.stderr.write(f'[whitenoise] WARN add_files media {_media_root}: {exc}\n')

if hasattr(application, 'files'):
    sys.stderr.write(f'[whitenoise] ready with {len(application.files)} static/media files, roots={_roots}\n')