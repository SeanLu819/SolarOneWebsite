"""
WSGI config for solarone project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

application = get_wsgi_application()
