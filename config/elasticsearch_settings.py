# Elasticsearch settings
ELASTICSEARCH_INDEX_NAMES = {
    'products.ProductDocument': 'products',
}

# Elasticsearch connection settings
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200'
    }
}

# Elasticsearch settings for development
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_DSL_AUTO_REFRESH = True

# Elasticsearch settings for production
if not DEBUG:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200'),
            'http_auth': (
                os.environ.get('ELASTICSEARCH_USER', 'elastic'),
                os.environ.get('ELASTICSEARCH_PASSWORD', '')
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