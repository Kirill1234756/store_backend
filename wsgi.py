import os
import sys

path = '/home/cy16820/store_backend'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 