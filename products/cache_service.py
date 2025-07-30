from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from functools import wraps
import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from .models import Product, Category

logger = logging.getLogger(__name__)

class CacheService:
    """Многоуровневый сервис кэширования"""
    
    # Префиксы для разных типов кэша
    CACHE_PREFIXES = {
        'products': 'products',
        'categories': 'categories', 
        'search': 'search',
        'facets': 'facets',
        'stats': 'stats',
        'suggestions': 'suggestions',
        'elasticsearch': 'es',
        'templates': 'templates',
        'sessions': 'sessions'
    }
    
    # Время жизни кэша (в секундах)
    CACHE_TIMEOUTS = {
        'products': 60 * 15,      # 15 минут
        'categories': 60 * 60,     # 1 час
        'search': 60 * 5,          # 5 минут
        'facets': 60 * 10,         # 10 минут
        'stats': 60 * 30,          # 30 минут
        'suggestions': 60 * 10,    # 10 минут
        'elasticsearch': 60 * 5,   # 5 минут
        'templates': 60 * 60,      # 1 час
        'sessions': 60 * 60 * 24,  # 24 часа
    }
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """Генерация уникального ключа кэша"""
        # Создаем строку из аргументов
        key_parts = [prefix]
        
        # Добавляем позиционные аргументы
        for arg in args:
            key_parts.append(str(arg))
        
        # Добавляем именованные аргументы (сортированные)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for key, value in sorted_kwargs:
                key_parts.append(f"{key}:{value}")
        
        # Создаем хеш от строки
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    def get_cache_key(cls, cache_type: str, *args, **kwargs) -> str:
        """Получение ключа кэша с префиксом"""
        prefix = cls.CACHE_PREFIXES.get(cache_type, cache_type)
        return cls.generate_cache_key(prefix, *args, **kwargs)
    
    @classmethod
    def get_cache_timeout(cls, cache_type: str) -> int:
        """Получение времени жизни кэша"""
        return cls.CACHE_TIMEOUTS.get(cache_type, 300)  # 5 минут по умолчанию
    
    @classmethod
    def cache_result(cls, cache_type: str, timeout: Optional[int] = None):
        """Декоратор для кэширования результатов функций"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Генерируем ключ кэша
                cache_key = cls.get_cache_key(cache_type, *args, **kwargs)
                cache_timeout = timeout or cls.get_cache_timeout(cache_type)
                
                # Пытаемся получить из кэша
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for {cache_key}")
                    return cached_result
                
                # Выполняем функцию
                logger.debug(f"Cache MISS for {cache_key}")
                result = func(*args, **kwargs)
                
                # Сохраняем в кэш
                cache.set(cache_key, result, cache_timeout)
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    def cache_page(cls, timeout: int = 300, key_prefix: str = 'page'):
        """Декоратор для кэширования страниц"""
        def decorator(view_func):
            @cache_page(timeout, key_prefix=key_prefix)
            @vary_on_cookie
            @wraps(view_func)
            def wrapper(*args, **kwargs):
                return view_func(*args, **kwargs)
            return wrapper
        return decorator
    
    @classmethod
    def invalidate_cache(cls, cache_type: str, *args, **kwargs):
        """Инвалидация кэша по типу и параметрам"""
        cache_key = cls.get_cache_key(cache_type, *args, **kwargs)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")
    
    @classmethod
    def invalidate_product_cache(cls, product_id: int = None):
        """Инвалидация кэша продуктов"""
        if product_id:
            # Инвалидируем конкретный продукт
            cls.invalidate_cache('products', product_id)
            cls.invalidate_cache('search')  # Инвалидируем поиск
        else:
            # Инвалидируем все продукты
            cls.clear_cache_by_prefix('products')
            cls.clear_cache_by_prefix('search')
    
    @classmethod
    def invalidate_category_cache(cls, category_id: int = None):
        """Инвалидация кэша категорий"""
        if category_id:
            cls.invalidate_cache('categories', category_id)
        else:
            cls.clear_cache_by_prefix('categories')
    
    @classmethod
    def clear_cache_by_prefix(cls, prefix: str):
        """Очистка кэша по префиксу"""
        # Получаем все ключи с префиксом
        pattern = f"{cls.CACHE_PREFIXES.get(prefix, prefix)}_*"
        
        # В Redis можно использовать SCAN для поиска ключей
        # Но для простоты удаляем основные ключи
        cache.delete_pattern(pattern)
        logger.info(f"Cache cleared for prefix: {prefix}")
    
    @classmethod
    def get_cached_products(cls, filters: Dict = None, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """Получение кэшированных продуктов"""
        cache_key = cls.get_cache_key('products', filters, page, page_size)
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_products(cls, products_data: Dict, filters: Dict = None, page: int = 1, page_size: int = 20):
        """Сохранение продуктов в кэш"""
        cache_key = cls.get_cache_key('products', filters, page, page_size)
        timeout = cls.get_cache_timeout('products')
        cache.set(cache_key, products_data, timeout)
    
    @classmethod
    def get_cached_search_results(cls, query: str, filters: Dict = None) -> Optional[Dict]:
        """Получение кэшированных результатов поиска"""
        cache_key = cls.get_cache_key('search', query, filters)
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_search_results(cls, results: Dict, query: str, filters: Dict = None):
        """Сохранение результатов поиска в кэш"""
        cache_key = cls.get_cache_key('search', query, filters)
        timeout = cls.get_cache_timeout('search')
        cache.set(cache_key, results, timeout)
    
    @classmethod
    def get_cached_facets(cls, filters: Dict = None) -> Optional[Dict]:
        """Получение кэшированных фасетов"""
        cache_key = cls.get_cache_key('facets', filters)
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_facets(cls, facets: Dict, filters: Dict = None):
        """Сохранение фасетов в кэш"""
        cache_key = cls.get_cache_key('facets', filters)
        timeout = cls.get_cache_timeout('facets')
        cache.set(cache_key, facets, timeout)
    
    @classmethod
    def get_cached_suggestions(cls, query: str, limit: int = 5) -> Optional[List[str]]:
        """Получение кэшированных подсказок"""
        cache_key = cls.get_cache_key('suggestions', query, limit)
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_suggestions(cls, suggestions: List[str], query: str, limit: int = 5):
        """Сохранение подсказок в кэш"""
        cache_key = cls.get_cache_key('suggestions', query, limit)
        timeout = cls.get_cache_timeout('suggestions')
        cache.set(cache_key, suggestions, timeout)
    
    @classmethod
    def get_cached_stats(cls, stats_type: str) -> Optional[Dict]:
        """Получение кэшированной статистики"""
        cache_key = cls.get_cache_key('stats', stats_type)
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_stats(cls, stats: Dict, stats_type: str):
        """Сохранение статистики в кэш"""
        cache_key = cls.get_cache_key('stats', stats_type)
        timeout = cls.get_cache_timeout('stats')
        cache.set(cache_key, stats, timeout)
    
    @classmethod
    def cache_elasticsearch_results(cls, query: str, filters: Dict = None, results: Dict = None):
        """Кэширование результатов Elasticsearch"""
        if results:
            cache_key = cls.get_cache_key('elasticsearch', query, filters)
            timeout = cls.get_cache_timeout('elasticsearch')
            cache.set(cache_key, results, timeout)
        else:
            # Получение из кэша
            cache_key = cls.get_cache_key('elasticsearch', query, filters)
            return cache.get(cache_key)
    
    @classmethod
    def get_cache_stats(cls) -> Dict:
        """Получение статистики кэша"""
        try:
            # Получаем информацию о Redis через прямой клиент
            redis_client = cache.client.get_client()
            redis_info = redis_client.info()
            
            stats = {
                'used_memory': redis_info.get('used_memory_human', 'N/A'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'total_commands_processed': redis_info.get('total_commands_processed', 0),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0),
            }
            
            # Вычисляем hit rate
            total_requests = stats['keyspace_hits'] + stats['keyspace_misses']
            if total_requests > 0:
                stats['hit_rate'] = f"{(stats['keyspace_hits'] / total_requests) * 100:.2f}%"
            else:
                stats['hit_rate'] = "0%"
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    @classmethod
    def warm_cache(cls):
        """Прогрев кэша - загрузка популярных данных"""
        try:
            logger.info("Starting cache warm-up...")
            
            # Кэшируем популярные продукты
            from .serializers import ProductSerializer
            
            popular_products = Product.objects.filter(
                is_active=True, 
                is_top=True
            ).select_related('category', 'seller')[:20]
            
            for product in popular_products:
                cache_key = cls.get_cache_key('products', product.id)
                # Сериализуем продукт в JSON
                serializer = ProductSerializer(product)
                cache.set(cache_key, serializer.data, cls.get_cache_timeout('products'))
            
            # Кэшируем категории
            categories = Category.objects.all()
            for category in categories:
                cache_key = cls.get_cache_key('categories', category.id)
                cache.set(cache_key, category, cls.get_cache_timeout('categories'))
            
            # Кэшируем базовую статистику
            stats = {
                'total_products': Product.objects.filter(is_active=True).count(),
                'top_products': Product.objects.filter(is_active=True, is_top=True).count(),
                'total_categories': Category.objects.count(),
            }
            cls.set_cached_stats(stats, 'basic')
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.error(f"Error during cache warm-up: {e}")


# Декораторы для удобного использования
def cache_products(timeout: Optional[int] = None):
    """Декоратор для кэширования продуктов"""
    return CacheService.cache_result('products', timeout)

def cache_search(timeout: Optional[int] = None):
    """Декоратор для кэширования поиска"""
    return CacheService.cache_result('search', timeout)

def cache_facets(timeout: Optional[int] = None):
    """Декоратор для кэширования фасетов"""
    return CacheService.cache_result('facets', timeout)

def cache_suggestions(timeout: Optional[int] = None):
    """Декоратор для кэширования подсказок"""
    return CacheService.cache_result('suggestions', timeout)

def cache_stats(timeout: Optional[int] = None):
    """Декоратор для кэширования статистики"""
    return CacheService.cache_result('stats', timeout) 