#!/usr/bin/env python
"""
Скрипт для тестирования производительности Elasticsearch vs PostgreSQL
"""

import os
import sys
import time
import requests
import django
from django.conf import settings

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product
from django.db import connection
from django.test import Client

def test_postgresql_search(query, filters=None):
    """Тест поиска через PostgreSQL"""
    start_time = time.time()
    
    queryset = Product.objects.filter(is_active=True)
    
    if query:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(phone_model__icontains=query)
        )
    
    if filters:
        if 'priceRange' in filters:
            min_price, max_price = map(float, filters['priceRange'].split(','))
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        
        if 'condition' in filters:
            queryset = queryset.filter(condition=filters['condition'])
    
    results = list(queryset[:20])  # Ограничиваем для сравнения
    end_time = time.time()
    
    return {
        'time': (end_time - start_time) * 1000,  # в миллисекундах
        'count': len(results),
        'engine': 'postgresql'
    }

def test_elasticsearch_search(query, filters=None):
    """Тест поиска через Elasticsearch API"""
    start_time = time.time()
    
    try:
        # Формируем URL для API запроса
        url = 'http://localhost:8000/api/products/'
        params = {}
        
        if query:
            params['search'] = query
        
        if filters:
            for key, value in filters.items():
                params[key] = value
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            end_time = time.time()
            
            return {
                'time': (end_time - start_time) * 1000,  # в миллисекундах
                'count': data.get('count', 0),
                'engine': data.get('search_engine', 'unknown')
            }
        else:
            return {
                'time': 0,
                'count': 0,
                'engine': 'error',
                'error': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'time': 0,
            'count': 0,
            'engine': 'error',
            'error': str(e)
        }

def test_suggestions(query):
    """Тест автодополнения"""
    start_time = time.time()
    
    try:
        url = f'http://localhost:8000/api/products/suggest/?q={query}&limit=5'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            end_time = time.time()
            
            return {
                'time': (end_time - start_time) * 1000,
                'suggestions': len(data.get('suggestions', [])),
                'engine': 'elasticsearch'
            }
        else:
            return {
                'time': 0,
                'suggestions': 0,
                'engine': 'error'
            }
    except Exception as e:
        return {
            'time': 0,
            'suggestions': 0,
            'engine': 'error',
            'error': str(e)
        }

def test_facets():
    """Тест фасетного поиска"""
    start_time = time.time()
    
    try:
        url = 'http://localhost:8000/api/products/facets/'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            end_time = time.time()
            
            return {
                'time': (end_time - start_time) * 1000,
                'facets': len(data),
                'engine': 'elasticsearch'
            }
        else:
            return {
                'time': 0,
                'facets': 0,
                'engine': 'error'
            }
    except Exception as e:
        return {
            'time': 0,
            'facets': 0,
            'engine': 'error',
            'error': str(e)
        }

def run_performance_tests():
    """Запуск всех тестов производительности"""
    print("🚀 Тестирование производительности Elasticsearch vs PostgreSQL")
    print("=" * 60)
    
    # Тестовые запросы
    test_queries = [
        "iPhone",
        "Samsung",
        "Pro",
        "256GB",
        "black",
        "A",  # condition
    ]
    
    # Тестовые фильтры
    test_filters = [
        {'priceRange': '0,50000'},
        {'condition': 'A'},
        {'color': 'black'},
        {'priceRange': '0,50000', 'condition': 'A'},
    ]
    
    print("\n📊 Результаты тестов поиска:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\n🔍 Поиск: '{query}'")
        
        # PostgreSQL
        pg_result = test_postgresql_search(query)
        print(f"  PostgreSQL: {pg_result['time']:.2f}ms, {pg_result['count']} результатов")
        
        # Elasticsearch
        es_result = test_elasticsearch_search(query)
        print(f"  Elasticsearch: {es_result['time']:.2f}ms, {es_result['count']} результатов")
        
        if es_result['engine'] != 'error':
            speedup = pg_result['time'] / es_result['time'] if es_result['time'] > 0 else 0
            print(f"  ⚡ Ускорение: {speedup:.1f}x")
    
    print("\n📊 Результаты тестов фильтрации:")
    print("-" * 40)
    
    for filters in test_filters:
        print(f"\n🔍 Фильтры: {filters}")
        
        # PostgreSQL
        pg_result = test_postgresql_search("", filters)
        print(f"  PostgreSQL: {pg_result['time']:.2f}ms, {pg_result['count']} результатов")
        
        # Elasticsearch
        es_result = test_elasticsearch_search("", filters)
        print(f"  Elasticsearch: {es_result['time']:.2f}ms, {es_result['count']} результатов")
        
        if es_result['engine'] != 'error':
            speedup = pg_result['time'] / es_result['time'] if es_result['time'] > 0 else 0
            print(f"  ⚡ Ускорение: {speedup:.1f}x")
    
    print("\n📊 Тест автодополнения:")
    print("-" * 40)
    
    for query in ["iph", "sam", "pro"]:
        result = test_suggestions(query)
        print(f"  '{query}': {result['time']:.2f}ms, {result['suggestions']} подсказок")
    
    print("\n📊 Тест фасетного поиска:")
    print("-" * 40)
    
    result = test_facets()
    print(f"  Фасеты: {result['time']:.2f}ms, {result['facets']} категорий")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    run_performance_tests() 