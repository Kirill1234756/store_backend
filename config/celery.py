import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.optimized')

# Создание экземпляра Celery
app = Celery('store_platform')

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в приложениях
app.autodiscover_tasks()

# Конфигурация брокера и бэкенда
app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'django-db'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    task_acks_late=True,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
    event_queue_expires=60,
    worker_cancel_long_running_tasks_on_connection_loss=True,
)

# Настройка очередей с приоритетами
app.conf.task_routes = {
    'products.tasks.process_images': {'queue': 'media'},
    'products.tasks.optimize_images': {'queue': 'media'},
    'products.tasks.generate_thumbnails': {'queue': 'media'},
    'products.tasks.ai_analyze_image': {'queue': 'ai'},
    'products.tasks.update_search_index': {'queue': 'search'},
    'products.tasks.send_notifications': {'queue': 'notifications'},
    'products.tasks.process_payment': {'queue': 'high_priority'},
    'products.tasks.fraud_check': {'queue': 'high_priority'},
    'products.tasks.update_analytics': {'queue': 'analytics'},
    'products.tasks.cleanup_expired': {'queue': 'maintenance'},
    'products.tasks.backup_database': {'queue': 'maintenance'},
    'products.tasks.sync_elasticsearch': {'queue': 'search'},
    'products.tasks.update_cache': {'queue': 'cache'},
    'products.tasks.process_bulk_operations': {'queue': 'bulk'},
}

# Периодические задачи (Celery Beat)
app.conf.beat_schedule = {
    # Ежедневные задачи
    'cleanup-expired-products': {
        'task': 'products.tasks.cleanup_expired_products',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM
    },
    'update-product-analytics': {
        'task': 'products.tasks.update_product_analytics',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM
    },
    'backup-database': {
        'task': 'products.tasks.backup_database',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM
    },
    'sync-elasticsearch': {
        'task': 'products.tasks.sync_elasticsearch_index',
        'schedule': crontab(hour=5, minute=0),  # 5:00 AM
    },
    
    # Еженедельные задачи
    'generate-weekly-reports': {
        'task': 'products.tasks.generate_weekly_reports',
        'schedule': crontab(day_of_week=1, hour=6, minute=0),  # Понедельник 6:00 AM
    },
    
    # Ежечасные задачи
    'update-cache': {
        'task': 'products.tasks.update_cache',
        'schedule': crontab(minute=0),  # Каждый час
    },
    'check-system-health': {
        'task': 'products.tasks.check_system_health',
        'schedule': crontab(minute=30),  # Каждые 30 минут
    },
    
    # Каждые 15 минут
    'update-search-suggestions': {
        'task': 'products.tasks.update_search_suggestions',
        'schedule': crontab(minute='*/15'),
    },
    
    # Каждые 5 минут
    'monitor-queue-health': {
        'task': 'products.tasks.monitor_queue_health',
        'schedule': crontab(minute='*/5'),
    },
}

# Настройка логирования
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Сигналы для мониторинга
@app.task(bind=True)
def task_success_handler(self, sender, **kwargs):
    print(f'Task {sender.name} completed successfully')

@app.task(bind=True)
def task_failure_handler(self, sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    print(f'Task {sender.name} failed: {exception}')

# Регистрация сигналов
from celery.signals import task_success, task_failure
task_success.connect(task_success_handler)
task_failure.connect(task_failure_handler) 