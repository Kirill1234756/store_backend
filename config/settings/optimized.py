from .base import *
import os

# Database Configuration for High Load
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'store_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'pgbouncer'),  # Use PgBouncer
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'django_app',
            'options': '-c default_transaction_isolation=read_committed -c timezone=UTC',
        },
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'store_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_REPLICA_HOST', 'postgresql_replica'),
        'PORT': os.getenv('DB_REPLICA_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'django_app_replica',
            'options': '-c default_transaction_isolation=read_committed -c timezone=UTC',
        },
    },
    'analytics': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('TIMESCALEDB_NAME', 'store_db_analytics'),
        'USER': os.getenv('TIMESCALEDB_USER', 'postgres'),
        'PASSWORD': os.getenv('TIMESCALEDB_PASSWORD', 'postgres'),
        'HOST': os.getenv('TIMESCALEDB_HOST', 'timescaledb'),
        'PORT': os.getenv('TIMESCALEDB_PORT', '5432'),
        'CONN_MAX_AGE': 300,  # Longer connections for analytics
        'OPTIONS': {
            'connect_timeout': 30,
            'application_name': 'django_analytics',
            'options': '-c default_transaction_isolation=read_committed -c timezone=UTC',
        },
    },
}

# Database Router for Read/Write splitting
DATABASE_ROUTERS = ['config.routers.DatabaseRouter']

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'store',
        'TIMEOUT': 900,  # 15 minutes
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 3600,  # 1 hour
    },
    'analytics': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 10,
            'SOCKET_TIMEOUT': 10,
            'RETRY_ON_TIMEOUT': True,
        },
        'KEY_PREFIX': 'analytics',
        'TIMEOUT': 3600,  # 1 hour for analytics
    },
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Celery Worker Settings
CELERY_WORKER_CONCURRENCY = int(os.getenv('CELERY_WORKER_CONCURRENCY', 100))
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', 4))
CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.getenv('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000))
CELERY_WORKER_MAX_MEMORY_PER_CHILD = int(os.getenv('CELERY_WORKER_MAX_MEMORY_PER_CHILD', 200000))  # 200MB

# Celery Task Settings
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True

# Celery Queue Settings
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

# Celery Beat Settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Monitoring
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_EVENT_QUEUE_EXPIRES = 60

# Celery Security
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True

# ============================================================================
# ASYNC CONFIGURATION
# ============================================================================

# ASGI Configuration
ASGI_APPLICATION = 'config.asgi.application'

# Async Settings
DJANGO_ALLOW_ASYNC_UNSAFE = os.getenv('DJANGO_ALLOW_ASYNC_UNSAFE', 'False').lower() == 'true'

# Async Database Settings
DATABASES['default']['OPTIONS']['async_connection'] = True
DATABASES['replica']['OPTIONS']['async_connection'] = True

# Async Cache Settings
CACHES['default']['OPTIONS']['async_connection'] = True

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

# Database Optimization
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 100,
    'MIN_CONNS': 10,
    'CONN_MAX_AGE': 60,
    'CONN_HEALTH_CHECKS': True,
})

# Cache Optimization
CACHES['default']['OPTIONS'].update({
    'COMPRESSOR': 'lz4',
    'COMPRESS_MIN_LEN': 10,
    'COMPRESS_COMPRESSOR_LEVEL': 6,
})

# Session Optimization
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['celery', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'products': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF Settings
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# THIRD-PARTY INTEGRATIONS
# ============================================================================

# Google Vision API
GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
GOOGLE_VISION_ENDPOINT = 'https://vision.googleapis.com/v1/images:annotate'

# Payment Gateway
PAYMENT_GATEWAY_URL = os.getenv('PAYMENT_GATEWAY_URL', 'https://api.payment-gateway.com/v1/charges')
PAYMENT_GATEWAY_KEY = os.getenv('PAYMENT_GATEWAY_KEY')

# Email Service
EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL', 'https://api.email-service.com/v1/send')
EMAIL_SERVICE_KEY = os.getenv('EMAIL_SERVICE_KEY')

# FCM Push Notifications
FCM_URL = 'https://fcm.googleapis.com/fcm/send'
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY')

# Elasticsearch
ELASTICSEARCH_ENABLED = os.getenv('ELASTICSEARCH_ENABLED', 'False').lower() == 'true'
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')
ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT', 9200))

# ============================================================================
# MONITORING AND METRICS
# ============================================================================

# Prometheus Metrics
PROMETHEUS_EXPORT_MIGRATIONS = False

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING = True
PERFORMANCE_MONITORING_SAMPLE_RATE = 0.1  # 10% of requests

# ============================================================================
# FILE UPLOAD SETTINGS
# ============================================================================

# File Upload Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'media', 'temp')

# Image Processing
IMAGE_PROCESSING_ENABLED = True
IMAGE_MAX_SIZE = (1200, 1200)
IMAGE_QUALITY = 85
IMAGE_FORMAT = 'WEBP'

# ============================================================================
# BACKUP SETTINGS
# ============================================================================

# Backup Configuration
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
BACKUP_RETENTION_DAYS = 30
BACKUP_COMPRESSION = True

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Debug Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Development Tools
if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_extensions',
    ]
    
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
    # Debug Toolbar Configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }

# ============================================================================
# PRODUCTION SETTINGS
# ============================================================================

if not DEBUG:
    # Production Security
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
    
    # Static Files
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
    
    # Database Optimization for Production
    DATABASES['default']['OPTIONS'].update({
        'MAX_CONNS': 200,
        'MIN_CONNS': 20,
    })
    
    # Cache Optimization for Production
    CACHES['default']['OPTIONS'].update({
        'COMPRESSOR_LEVEL': 9,
    })
    
    # Celery Optimization for Production
    CELERY_WORKER_CONCURRENCY = 200
    CELERY_WORKER_PREFETCH_MULTIPLIER = 2 