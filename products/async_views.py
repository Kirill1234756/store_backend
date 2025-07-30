import asyncio
import json
import logging
from typing import List, Dict, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async, async_to_sync
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

# Импорты моделей и сериализаторов
from .models import Product, Category
from .media_models import MediaImage
from .serializers import ProductSerializer, MediaImageSerializer
from .tasks import (
    process_product_images, optimize_image, generate_thumbnails,
    ai_analyze_image, process_payment, fraud_check,
    send_payment_confirmation, update_search_index,
    update_product_analytics, process_analytics
)

logger = logging.getLogger(__name__)

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ ПРОДУКТОВ
# ============================================================================

@api_view(['POST'])
async def async_create_product(request):
    """Асинхронное создание продукта с обработкой изображений"""
    try:
        # Валидация данных
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Создание продукта
        product = await sync_to_async(serializer.save)()
        
        # Асинхронная обработка изображений
        if 'images' in request.FILES:
            image_tasks = []
            for image_file in request.FILES.getlist('images'):
                # Сохранение изображения
                media_image = await sync_to_async(MediaImage.objects.create)(
                    product=product,
                    image=image_file
                )
                
                # Запуск задач обработки изображений
                image_tasks.extend([
                    optimize_image.delay(media_image.id),
                    generate_thumbnails.delay(media_image.id),
                    ai_analyze_image.delay(media_image.id)
                ])
            
            # Обновление статуса продукта
            product.image_processing_status = 'processing'
            await sync_to_async(product.save)()
        
        # Обновление поискового индекса
        update_search_index.delay(product.id)
        
        # Обновление аналитики
        update_product_analytics.delay()
        
        return Response({
            'id': product.id,
            'status': 'created',
            'image_processing': 'started' if 'images' in request.FILES else 'none'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in async_create_product: {e}")
        return Response(
            {'error': 'Failed to create product'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
async def async_product_list(request):
    """Асинхронный список продуктов с кэшированием"""
    try:
        # Проверка кэша
        cache_key = f"product_list_{request.GET.get('page', 1)}_{request.GET.get('search', '')}"
        cached_data = await sync_to_async(cache.get)(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Асинхронное получение продуктов
        products = await sync_to_async(Product.objects.filter)(is_active=True)
        
        # Применение фильтров
        if 'search' in request.GET:
            search_term = request.GET['search']
            products = await sync_to_async(products.filter)(
                title__icontains=search_term
            )
        
        if 'category' in request.GET:
            category_id = request.GET['category']
            products = await sync_to_async(products.filter)(category_id=category_id)
        
        # Пагинация
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        products = await sync_to_async(list)(products[start:end])
        
        # Сериализация
        serializer = ProductSerializer(products, many=True)
        data = {
            'results': serializer.data,
            'count': len(products),
            'page': page,
            'page_size': page_size
        }
        
        # Сохранение в кэш
        await sync_to_async(cache.set)(cache_key, data, timeout=300)
        
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in async_product_list: {e}")
        return Response(
            {'error': 'Failed to fetch products'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
async def async_upload_images(request, product_id):
    """Асинхронная загрузка изображений для продукта"""
    try:
        # Получение продукта
        product = await sync_to_async(Product.objects.get)(id=product_id)
        
        if 'images' not in request.FILES:
            return Response(
                {'error': 'No images provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Обработка изображений
        image_tasks = []
        uploaded_images = []
        
        for image_file in request.FILES.getlist('images'):
            # Создание MediaImage
            media_image = await sync_to_async(MediaImage.objects.create)(
                product=product,
                image=image_file
            )
            uploaded_images.append(media_image)
            
            # Запуск задач обработки
            image_tasks.extend([
                optimize_image.delay(media_image.id),
                generate_thumbnails.delay(media_image.id),
                ai_analyze_image.delay(media_image.id)
            ])
        
        # Обновление статуса продукта
        product.image_processing_status = 'processing'
        await sync_to_async(product.save)()
        
        # Сериализация результатов
        serializer = MediaImageSerializer(uploaded_images, many=True)
        
        return Response({
            'message': f'Uploaded {len(uploaded_images)} images',
            'images': serializer.data,
            'processing_tasks': len(image_tasks)
        }, status=status.HTTP_201_CREATED)
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in async_upload_images: {e}")
        return Response(
            {'error': 'Failed to upload images'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ ПЛАТЕЖЕЙ
# ============================================================================

@api_view(['POST'])
async def async_process_order(request):
    """Асинхронная обработка заказа с платежом"""
    try:
        # Валидация данных заказа
        order_data = request.data
        
        # Создание заказа
        from .models import Order
        order = await sync_to_async(Order.objects.create)(
            user=request.user,
            total=order_data['total'],
            status='PENDING'
        )
        
        # Параллельные проверки
        fraud_task = fraud_check.delay(request.user.id, order_data['total'])
        payment_task = process_payment.delay(order.id)
        
        # Ожидание результатов
        fraud_result = await sync_to_async(fraud_task.get)(timeout=30)
        payment_result = await sync_to_async(payment_task.get)(timeout=60)
        
        if not fraud_result:
            order.status = 'FRAUD_DETECTED'
            await sync_to_async(order.save)()
            return Response({
                'status': 'fraud_detected',
                'message': 'Order flagged for fraud'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not payment_result:
            order.status = 'PAYMENT_FAILED'
            await sync_to_async(order.save)()
            return Response({
                'status': 'payment_failed',
                'message': 'Payment processing failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Успешная обработка
        order.status = 'CONFIRMED'
        await sync_to_async(order.save)()
        
        # Запуск дополнительных задач
        from celery.result import chain
        chain(
            send_payment_confirmation.s(order.user.email, order.id),
            process_analytics.si(order.id)
        ).apply_async()
        
        return Response({
            'status': 'success',
            'order_id': order.id,
            'message': 'Order processed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in async_process_order: {e}")
        return Response(
            {'error': 'Failed to process order'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ АНАЛИТИКИ
# ============================================================================

@api_view(['GET'])
async def async_product_analytics(request, product_id):
    """Асинхронная аналитика продукта"""
    try:
        # Получение продукта
        product = await sync_to_async(Product.objects.get)(id=product_id)
        
        # Параллельный сбор аналитики
        tasks = [
            sync_to_async(get_product_views)(product_id),
            sync_to_async(get_product_reviews)(product_id),
            sync_to_async(get_product_performance)(product_id)
        ]
        
        # Ожидание результатов
        views_data, reviews_data, performance_data = await asyncio.gather(*tasks)
        
        analytics = {
            'product_id': product_id,
            'views': views_data,
            'reviews': reviews_data,
            'performance': performance_data,
            'timestamp': await sync_to_async(datetime.now)().isoformat()
        }
        
        return Response(analytics)
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in async_product_analytics: {e}")
        return Response(
            {'error': 'Failed to fetch analytics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_product_views(product_id):
    """Получение статистики просмотров"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    views = Product.objects.filter(
        id=product_id,
        views__created_at__range=(start_date, end_date)
    ).aggregate(
        total_views=Count('views'),
        unique_views=Count('views', distinct=True)
    )
    
    return views

def get_product_reviews(product_id):
    """Получение статистики отзывов"""
    from django.db.models import Avg, Count
    
    reviews = Product.objects.filter(id=product_id).aggregate(
        total_reviews=Count('reviews'),
        avg_rating=Avg('reviews__rating'),
        positive_reviews=Count('reviews', filter={'reviews__rating__gte': 4})
    )
    
    return reviews

def get_product_performance(product_id):
    """Получение производительности продукта"""
    from django.db.models import Avg
    
    performance = Product.objects.filter(id=product_id).aggregate(
        avg_load_time=Avg('performance_metrics__load_time'),
        avg_response_time=Avg('performance_metrics__response_time')
    )
    
    return performance

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ ПОИСКА
# ============================================================================

@api_view(['GET'])
async def async_search_products(request):
    """Асинхронный поиск продуктов"""
    try:
        query = request.GET.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка кэша
        import hashlib
        cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}"
        cached_results = await sync_to_async(cache.get)(cache_key)
        
        if cached_results:
            return Response(cached_results)
        
        # Параллельный поиск в разных источниках
        tasks = [
            sync_to_async(search_database)(query),
            sync_to_async(search_elasticsearch)(query) if settings.ELASTICSEARCH_ENABLED else None
        ]
        
        # Фильтрация None задач
        valid_tasks = [task for task in tasks if task is not None]
        results = await asyncio.gather(*valid_tasks, return_exceptions=True)
        
        # Объединение результатов
        combined_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search error: {result}")
                continue
            combined_results.extend(result)
        
        # Удаление дубликатов
        seen_ids = set()
        unique_results = []
        for product in combined_results:
            if product['id'] not in seen_ids:
                seen_ids.add(product['id'])
                unique_results.append(product)
        
        # Сортировка по релевантности
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Сохранение в кэш
        await sync_to_async(cache.set)(cache_key, unique_results, timeout=1800)
        
        return Response({
            'query': query,
            'results': unique_results,
            'total': len(unique_results)
        })
        
    except Exception as e:
        logger.error(f"Error in async_search_products: {e}")
        return Response(
            {'error': 'Search failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def search_database(query):
    """Поиск в базе данных"""
    from django.db.models import Q
    
    products = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(phone_model__icontains=query),
        is_active=True
    )[:50]
    
    return ProductSerializer(products, many=True).data

def search_elasticsearch(query):
    """Поиск в Elasticsearch"""
    try:
        from .search_service import ProductSearchService
        
        search_service = ProductSearchService()
        results = search_service.search(query, size=50)
        
        return results
    except Exception as e:
        logger.error(f"Elasticsearch search error: {e}")
        return []

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ МОНИТОРИНГА
# ============================================================================

@api_view(['GET'])
async def async_system_status(request):
    """Асинхронная проверка статуса системы"""
    try:
        # Параллельные проверки
        tasks = [
            sync_to_async(check_database_health)(),
            sync_to_async(check_redis_health)(),
            sync_to_async(check_elasticsearch_health)(),
            sync_to_async(check_celery_health)()
        ]
        
        # Ожидание результатов
        db_status, redis_status, es_status, celery_status = await asyncio.gather(*tasks)
        
        overall_status = 'healthy' if all([db_status, redis_status, es_status, celery_status]) else 'degraded'
        
        return Response({
            'status': overall_status,
            'services': {
                'database': db_status,
                'redis': redis_status,
                'elasticsearch': es_status,
                'celery': celery_status
            },
            'timestamp': await sync_to_async(datetime.now)().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in async_system_status: {e}")
        return Response(
            {'error': 'Failed to check system status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def check_database_health():
    """Проверка здоровья базы данных"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def check_redis_health():
    """Проверка здоровья Redis"""
    try:
        cache.set('health_check', 'ok', timeout=60)
        return cache.get('health_check') == 'ok'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

def check_elasticsearch_health():
    """Проверка здоровья Elasticsearch"""
    try:
        if not settings.ELASTICSEARCH_ENABLED:
            return True
        
        from .search_service import ProductSearchService
        search_service = ProductSearchService()
        return search_service.health_check()
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return False

def check_celery_health():
    """Проверка здоровья Celery"""
    try:
        from celery.task.control import inspect
        i = inspect()
        stats = i.stats()
        return bool(stats)
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return False

# ============================================================================
# АСИНХРОННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ МАССОВЫХ ОПЕРАЦИЙ
# ============================================================================

@api_view(['POST'])
async def async_bulk_operations(request):
    """Асинхронные массовые операции"""
    try:
        operation_type = request.data.get('operation_type')
        data = request.data.get('data', [])
        
        if not operation_type or not data:
            return Response(
                {'error': 'operation_type and data required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Запуск массовой операции
        from .tasks import process_bulk_operations
        task = process_bulk_operations.delay(operation_type, data)
        
        return Response({
            'task_id': task.id,
            'operation_type': operation_type,
            'status': 'started',
            'message': f'Bulk operation {operation_type} started'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error in async_bulk_operations: {e}")
        return Response(
            {'error': 'Failed to start bulk operation'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
async def async_task_status(request, task_id):
    """Проверка статуса задачи"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready()
        }
        
        if result.ready():
            if result.successful():
                response_data['result'] = result.result
            else:
                response_data['error'] = str(result.info)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error in async_task_status: {e}")
        return Response(
            {'error': 'Failed to get task status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ============================================================================
# ДЕКОРАТОРЫ ДЛЯ АСИНХРОННЫХ ПРЕДСТАВЛЕНИЙ
# ============================================================================

def async_view(view_func):
    """Декоратор для асинхронных представлений"""
    def wrapper(request, *args, **kwargs):
        return async_to_sync(view_func)(request, *args, **kwargs)
    return wrapper

def cache_async_response(timeout=300):
    """Декоратор для кэширования асинхронных ответов"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Создание ключа кэша
            cache_key = f"async_view_{view_func.__name__}_{hash(str(request.GET))}"
            
            # Проверка кэша
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Выполнение представления
            response = async_to_sync(view_func)(request, *args, **kwargs)
            
            # Сохранение в кэш
            cache.set(cache_key, response, timeout=timeout)
            
            return response
        return wrapper
    return decorator 