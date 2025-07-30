import os
import json
import logging
import asyncio
import aiohttp
import requests
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from celery import shared_task, chain, group
from celery.utils.log import get_task_logger
from asgiref.sync import sync_to_async
import time
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal

# Импорты моделей
from .models import Product, Category
from .media_models import MediaImage
from .serializers import ProductSerializer

logger = get_task_logger(__name__)

# ============================================================================
# ЗАДАЧИ ОБРАБОТКИ ИЗОБРАЖЕНИЙ
# ============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    max_retries=3,
    queue='media'
)
def process_product_images(self, product_id):
    """Обработка изображений продукта с оптимизацией"""
    try:
        product = Product.objects.get(id=product_id)
        images = product.product_images.all()
        
        processed_count = 0
        for image in images:
            try:
                # Оптимизация изображения
                optimize_image.delay(image.id)
                # Генерация миниатюр
                generate_thumbnails.delay(image.id)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {e}")
                continue
        
        # Обновление статуса продукта
        product.image_processing_status = 'completed'
        product.save()
        
        logger.info(f"Processed {processed_count} images for product {product_id}")
        return processed_count
        
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing images for product {product_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    max_retries=5,
    queue='media'
)
def optimize_image(self, image_id):
    """Оптимизация изображения с конвертацией в WebP"""
    try:
        image = MediaImage.objects.get(id=image_id)
        
        # Открытие изображения
        with Image.open(image.image) as img:
            # Конвертация в RGB если необходимо
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Изменение размера если слишком большое
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Оптимизация качества
            output = BytesIO()
            img.save(output, format='WEBP', quality=85, optimize=True)
            content = ContentFile(output.getvalue())
            
            # Сохранение оптимизированного изображения
            filename = f'optimized_{image_id}.webp'
            image.optimized_image.save(filename, content, save=True)
            
            # Обновление размера файла
            image.file_size = len(content)
            image.save()
            
        logger.info(f"Optimized image {image_id}")
        return True
        
    except MediaImage.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error optimizing image {image_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=3,
    queue='media'
)
def generate_thumbnails(self, image_id):
    """Генерация миниатюр разных размеров"""
    try:
        image = MediaImage.objects.get(id=image_id)
        
        sizes = [
            (150, 150, 'small'),
            (300, 300, 'medium'),
            (600, 600, 'large')
        ]
        
        with Image.open(image.image) as img:
            for width, height, size_name in sizes:
                # Создание миниатюры
                thumb = img.copy()
                thumb.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                # Сохранение миниатюры
                output = BytesIO()
                thumb.save(output, format='WEBP', quality=80, optimize=True)
                content = ContentFile(output.getvalue())
                
                # Сохранение в соответствующее поле
                filename = f'thumb_{size_name}_{image_id}.webp'
                if size_name == 'small':
                    image.thumbnail_small.save(filename, content, save=False)
                elif size_name == 'medium':
                    image.thumbnail_medium.save(filename, content, save=False)
                elif size_name == 'large':
                    image.thumbnail_large.save(filename, content, save=False)
        
        image.save()
        logger.info(f"Generated thumbnails for image {image_id}")
        return True
        
    except MediaImage.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating thumbnails for image {image_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    max_retries=3,
    queue='ai'
)
def ai_analyze_image(self, image_id):
    """AI анализ изображения с использованием Google Vision API"""
    try:
        image = MediaImage.objects.get(id=image_id)
        
        if not settings.GOOGLE_VISION_API_KEY:
            logger.warning("Google Vision API key not configured")
            return False
        
        # Подготовка изображения для API
        with open(image.image.path, 'rb') as image_file:
            image_content = image_file.read()
        
        # Запрос к Google Vision API
        vision_request = {
            'requests': [{
                'image': {
                    'content': image_content.decode('latin1')
                },
                'features': [
                    {'type': 'LABEL_DETECTION', 'maxResults': 10},
                    {'type': 'TEXT_DETECTION'},
                    {'type': 'SAFE_SEARCH_DETECTION'},
                    {'type': 'OBJECT_LOCALIZATION', 'maxResults': 5}
                ]
            }]
        }
        
        response = requests.post(
            settings.GOOGLE_VISION_ENDPOINT,
            params={'key': settings.GOOGLE_VISION_API_KEY},
            json=vision_request,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Сохранение результатов анализа
        image.ai_analysis = result
        image.analysis_status = 'completed'
        image.save()
        
        logger.info(f"AI analysis completed for image {image_id}")
        return True
        
    except MediaImage.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error in AI analysis for image {image_id}: {e}")
        raise

# ============================================================================
# ЗАДАЧИ ПЛАТЕЖЕЙ И БЕЗОПАСНОСТИ
# ============================================================================

@shared_task(
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=5,
    queue='high_priority'
)
def process_payment(self, order_id):
    """Обработка платежа с интеграцией платежного шлюза"""
    try:
        from .models import Order  # Локальный импорт для избежания циклических зависимостей
        
        order = Order.objects.get(id=order_id)
        
        # Проверка мошенничества
        fraud_result = fraud_check.delay(order.user.id, order.total)
        
        # Ожидание результата проверки
        fraud_status = fraud_result.get(timeout=30)
        
        if not fraud_status:
            order.status = 'FRAUD_DETECTED'
            order.save()
            logger.warning(f"Fraud detected for order {order_id}")
            return False
        
        # Интеграция с платежным шлюзом
        payment_data = {
            'amount': float(order.total),
            'currency': 'USD',
            'order_id': str(order_id),
            'customer_email': order.user.email,
            'description': f'Order #{order_id}'
        }
        
        # Асинхронный запрос к платежному шлюзу
        response = requests.post(
            settings.PAYMENT_GATEWAY_URL,
            json=payment_data,
            headers={'Authorization': f'Bearer {settings.PAYMENT_GATEWAY_KEY}'},
            timeout=30
        )
        response.raise_for_status()
        
        payment_result = response.json()
        
        if payment_result.get('status') == 'success':
            order.status = 'PAID'
            order.payment_id = payment_result.get('payment_id')
            order.save()
            
            # Запуск цепочки задач после успешной оплаты
            chain(
                send_payment_confirmation.s(order.user.email, order_id),
                update_inventory.si(order_id),
                process_analytics.si(order_id)
            ).apply_async()
            
            logger.info(f"Payment processed successfully for order {order_id}")
            return True
        else:
            order.status = 'PAYMENT_FAILED'
            order.save()
            logger.error(f"Payment failed for order {order_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing payment for order {order_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=3,
    queue='high_priority'
)
def fraud_check(self, user_id, amount):
    """Проверка на мошенничество"""
    try:
        from .models import User
        
        user = User.objects.get(id=user_id)
        
        # Проверка истории транзакций
        recent_orders = user.orders.filter(
            created_at__gte=datetime.now() - timedelta(hours=24)
        )
        
        total_amount_24h = sum(order.total for order in recent_orders)
        
        # Проверка подозрительной активности
        suspicious_indicators = []
        
        if total_amount_24h > 1000:  # Большие суммы за 24 часа
            suspicious_indicators.append('high_amount_24h')
        
        if recent_orders.count() > 10:  # Много заказов за 24 часа
            suspicious_indicators.append('many_orders_24h')
        
        if amount > 500:  # Большой единичный заказ
            suspicious_indicators.append('large_single_order')
        
        # Проверка IP адреса (если доступно)
        # Проверка геолокации
        # Проверка устройства
        
        fraud_score = len(suspicious_indicators) * 25  # Простая система скоринга
        
        is_fraud = fraud_score > 50
        
        logger.info(f"Fraud check for user {user_id}: score={fraud_score}, fraud={is_fraud}")
        
        return not is_fraud
        
    except Exception as e:
        logger.error(f"Error in fraud check for user {user_id}: {e}")
        raise

# ============================================================================
# ЗАДАЧИ УВЕДОМЛЕНИЙ
# ============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    max_retries=3,
    queue='notifications'
)
def send_payment_confirmation(self, user_email, order_id):
    """Отправка подтверждения платежа"""
    try:
        # Интеграция с email сервисом
        email_data = {
            'to': user_email,
            'subject': f'Payment Confirmation - Order #{order_id}',
            'template': 'payment_confirmation',
            'context': {'order_id': order_id}
        }
        
        # Асинхронная отправка email
        response = requests.post(
            settings.EMAIL_SERVICE_URL,
            json=email_data,
            headers={'Authorization': f'Bearer {settings.EMAIL_SERVICE_KEY}'},
            timeout=10
        )
        response.raise_for_status()
        
        logger.info(f"Payment confirmation sent for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending payment confirmation for order {order_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    max_retries=5,
    queue='notifications'
)
def send_bulk_notifications(self, user_ids, message, notification_type='general'):
    """Массовая отправка уведомлений"""
    try:
        from .models import User
        
        users = User.objects.filter(id__in=user_ids)
        
        # Группировка по типам уведомлений
        notification_tasks = []
        
        for user in users:
            if notification_type == 'push' and user.device_token:
                notification_tasks.append(
                    send_push_notification.si(user.device_token, message)
                )
            elif notification_type == 'email':
                notification_tasks.append(
                    send_email_notification.si(user.email, message)
                )
        
        # Параллельная отправка
        if notification_tasks:
            group(notification_tasks).apply_async()
        
        logger.info(f"Bulk notifications sent to {len(users)} users")
        return len(users)
        
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {e}")
        raise

