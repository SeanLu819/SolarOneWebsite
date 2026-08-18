import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

IS_VERCEL = os.environ.get('VERCEL', '') == '1'

if IS_VERCEL and 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

from django.core.wsgi import get_wsgi_application
from django.conf import settings

# collectstatic runs at BUILD time (build.sh), not at runtime.
# This eliminates 5-15s of cold start latency on Vercel.
# If staticfiles/ is missing at runtime, WhiteNoise falls back to STATICFILES_DIRS.

application = get_wsgi_application()

import whitenoise

STATIC_ROOT_VAL = str(settings.STATIC_ROOT)
_STATICFILES_DIRS = list(getattr(settings, 'STATICFILES_DIRS', []))

sys.stderr.write(f'[index.py] BASE_DIR={BASE_DIR}\n')
sys.stderr.write(f'[index.py] STATIC_ROOT={STATIC_ROOT_VAL} exists={os.path.isdir(STATIC_ROOT_VAL)}\n')
if os.path.isdir(STATIC_ROOT_VAL):
    _sr_files = sum(len(f) for _, _, f in os.walk(STATIC_ROOT_VAL))
    sys.stderr.write(f'[index.py] STATIC_ROOT file count={_sr_files}\n')
for _i, d in enumerate(_STATICFILES_DIRS):
    _d = str(d)
    sys.stderr.write(f'[index.py] STATICFILES_DIRS[{_i}]={_d} exists={os.path.isdir(_d)}\n')
    if os.path.isdir(_d):
        _sf_files = sum(len(f) for _, _, f in os.walk(_d))
        sys.stderr.write(f'[index.py]   file count={_sf_files}\n')
sys.stderr.flush()

_roots = []
if os.path.isdir(STATIC_ROOT_VAL):
    _roots.append(STATIC_ROOT_VAL)
for d in _STATICFILES_DIRS:
    _d = str(d)
    if os.path.isdir(_d) and _d not in _roots:
        _roots.append(_d)

if _roots:
    _primary = _roots[0]
    try:
        application = whitenoise.WhiteNoise(
            application, root=_primary, autorefresh=False, prefix='/static/',
            use_finders=False,
        )
    except TypeError:
        application = whitenoise.WhiteNoise(
            application, root=_primary, autorefresh=False, prefix='/static/',
        )
    for _extra in _roots[1:]:
        try:
            application.add_files(_extra, prefix='/static/')
        except Exception as exc:
            sys.stderr.write(f'[whitenoise] WARN skip add_files {_extra}: {exc}\n')
else:
    try:
        application = whitenoise.WhiteNoise(
            application, autorefresh=False, prefix='/static/', use_finders=False,
        )
    except TypeError:
        application = whitenoise.WhiteNoise(
            application, autorefresh=False, prefix='/static/',
        )

_media_root = str(settings.MEDIA_ROOT)
if os.path.isdir(_media_root):
    try:
        application.add_files(_media_root, prefix='/media/')
    except Exception as exc:
        sys.stderr.write(f'[whitenoise] WARN add_files media {_media_root}: {exc}\n')

_file_count = len(getattr(application, 'files', {}))
sys.stderr.write(f'[whitenoise] ready with {_file_count} static/media files, roots={_roots}\n')
_sample_keys = list(getattr(application, 'files', {}).keys())[:10]
sys.stderr.write(f'[whitenoise] sample keys: {_sample_keys}\n')
_gallery_test = '/static/images/projects/gallery/shys-soccer-01.webp'
_wn_found = _gallery_test in getattr(application, 'files', {})
sys.stderr.write(f'[whitenoise] test gallery file {_gallery_test}: found={_wn_found}\n')
_product_test = '/static/images/products/fl4m-01.webp'
_wn_found2 = _product_test in getattr(application, 'files', {})
sys.stderr.write(f'[whitenoise] test product file {_product_test}: found={_wn_found2}\n')
sys.stderr.flush()