#!/usr/bin/env python
"""
Скрипт для настройки и индексации Elasticsearch
"""

import os
import sys
import django
from django.conf import settings

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_elasticsearch_dsl.registries import registry
from products.models import Product
from products.search_indexes import ProductDocument
import time

def check_elasticsearch_connection():
    """Проверка подключения к Elasticsearch"""
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(['localhost:9200'])
        if es.ping():
            print("✅ Подключение к Elasticsearch успешно")
            return True
        else:
            print("❌ Не удалось подключиться к Elasticsearch")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Elasticsearch: {e}")
        return False

def create_indexes():
    """Создание индексов"""
    print("🔧 Создание индексов Elasticsearch...")
    
    try:
        for doc in registry.get_documents():
            print(f"Создание индекса для {doc._doc_type.model.__name__}...")
            doc._index.create()
            print(f"✅ Индекс для {doc._doc_type.model.__name__} создан")
        
        print("✅ Все индексы созданы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания индексов: {e}")
        return False

def index_data():
    """Индексация данных"""
    print("📊 Индексация данных...")
    
    try:
        for doc in registry.get_documents():
            model = doc._doc_type.model
            print(f"Индексация {model.__name__}...")
            
            # Получаем queryset для индексации
            queryset = doc().get_indexing_queryset()
            total_count = queryset.count()
            
            if total_count == 0:
                print(f"Нет данных для индексации в {model.__name__}")
                continue
            
            # Индексируем данные
            doc().update(queryset)
            
            print(f"✅ {model.__name__} проиндексирован: {total_count} записей")
        
        print("✅ Все данные проиндексированы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка индексации данных: {e}")
        return False

def check_index_status():
    """Проверка статуса индексов"""
    print("🔍 Проверка статуса индексов...")
    
    try:
        for doc in registry.get_documents():
            index_name = doc._index._name
            model_name = doc._doc_type.model.__name__
            
            if doc._index.exists():
                stats = doc._index.stats()
                doc_count = stats['indices'][index_name]['total']['docs']['count']
                print(f"✅ {model_name} -> {index_name} ({doc_count} документов)")
            else:
                print(f"❌ {model_name} -> {index_name} (не существует)")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Настройка Elasticsearch для проекта...")
    
    # Проверяем подключение
    if not check_elasticsearch_connection():
        print("❌ Не удалось подключиться к Elasticsearch. Убедитесь, что сервис запущен.")
        return False
    
    # Создаем индексы
    if not create_indexes():
        print("❌ Не удалось создать индексы")
        return False
    
    # Индексируем данные
    if not index_data():
        print("❌ Не удалось проиндексировать данные")
        return False
    
    # Проверяем статус
    if not check_index_status():
        print("❌ Ошибка проверки статуса")
        return False
    
    print("🎉 Elasticsearch успешно настроен!")
    print("📊 Kibana: http://localhost:5601")
    print("🔍 Elasticsearch: http://localhost:9200")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 