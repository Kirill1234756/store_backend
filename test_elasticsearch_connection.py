#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Импортируем документ после настройки Django
from products.search_indexes import ProductDocument

from elasticsearch import Elasticsearch
from django_elasticsearch_dsl.registries import registry

def test_connection():
    """Тестирование подключения к Elasticsearch"""
    try:
        print("🔍 Тестирование подключения к Elasticsearch...")
        
        # Проверяем настройки
        print(f"ELASTICSEARCH_ENABLED: {getattr(settings, 'ELASTICSEARCH_ENABLED', False)}")
        print(f"ELASTICSEARCH_DSL: {getattr(settings, 'ELASTICSEARCH_DSL', 'NOT_FOUND')}")
        
        # Прямое подключение
        es = Elasticsearch(['http://localhost:9200'])
        if es.ping():
            print("✅ Прямое подключение к Elasticsearch успешно")
        else:
            print("❌ Прямое подключение к Elasticsearch не удалось")
            return False
        
        # Проверяем документы в registry
        documents = registry.get_documents()
        print(f"📄 Найдено документов в registry: {len(documents)}")
        
        for doc in documents:
            print(f"  - {doc.__name__}")
            print(f"    Index: {doc._index._name}")
            print(f"    Model: {doc.Django.model.__name__}")
            
            # Проверяем подключение документа
            try:
                search = doc.search()
                print(f"    ✅ Поиск работает")
            except Exception as e:
                print(f"    ❌ Ошибка поиска: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 