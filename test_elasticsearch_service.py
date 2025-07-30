#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from products.search_service import ProductSearchService
import time

def test_elasticsearch_service():
    """Тестирование обновленного ProductSearchService"""
    try:
        print("🔍 Тестирование ProductSearchService...")
        
        # Создаем экземпляр сервиса
        service = ProductSearchService()
        
        # Тест 1: Поиск по запросу
        print("\n📝 Тест 1: Поиск 'iPhone'")
        start_time = time.time()
        products, total = service.search_products(query="iPhone", page=1, page_size=10)
        end_time = time.time()
        
        print(f"  Время: {(end_time - start_time) * 1000:.2f}ms")
        print(f"  Найдено: {total} продуктов")
        print(f"  Первые 3: {[p.title for p in products[:3]]}")
        
        # Тест 2: Фильтрация по цене
        print("\n📝 Тест 2: Фильтр по цене 0-50000")
        start_time = time.time()
        products, total = service.search_products(
            filters={'priceRange': '0,50000'}, 
            page=1, 
            page_size=10
        )
        end_time = time.time()
        
        print(f"  Время: {(end_time - start_time) * 1000:.2f}ms")
        print(f"  Найдено: {total} продуктов")
        print(f"  Первые 3: {[p.title for p in products[:3]]}")
        
        # Тест 3: Комбинированный поиск
        print("\n📝 Тест 3: Поиск + фильтры")
        start_time = time.time()
        products, total = service.search_products(
            query="iPhone",
            filters={'priceRange': '0,50000', 'condition': 'A'}, 
            page=1, 
            page_size=10
        )
        end_time = time.time()
        
        print(f"  Время: {(end_time - start_time) * 1000:.2f}ms")
        print(f"  Найдено: {total} продуктов")
        print(f"  Первые 3: {[p.title for p in products[:3]]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    success = test_elasticsearch_service()
    sys.exit(0 if success else 1) 