@shared_task(queue='notifications')
def send_push_notification(device_token, message):
    """Отправка push-уведомления"""
    try:
        # Интеграция с FCM или другим push-сервисом
        push_data = {
            'to': device_token,
            'notification': {
                'title': 'Store Platform',
                'body': message
            },
            'data': {
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            }
        }
        
        response = requests.post(
            settings.FCM_URL,
            json=push_data,
            headers={'Authorization': f'key={settings.FCM_SERVER_KEY}'},
            timeout=10
        )
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        raise

# ============================================================================
# ЗАДАЧИ ПОИСКА И ИНДЕКСАЦИИ
# ============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    max_retries=3,
    queue='search'
)
def update_search_index(self, product_id):
    """Обновление поискового индекса для продукта"""
    try:
        product = Product.objects.get(id=product_id)
        
        if hasattr(settings, 'ELASTICSEARCH_ENABLED') and settings.ELASTICSEARCH_ENABLED:
            # Обновление в Elasticsearch
            from .search_service import ProductSearchService
            
            search_service = ProductSearchService()
            search_service.index_product(product)
            
            logger.info(f"Search index updated for product {product_id}")
            return True
        else:
            logger.info(f"Elasticsearch not enabled, skipping index update for product {product_id}")
            return True
            
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error updating search index for product {product_id}: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    max_retries=3,
    queue='search'
)
def sync_elasticsearch_index(self):
    """Синхронизация всего индекса Elasticsearch"""
    try:
        if not hasattr(settings, 'ELASTICSEARCH_ENABLED') or not settings.ELASTICSEARCH_ENABLED:
            logger.info("Elasticsearch not enabled, skipping sync")
            return True
        
        from .search_service import ProductSearchService
        
        search_service = ProductSearchService()
        
        # Получение всех продуктов для индексации
        products = Product.objects.filter(is_active=True)
        
        indexed_count = 0
        for product in products:
            try:
                search_service.index_product(product)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Error indexing product {product.id}: {e}")
                continue
        
        logger.info(f"Elasticsearch sync completed: {indexed_count} products indexed")
        return indexed_count
        
    except Exception as e:
        logger.error(f"Error in Elasticsearch sync: {e}")
        raise

