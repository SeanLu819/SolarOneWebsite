import os
import sys

# Add project root to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

# Trigger collectstatic if not already done
os.environ.setdefault('STATIC_ROOT', os.path.join(BASE_DIR, 'staticfiles'))

# Static files handling with whitenoise
from django.core.wsgi import get_wsgi_application
from django.conf import settings

# Ensure collectstatic has been run
if not os.path.exists(settings.STATIC_ROOT):
    import subprocess
    subprocess.check_call([sys.executable, 'manage.py', 'collectstatic', '--noinput'],
                          cwd=BASE_DIR, env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'solarone.settings'})

from whitenoise import WhiteNoise

application = get_wsgi_application()
application = WhiteNoise(application, root=settings.STATIC_ROOT, prefixes=['/static/', '/staticfiles/'])
