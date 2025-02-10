"""
WSGI config for etag project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etag.settings.production')

application = get_wsgi_application() 