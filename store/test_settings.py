from store.settings import *

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

# Disable Redis for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable Redis session engine
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