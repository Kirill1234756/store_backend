from .production import *
import os

# =============================================================================
# REDIS PRODUCTION CONFIGURATION
# =============================================================================

# Redis Cluster Configuration (for high availability)
REDIS_CLUSTER_NODES = os.getenv('REDIS_CLUSTER_NODES', '').split(',') if os.getenv('REDIS_CLUSTER_NODES') else []

# Advanced Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 200,  # Increased for high load
                'timeout': 20,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'MAX_CONNECTIONS': 5000,  # Increased connection pool
            'RETRY_ON_TIMEOUT': True,
            'SOCKET_TIMEOUT': 5,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'COMPRESSOR_CLASS': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'PARSER_CLASS': 'redis.connection.HiredisParser',  # Faster parser
            'MASTER_CACHE': 'redis://redis:6379/1',
            'REPLICA_CACHE': 'redis://redis:6379/2',
        },
        'KEY_PREFIX': 'store_prod',
        'TIMEOUT': 60 * 60 * 2,  # 2 hours
        'VERSION': 1,
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 100,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 2000,
            'RETRY_ON_TIMEOUT': True,
            'SOCKET_TIMEOUT': 5,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'COMPRESSOR_CLASS': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'session_prod',
        'TIMEOUT': 60 * 60 * 24,  # 24 hours
    },
    'celery': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 300,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 3000,
            'RETRY_ON_TIMEOUT': True,
            'SOCKET_TIMEOUT': 5,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'COMPRESSOR_CLASS': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'celery_prod',
        'TIMEOUT': 60 * 60 * 6,  # 6 hours
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# CELERY PRODUCTION OPTIMIZATION
# =============================================================================

# Celery Configuration for High Load
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db')
CELERY_CACHE_BACKEND = 'celery'

# Task Configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60 * 60  # 1 hour
CELERY_TASK_SOFT_TIME_LIMIT = 50 * 60  # 50 minutes
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Reduced for better distribution
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 300000  # 300MB
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_EVENT_QUEUE_EXPIRES = 60
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True

# Queue Configuration
CELERY_TASK_ROUTES = {
    'products.tasks.process_images': {'queue': 'media'},
    'products.tasks.optimize_images': {'queue': 'media'},
    'products.tasks.generate_thumbnails': {'queue': 'media'},
    'products.tasks.ai_analyze_image': {'queue': 'ai'},
    'products.tasks.update_search_index': {'queue': 'search'},
    'products.tasks.send_notifications': {'queue': 'notifications'},
    'products.tasks.process_payment': {'queue': 'high_priority'},
    'products.tasks.fraud_check': {'queue': 'high_priority'},
    'products.tasks.update_analytics': {'queue': 'analytics'},
    'products.tasks.cleanup_expired': {'queue': 'maintenance'},
    'products.tasks.backup_database': {'queue': 'maintenance'},
    'products.tasks.sync_elasticsearch': {'queue': 'search'},
    'products.tasks.update_cache': {'queue': 'cache'},
    'products.tasks.process_bulk_operations': {'queue': 'bulk'},
}

# Task Priority Configuration
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

# =============================================================================
# DATABASE PRODUCTION OPTIMIZATION
# =============================================================================

# Database Connection Pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'store_db'),
        'USER': os.getenv('DB_USER', 'store_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'django_app_prod',
            'options': '-c default_transaction_isolation=read_committed',
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'store_db'),
        'USER': os.getenv('DB_USER', 'store_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_REPLICA_HOST', 'postgresql_replica'),
        'PORT': os.getenv('DB_REPLICA_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'django_app_prod_replica',
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
    },
    'analytics': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_ANALYTICS_NAME', 'store_db_analytics'),
        'USER': os.getenv('DB_USER', 'store_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_ANALYTICS_HOST', 'timescaledb'),
        'PORT': os.getenv('DB_ANALYTICS_PORT', '5432'),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'django_app_prod_analytics',
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
    }
}

# Database Router Configuration
DATABASE_ROUTERS = [
    'config.routers.DatabaseRouter',
    'config.routers.AnalyticsRouter',
    'config.routers.CacheRouter',
    'config.routers.ReadOnlyRouter',
    'config.routers.CompositeRouter',
]

# =============================================================================
# ASYNC CONFIGURATION
# =============================================================================

# ASGI Configuration
ASGI_APPLICATION = 'config.asgi.application'
DJANGO_ALLOW_ASYNC_UNSAFE = os.getenv('DJANGO_ALLOW_ASYNC_UNSAFE', 'False').lower() == 'true'

# =============================================================================
# PERFORMANCE OPTIMIZATION
# =============================================================================

# Cache Middleware
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 60 * 30  # 30 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'store_prod'

# Static Files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

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
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '..', 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '..', 'logs', 'celery.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
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
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# =============================================================================
# SECURITY ENHANCEMENTS
# =============================================================================

# Additional Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================

# Prometheus Metrics
PROMETHEUS_EXPORT_MIGRATIONS = False
PROMETHEUS_EXPORT_ADDRESS = '0.0.0.0'
PROMETHEUS_EXPORT_PORT = 8001

# Health Check
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percentage
    'MEMORY_MIN': 100,  # MB
}

# =============================================================================
# THIRD-PARTY INTEGRATIONS
# =============================================================================

# Elasticsearch Configuration
ELASTICSEARCH_INDEX_NAMES = {
    'products.Product': 'products',
}

# Email Configuration (Production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@cy16820.tw1.ru')

# =============================================================================
# FILE UPLOAD CONFIGURATION
# =============================================================================

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, '..', 'temp')

# =============================================================================
# BACKUP CONFIGURATION
# =============================================================================

# Backup Settings
BACKUP_DIR = os.path.join(BASE_DIR, '..', 'backups')
BACKUP_RETENTION_DAYS = 30

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================

# Override for development testing
if os.getenv('DJANGO_ENV') == 'development':
    DEBUG = True
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True 