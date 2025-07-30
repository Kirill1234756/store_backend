#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from elasticsearch import Elasticsearch
from products.search_indexes import ProductDocument

def create_index():
    """Создание индекса Elasticsearch"""
    try:
        # Подключаемся к Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])
        
        # Проверяем подключение
        if not es.ping():
            print("❌ Не удалось подключиться к Elasticsearch")
            return False
        
        print("✅ Подключение к Elasticsearch успешно")
        
        # Создаем индекс
        index_name = 'products'
        if es.indices.exists(index=index_name):
            print(f"Индекс {index_name} уже существует")
            return True
        
        # Создаем маппинг
        mapping = {
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "russian",
                        "fields": {
                            "raw": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "russian",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "phone_model": {
                        "type": "text",
                        "analyzer": "russian",
                        "fields": {
                            "raw": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "price": {"type": "float"},
                    "condition": {"type": "keyword"},
                    "is_active": {"type": "boolean"},
                    "is_top": {"type": "boolean"},
                    "color": {"type": "keyword"},
                    "storage": {"type": "keyword"},
                    "screen_size": {"type": "float"},
                    "body_condition": {"type": "keyword"},
                    "screen_condition": {"type": "keyword"},
                    "battery_health": {"type": "integer"},
                    "turbo": {"type": "boolean"},
                    "city": {
                        "type": "text",
                        "analyzer": "russian",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "package_contents": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "category_name": {
                        "type": "text",
                        "analyzer": "russian",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "seller_username": {"type": "keyword"},
                    "rating": {"type": "float"},
                    "main_image_url": {"type": "keyword"},
                    "image_count": {"type": "integer"},
                    "display": {"type": "keyword"},
                    "imei": {"type": "keyword"},
                    "sim": {"type": "integer"},
                    "face": {"type": "boolean"},
                    "market": {"type": "keyword"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "russian": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "russian_stop", "russian_stemmer"]
                        }
                    },
                    "filter": {
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_"
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian"
                        }
                    }
                }
            }
        }
        
        # Создаем индекс
        es.indices.create(index=index_name, body=mapping)
        print(f"✅ Индекс {index_name} создан успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания индекса: {e}")
        return False

if __name__ == "__main__":
    success = create_index()
    sys.exit(0 if success else 1) 