@shared_task(queue='search')
def update_search_suggestions(self):
    """Обновление поисковых подсказок"""
    try:
        # Получение популярных поисковых запросов
        from django.db.models import Count
        from .models import SearchQuery
        
        popular_queries = SearchQuery.objects.values('query').annotate(
            count=Count('id')
        ).filter(count__gte=5).order_by('-count')[:50]
        
        # Сохранение в кэш
        suggestions = [item['query'] for item in popular_queries]
        cache.set('search_suggestions', suggestions, timeout=3600)
        
        logger.info(f"Updated search suggestions: {len(suggestions)} items")
        return len(suggestions)
        
    except Exception as e:
        logger.error(f"Error updating search suggestions: {e}")
        raise

# ============================================================================
# ЗАДАЧИ АНАЛИТИКИ
# ============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    max_retries=3,
    queue='analytics'
)
def update_product_analytics(self):
    """Обновление аналитики продуктов"""
    try:
        from django.db.models import Count, Avg, Sum
        from datetime import datetime, timedelta
        
        # Период для анализа
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Анализ просмотров продуктов
        product_views = Product.objects.filter(
            created_at__range=(start_date, end_date)
        ).annotate(
            view_count=Count('views'),
            avg_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews')
        )
        
        # Сохранение аналитики в кэш
        analytics_data = {}
        for product in product_views:
            analytics_data[product.id] = {
                'view_count': product.view_count,
                'avg_rating': float(product.avg_rating) if product.avg_rating else 0,
                'total_reviews': product.total_reviews
            }
        
        cache.set('product_analytics', analytics_data, timeout=86400)  # 24 часа
        
        logger.info(f"Updated analytics for {len(analytics_data)} products")
        return len(analytics_data)
        
    except Exception as e:
        logger.error(f"Error updating product analytics: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    max_retries=3,
    queue='analytics'
)
def process_analytics(self, order_id):
    """Обработка аналитики для заказа"""
    try:
        from .models import Order
        
        order = Order.objects.get(id=order_id)
        
        # Обновление статистики продаж
        sales_stats = cache.get('sales_stats', {})
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date not in sales_stats:
            sales_stats[current_date] = {
                'total_sales': 0,
                'order_count': 0,
                'avg_order_value': 0
            }
        
        sales_stats[current_date]['total_sales'] += float(order.total)
        sales_stats[current_date]['order_count'] += 1
        sales_stats[current_date]['avg_order_value'] = (
            sales_stats[current_date]['total_sales'] / 
            sales_stats[current_date]['order_count']
        )
        
        cache.set('sales_stats', sales_stats, timeout=86400)
        
        logger.info(f"Analytics processed for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing analytics for order {order_id}: {e}")
        raise

