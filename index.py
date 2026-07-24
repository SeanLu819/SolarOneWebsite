import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.core.management import call_command

# Run migrations silently on cold start to create tables in ephemeral DB
try:
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception:
    pass

application = get_wsgi_application()

from whitenoise import WhiteNoise

# WhiteNoise serves static files from STATIC_ROOT (populated by collectstatic during build)
# If STATIC_ROOT doesn't exist (build skipped), WhiteNoise will simply return 404 for static files
_whitenoise_root = str(settings.STATIC_ROOT)
if not os.path.isdir(_whitenoise_root):
    os.makedirs(_whitenoise_root, exist_ok=True)

application = WhiteNoise(application, root=_whitenoise_root, autorefresh=False, prefix='static/')
