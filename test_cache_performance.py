#!/usr/bin/env python
import os
import sys
import django
import time
import requests
from django.conf import settings

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from products.cache_service import CacheService
from products.models import Product
from django.core.cache import cache

def test_cache_performance():
    """Тестирование производительности кэширования"""
    print("🚀 Тестирование производительности кэширования")
    print("=" * 50)
    
    # Тест 1: Запись в кэш
    print("\n📝 Тест 1: Запись в кэш")
    write_times = []
    for i in range(100):
        key = f'test_key_{i}'
        value = f'test_value_{i}'
        start = time.time()
        cache.set(key, value, timeout=60)
        write_times.append(time.time() - start)
    
    avg_write_time = sum(write_times) / len(write_times)
    print(f"Среднее время записи: {avg_write_time * 1000:.2f}ms")
    
    # Тест 2: Чтение из кэша
    print("\n📖 Тест 2: Чтение из кэша")
    read_times = []
    for i in range(100):
        key = f'test_key_{i}'
        start = time.time()
        cache.get(key)
        read_times.append(time.time() - start)
    
    avg_read_time = sum(read_times) / len(read_times)
    print(f"Среднее время чтения: {avg_read_time * 1000:.2f}ms")
    
    # Тест 3: Массовые операции
    print("\n📦 Тест 3: Массовые операции")
    data = {f'bulk_key_{i}': f'bulk_value_{i}' for i in range(50)}
    
    start = time.time()
    cache.set_many(data, timeout=60)
    bulk_write_time = time.time() - start
    
    start = time.time()
    cache.get_many(data.keys())
    bulk_read_time = time.time() - start
    
    print(f"Время массовой записи (50 ключей): {bulk_write_time * 1000:.2f}ms")
    print(f"Время массового чтения (50 ключей): {bulk_read_time * 1000:.2f}ms")
    
    # Тест 4: Кэширование продуктов
    print("\n🛍️ Тест 4: Кэширование продуктов")
    
    # Получаем продукты из БД
    start = time.time()
    products = list(Product.objects.filter(is_active=True)[:10])
    db_time = time.time() - start
    
    # Кэшируем продукты (сериализуем в JSON)
    from products.serializers import ProductSerializer
    start = time.time()
    for product in products:
        cache_key = CacheService.get_cache_key('products', product.id)
        # Сериализуем продукт в JSON
        serializer = ProductSerializer(product)
        cache.set(cache_key, serializer.data, CacheService.get_cache_timeout('products'))
    cache_write_time = time.time() - start
    
    # Читаем из кэша
    start = time.time()
    cached_products = []
    for product in products:
        cache_key = CacheService.get_cache_key('products', product.id)
        cached_product = cache.get(cache_key)
        if cached_product:
            cached_products.append(cached_product)
    cache_read_time = time.time() - start
    
    print(f"Время чтения из БД: {db_time * 1000:.2f}ms")
    print(f"Время записи в кэш: {cache_write_time * 1000:.2f}ms")
    print(f"Время чтения из кэша: {cache_read_time * 1000:.2f}ms")
    print(f"Ускорение чтения: {db_time / cache_read_time:.1f}x")
    
    # Тест 5: Статистика кэша
    print("\n📊 Тест 5: Статистика кэша")
    stats = CacheService.get_cache_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Очистка тестовых данных
    print("\n🧹 Очистка тестовых данных...")
    for i in range(100):
        cache.delete(f'test_key_{i}')
    for key in data.keys():
        cache.delete(key)
    for product in products:
        cache_key = CacheService.get_cache_key('products', product.id)
        cache.delete(cache_key)
    
    print("✅ Тестирование завершено!")

def test_api_caching():
    """Тестирование кэширования API"""
    print("\n🌐 Тестирование кэширования API")
    print("=" * 40)
    
    # Запускаем Django сервер если не запущен
    base_url = "http://localhost:8000"
    
    # Тест API без кэша
    print("\n📝 Тест API без кэша:")
    start = time.time()
    try:
        response = requests.get(f"{base_url}/api/products/", timeout=10)
        no_cache_time = time.time() - start
        print(f"Время ответа: {no_cache_time * 1000:.2f}ms")
        print(f"Статус: {response.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")
        return
    
    # Тест API с кэшем (повторный запрос)
    print("\n📖 Тест API с кэшем:")
    start = time.time()
    try:
        response = requests.get(f"{base_url}/api/products/", timeout=10)
        cache_time = time.time() - start
        print(f"Время ответа: {cache_time * 1000:.2f}ms")
        print(f"Статус: {response.status_code}")
        
        if no_cache_time > 0:
            speedup = no_cache_time / cache_time
            print(f"Ускорение: {speedup:.1f}x")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_cache_performance()
    test_api_caching() 