import time
import hashlib
import json
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CacheMiddleware(MiddlewareMixin):
    """Middleware для кэширования HTTP-ответов"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache_timeout = getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 300)
        self.cache_prefix = getattr(settings, 'CACHE_MIDDLEWARE_KEY_PREFIX', 'http')
    
    def process_request(self, request):
        """Обработка входящего запроса"""
        # Пропускаем POST, PUT, DELETE запросы
        if request.method not in ['GET', 'HEAD']:
            return None
        
        # Пропускаем запросы с авторизацией
        if request.user.is_authenticated:
            return None
        
        # Генерируем ключ кэша
        cache_key = self._generate_cache_key(request)
        
        # Пытаемся получить из кэша
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.debug(f"Cache HIT for {request.path}")
            return cached_response
        
        # Сохраняем запрос для обработки в process_response
        request._cache_key = cache_key
        return None
    
    def process_response(self, request, response):
        """Обработка исходящего ответа"""
        # Проверяем, нужно ли кэшировать
        if not hasattr(request, '_cache_key'):
            return response
        
        # Кэшируем только успешные GET-запросы
        if (request.method == 'GET' and 
            response.status_code == 200 and 
            'application/json' in response.get('Content-Type', '')):
            
            cache_key = request._cache_key
            cache.set(cache_key, response, self.cache_timeout)
            logger.debug(f"Cache SET for {request.path}")
        
        return response
    
    def _generate_cache_key(self, request):
        """Генерация ключа кэша для запроса"""
        # Создаем строку из URL и параметров
        key_parts = [
            self.cache_prefix,
            request.path,
            request.GET.urlencode()
        ]
        
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware для мониторинга производительности"""
    
    def process_request(self, request):
        """Засекаем время начала обработки"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Измеряем время обработки запроса"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Логируем медленные запросы
            if duration > 1.0:  # Больше 1 секунды
                logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
            
            # Добавляем заголовок с временем обработки
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """Middleware для установки заголовков кэширования"""
    
    def process_response(self, request, response):
        """Устанавливаем заголовки кэширования"""
        
        # Для статических файлов
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 год
            response['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
        
        # Для API ответов
        elif request.path.startswith('/api/'):
            if request.method == 'GET':
                response['Cache-Control'] = 'public, max-age=300'  # 5 минут
            else:
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
        
        # Для HTML страниц
        else:
            response['Cache-Control'] = 'public, max-age=60'  # 1 минута
        
        return response


class ETagMiddleware(MiddlewareMixin):
    """Middleware для поддержки ETag"""
    
    def process_request(self, request):
        """Проверяем ETag в запросе"""
        if request.method not in ['GET', 'HEAD']:
            return None
        
        etag = request.META.get('HTTP_IF_NONE_MATCH')
        if etag:
            # Генерируем ETag для текущего запроса
            current_etag = self._generate_etag(request)
            
            if etag.strip('"') == current_etag:
                # Контент не изменился
                response = HttpResponse(status=304)
                response['ETag'] = f'"{current_etag}"'
                return response
        
        return None
    
    def process_response(self, request, response):
        """Добавляем ETag к ответу"""
        if request.method in ['GET', 'HEAD'] and response.status_code == 200:
            etag = self._generate_etag(request)
            response['ETag'] = f'"{etag}"'
        
        return response
    
    def _generate_etag(self, request):
        """Генерация ETag для запроса"""
        # Создаем строку из URL и параметров
        key_parts = [
            request.path,
            request.GET.urlencode(),
            str(request.user.id if request.user.is_authenticated else 'anonymous')
        ]
        
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class CompressionMiddleware(MiddlewareMixin):
    """Middleware для сжатия ответов"""
    
    def process_response(self, request, response):
        """Сжимаем ответ если возможно"""
        # Проверяем, поддерживает ли клиент сжатие
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        if 'gzip' in accept_encoding and len(response.content) > 1024:
            # Здесь можно добавить логику сжатия
            # Для простоты просто добавляем заголовок
            response['Content-Encoding'] = 'gzip'
        
        return response


class CacheInvalidationMiddleware(MiddlewareMixin):
    """Middleware для автоматической инвалидации кэша"""
    
    def process_response(self, request, response):
        """Инвалидируем кэш при изменениях"""
        
        # При создании/обновлении/удалении продуктов
        if (request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and 
            '/api/products/' in request.path):
            
            # Инвалидируем кэш продуктов
            from .cache_service import CacheService
            CacheService.invalidate_product_cache()
        
        # При изменениях категорий
        elif (request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and 
              '/api/categories/' in request.path):
            
            from .cache_service import CacheService
            CacheService.invalidate_category_cache()
        
        return response 