# ============================================================================
# ЗАДАЧИ ОБСЛУЖИВАНИЯ
# ============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    max_retries=3,
    queue='maintenance'
)
def cleanup_expired_products(self):
    """Очистка просроченных продуктов"""
    try:
        from datetime import datetime, timedelta
        
        # Продукты старше 90 дней без активности
        cutoff_date = datetime.now() - timedelta(days=90)
        
        expired_products = Product.objects.filter(
            created_at__lt=cutoff_date,
            is_active=True,
            views__isnull=True  # Без просмотров
        )
        
        deleted_count = 0
        for product in expired_products:
            try:
                product.is_active = False
                product.save()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deactivating product {product.id}: {e}")
                continue
        
        logger.info(f"Cleaned up {deleted_count} expired products")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error in cleanup expired products: {e}")
        raise

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=3,
    queue='maintenance'
)
def backup_database(self):
    """Резервное копирование базы данных"""
    try:
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sql'
        backup_path = os.path.join(settings.BACKUP_DIR, backup_filename)
        
        # Создание резервной копии PostgreSQL
        db_settings = settings.DATABASES['default']
        
        cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', backup_path
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        else:
            logger.error(f"Database backup failed: {result.stderr}")
            raise Exception("Database backup failed")
            
    except Exception as e:
        logger.error(f"Error in database backup: {e}")
        raise

