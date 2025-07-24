import os
import sys
from pathlib import Path

# Добавляем путь к проекту
path = Path(__file__).resolve().parent
if str(path) not in sys.path:
    sys.path.append(str(path))

# Устанавливаем переменные окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
os.environ.setdefault('PYTHONPATH', str(path))

# Импортируем приложение Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 