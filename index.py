import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

# WhiteNoise: serve static files directly from STATICFILES_DIRS (source)
# On Vercel, the build output directory is read-only, so we use the source dirs
from whitenoise import WhiteNoise

_whitenoise_dirs = [str(d) for d in settings.STATICFILES_DIRS if os.path.isdir(d)]
if not _whitenoise_dirs:
    # Fallback: serve from STATIC_ROOT if available
    _whitenoise_root = str(settings.STATIC_ROOT)
    os.makedirs(_whitenoise_root, exist_ok=True)
    application = WhiteNoise(application, root=_whitenoise_root, autorefresh=False, prefix='static/')
else:
    # Add each static files dir as a WhiteNoise root
    for static_dir in _whitenoise_dirs:
        application = WhiteNoise(application, root=static_dir, prefix='static/')