@shared_task(queue='maintenance')
def check_system_health(self):
    """Проверка здоровья системы"""
    try:
        health_status = {
            'database': False,
            'redis': False,
            'elasticsearch': False,
            'disk_space': False,
            'memory_usage': False
        }
        
        # Проверка базы данных
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['database'] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
        
        # Проверка Redis
        try:
            cache.set('health_check', 'ok', timeout=60)
            if cache.get('health_check') == 'ok':
                health_status['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        # Проверка дискового пространства
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            if free > 1024 * 1024 * 1024 * 10:  # 10GB
                health_status['disk_space'] = True
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
        
        # Проверка использования памяти
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent < 90:  # Меньше 90%
                health_status['memory_usage'] = True
        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
        
        # Сохранение статуса в кэш
        cache.set('system_health', health_status, timeout=300)  # 5 минут
        
        healthy_services = sum(health_status.values())
        total_services = len(health_status)
        
        logger.info(f"System health check: {healthy_services}/{total_services} services healthy")
        return health_status
        
    except Exception as e:
        logger.error(f"Error in system health check: {e}")
        raise

# ============================================================================
# ЗАДАЧИ КЭШИРОВАНИЯ
# ============================================================================

@shared_task(queue='cache')
def update_cache(self):
    """Обновление кэша"""
    try:
        # Обновление кэша популярных продуктов
        popular_products = Product.objects.filter(
            is_active=True
        ).order_by('-views')[:20]
        
        cache.set('popular_products', list(popular_products.values()), timeout=3600)
        
        # Обновление кэша категорий
        categories = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)
        
        cache.set('categories', list(categories.values()), timeout=3600)
        
        # Обновление кэша статистики
        stats = {
            'total_products': Product.objects.filter(is_active=True).count(),
            'total_categories': Category.objects.count(),
            'total_users': User.objects.count() if 'User' in globals() else 0
        }
        
        cache.set('platform_stats', stats, timeout=3600)
        
        logger.info("Cache updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating cache: {e}")
        raise

# ============================================================================
# ЗАДАЧИ МОНИТОРИНГА
# ============================================================================

@shared_task(queue='monitoring')
def monitor_queue_health(self):
    """Мониторинг здоровья очередей"""
    try:
        from celery.task.control import inspect
        
        i = inspect()
        
        # Получение статистики активных задач
        active_tasks = i.active()
        reserved_tasks = i.reserved()
        scheduled_tasks = i.scheduled()
        
        queue_stats = {
            'active_tasks': len(active_tasks) if active_tasks else 0,
            'reserved_tasks': len(reserved_tasks) if reserved_tasks else 0,
            'scheduled_tasks': len(scheduled_tasks) if scheduled_tasks else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Сохранение статистики в кэш
        cache.set('queue_health', queue_stats, timeout=300)  # 5 минут
        
        # Алерт если слишком много задач в очереди
        total_tasks = queue_stats['active_tasks'] + queue_stats['reserved_tasks']
        if total_tasks > 1000:
            logger.warning(f"High queue load: {total_tasks} tasks in queue")
        
        logger.info(f"Queue health monitored: {total_tasks} total tasks")
        return queue_stats
        
    except Exception as e:
        logger.error(f"Error monitoring queue health: {e}")
        raise

# ============================================================================
# УТИЛИТАРНЫЕ ЗАДАЧИ
# ============================================================================

@shared_task(queue='bulk')
def process_bulk_operations(self, operation_type, data):
    """Обработка массовых операций"""
    try:
        if operation_type == 'product_import':
            return process_product_import(data)
        elif operation_type == 'user_export':
            return process_user_export(data)
        elif operation_type == 'category_update':
            return process_category_update(data)
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
            
    except Exception as e:
        logger.error(f"Error in bulk operation {operation_type}: {e}")
        raise

def process_product_import(data):
    """Импорт продуктов"""
    imported_count = 0
    for product_data in data:
        try:
            with transaction.atomic():
                product = Product.objects.create(**product_data)
                imported_count += 1
        except Exception as e:
            logger.error(f"Error importing product: {e}")
            continue
    
    return imported_count

def process_user_export(data):
    """Экспорт пользователей"""
    # Логика экспорта пользователей
    return len(data)

def process_category_update(data):
    """Обновление категорий"""
    updated_count = 0
    for category_data in data:
        try:
            category = Category.objects.get(id=category_data['id'])
            for field, value in category_data.items():
                if field != 'id':
                    setattr(category, field, value)
            category.save()
            updated_count += 1
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            continue
    
    return updated_count 