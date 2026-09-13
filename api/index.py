import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

IS_VERCEL = os.environ.get('VERCEL', '') == '1'

if IS_VERCEL and 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

from django.core.wsgi import get_wsgi_application
from django.conf import settings

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

# --- static storage self-check -------------------------------------------------
# Content-hashed static URLs need the manifest at request time. If it is missing,
# {% static %} raises and EVERY page becomes a 500 (incident 2026-09-12). Log the
# decisive facts on cold start so a future failure is diagnosable in one glance.
try:
    from django.contrib.staticfiles.storage import staticfiles_storage

    sys.stderr.write(f'[index.py] static storage = {type(staticfiles_storage).__name__}\n')
    try:
        from pages.storage import bundled_hashed_files
        _bundled = bundled_hashed_files()
        sys.stderr.write(f'[index.py] bundled manifest entries = {len(_bundled)}\n')
        if not _bundled:
            sys.stderr.write(
                '[index.py] WARNING: bundled manifest is empty — static URLs will be '
                'un-hashed. Check that build.sh ran pages.static_index.\n'
            )
    except Exception as exc:
        sys.stderr.write(f'[index.py] bundled manifest check skipped: {exc!r}\n')
    for _probe in ('css/base.css', 'images/hero-main.webp'):
        try:
            sys.stderr.write(f'[index.py] static("{_probe}") -> {staticfiles_storage.url(_probe)}\n')
        except Exception as exc:
            sys.stderr.write(f'[index.py] static("{_probe}") FAILED: {exc!r}\n')
except Exception as exc:  # never let diagnostics break the app
    sys.stderr.write(f'[index.py] static self-check failed: {exc!r}\n')

# --- contact-form persistence self-check --------------------------------------
# On Vercel the contact form stores submissions in the ephemeral /tmp SQLite DB
# (lost on redeploy). The only durable channel is email, gated by CONTACT_NOTIFY_EMAIL
# + SMTP. If neither is configured, submissions are silently lost (incident 2026-09-13).
try:
    _notify = getattr(settings, 'CONTACT_NOTIFY_EMAIL', '')
    _email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    _db_url = os.environ.get('DATABASE_URL', '')
    _ephemeral = '/tmp/' in _db_url
    sys.stderr.write(f'[index.py] contact notify_email set = {bool(_notify)}\n')
    sys.stderr.write(f'[index.py] email backend = {_email_backend}\n')
    sys.stderr.write(f'[index.py] DB ephemeral(/tmp) = {_ephemeral} (url={_db_url})\n')
    if getattr(settings, 'IS_VERCEL', False) and not _notify:
        sys.stderr.write(
            '[index.py] WARNING: contact form has NO durable delivery on Vercel '
            '(notify_email empty, DB ephemeral). Submissions will be LOST. '
            'Set CONTACT_NOTIFY_EMAIL + EMAIL_HOST_USER/PASSWORD, or point DATABASE_URL at Neon/Supabase.\n'
        )
except Exception as exc:  # never let diagnostics break the app
    sys.stderr.write(f'[index.py] contact self-check failed: {exc!r}\n')
sys.stderr.flush()