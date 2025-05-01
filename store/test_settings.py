from store.settings import *
import django

# Initialize Django
django.setup()

# Override settings for tests
DEBUG = True
SECRET_KEY = 'test-secret-key'

# Use SQLite in memory for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use DummyCache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Use database session engine for tests
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable CORS for tests
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False

# Disable pagination for tests
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': None,
    'PAGE_SIZE': None,
} 