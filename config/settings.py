import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import sys
import codecs

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-1234567890'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False  # Безопаснее явно указывать разрешенные домены
CORS_ALLOW_CREDENTIALS = True

# Разрешенные домены для продакшена и разработки
CORS_ALLOWED_ORIGINS = [
    "https://cy16820.tw1.ru",
    "https://www.cy16820.tw1.ru",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# Регулярные выражения для дополнительных доменов
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.cy16820\.tw1\.ru$",
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$"
]

# Разрешенные методы
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Разрешенные заголовки
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Заголовки, доступные для JavaScript
CORS_EXPOSE_HEADERS = ['content-type', 'content-length']

# Время кэширования preflight запросов
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 часа

# Применять CORS только к API эндпоинтам
CORS_URLS_REGEX = r'^/api/.*$'

# Настройки для разработки
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    # Настройки для продакшена
    CORS_ALLOW_ALL_ORIGINS = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Настройки куки
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Домен для куки (только для продакшена)
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.cy16820.tw1.ru'
    CSRF_COOKIE_DOMAIN = '.cy16820.tw1.ru'
else:
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'django_extensions',
    'django_elasticsearch_dsl',  # Elasticsearch support
    'products',
]

# Console encoding settings
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Middleware order is important
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Кэширование middleware
    'products.middleware.PerformanceMiddleware',
    'products.middleware.CacheControlMiddleware',
    'products.middleware.ETagMiddleware',
    'products.middleware.CompressionMiddleware',
    'products.middleware.CacheInvalidationMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'shop_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        }
    }
}

# Cache time to live is 15 minutes
CACHE_TTL = 60 * 15

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'

# Cache middleware settings
CACHE_MIDDLEWARE_SECONDS = CACHE_TTL
CACHE_MIDDLEWARE_KEY_PREFIX = 'store'

# Security settings (consolidated)
# Удаляю дублирующие и конфликтующие настройки безопасности и cookies
# (SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD, SECURE_PROXY_SSL_HEADER, SECURE_BROWSER_XSS_FILTER, SECURE_CONTENT_TYPE_NOSNIFF, X_FRAME_OPTIONS)
# Все эти параметры должны задаваться только в соответствующих файлах base/development/production

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

# Static files optimization
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year

# Gunicorn settings
GUNICORN_CMD_ARGS = '--workers=4 --threads=2 --timeout=60 --keep-alive=5'

# Monitoring and logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'products': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Security headers
# Удаляю дублирующие и конфликтующие настройки безопасности и cookies
# (SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD, SECURE_PROXY_SSL_HEADER, SECURE_BROWSER_XSS_FILTER, SECURE_CONTENT_TYPE_NOSNIFF, X_FRAME_OPTIONS)
# Все эти параметры должны задаваться только в соответствующих файлах base/development/production

# Database backup settings
BACKUP_ROOT = os.path.join(BASE_DIR, 'backups')
BACKUP_FORMAT = 'zip'
BACKUP_FILENAME_TEMPLATE = '{datetime}.{extension}'
BACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
BACKUP_STORAGE_OPTIONS = {
    'location': BACKUP_ROOT,
}

# Backup schedule (using cron syntax)
BACKUP_SCHEDULE = {
    'daily': '0 0 * * *',  # Every day at midnight
    'weekly': '0 0 * * 0',  # Every Sunday at midnight
    'monthly': '0 0 1 * *',  # First day of every month at midnight
}

# Backup retention
BACKUP_RETENTION = {
    'daily': 7,    # Keep daily backups for 7 days
    'weekly': 4,   # Keep weekly backups for 4 weeks
    'monthly': 12,  # Keep monthly backups for 12 months
}

# Advanced security settings
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = 'require-corp'
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = 'same-origin'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_UPGRADE_INSECURE_REQUESTS = True

# Advanced CORS settings
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.example\.com$",
]
CORS_ALLOW_HEADERS += [
    'x-api-key',
    'x-request-id',
]
CORS_PREFLIGHT_MAX_AGE = 86400

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_KEY_PREFIX = 'ratelimit'
RATELIMIT_BLOCK = True

# Session security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Other settings...

# Elasticsearch settings
ELASTICSEARCH_INDEX_NAMES = {
    'products.ProductDocument': 'products',
}

# Elasticsearch connection settings
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
    }
}

# Elasticsearch settings for development
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_DSL_AUTO_REFRESH = True

# Elasticsearch settings for production
if not DEBUG:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200'),
            'http_auth': (
                os.getenv('ELASTICSEARCH_USER', 'elastic'),
                os.getenv('ELASTICSEARCH_PASSWORD', '')
            ),
            'use_ssl': True,
            'verify_certs': False,
            'ssl_show_warn': False,
        }
    }
    
    # Отключаем автосинхронизацию в продакшене
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ELASTICSEARCH_DSL_AUTO_REFRESH = False

# Elasticsearch index settings
ELASTICSEARCH_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0,
    'analysis': {
        'analyzer': {
            'russian': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': ['lowercase', 'russian_stop', 'russian_stemmer']
            },
            'russian_exact': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': ['lowercase']
            }
        },
        'filter': {
            'russian_stop': {
                'type': 'stop',
                'stopwords': '_russian_'
            },
            'russian_stemmer': {
                'type': 'stemmer',
                'language': 'russian'
            }
        }
    }
}

# Elasticsearch bulk settings
ELASTICSEARCH_DSL_BULK_SIZE = 1000
ELASTICSEARCH_DSL_BULK_TIMEOUT = 30

# Elasticsearch connection pool settings
ELASTICSEARCH_DSL_CONNECTION_POOL = {
    'maxsize': 25,
    'retry_on_timeout': True,
    'timeout': 30,
    'max_retries': 3
}

# Elasticsearch logging
ELASTICSEARCH_DSL_LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Feature flag for Elasticsearch
ELASTICSEARCH_ENABLED = os.getenv('ELASTICSEARCH_ENABLED', 'true').lower() == 'true'
