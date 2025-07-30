"""
Database Router for Read/Write splitting between primary and replica databases.
"""

class DatabaseRouter:
    """
    Router для разделения операций чтения и записи между основной БД и репликой.
    """
    
    def db_for_read(self, model, **hints):
        """
        Предлагает базу данных для операций чтения.
        """
        # Используем реплику для операций чтения
        if model._meta.app_label == 'products':
            return 'replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Предлагает базу данных для операций записи.
        """
        # Всегда используем основную БД для записи
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Разрешает отношения между объектами.
        """
        # Разрешаем отношения только в рамках одной БД
        if obj1._meta.app_label == obj2._meta.app_label:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Разрешает миграции только на основной БД.
        """
        # Миграции выполняем только на основной БД
        if db == 'default':
            return True
        return False


class AnalyticsRouter:
    """
    Router для аналитических операций с TimescaleDB.
    """
    
    def db_for_read(self, model, **hints):
        """
        Предлагает аналитическую БД для чтения аналитических данных.
        """
        # Используем аналитическую БД для определенных моделей
        analytics_models = [
            'ProductAnalytics',
            'UserAnalytics', 
            'SalesAnalytics',
            'PerformanceMetrics'
        ]
        
        if model._meta.model_name in analytics_models:
            return 'analytics'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Предлагает аналитическую БД для записи аналитических данных.
        """
        # Используем аналитическую БД для записи аналитических данных
        analytics_models = [
            'ProductAnalytics',
            'UserAnalytics',
            'SalesAnalytics', 
            'PerformanceMetrics'
        ]
        
        if model._meta.model_name in analytics_models:
            return 'analytics'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Разрешает отношения между объектами в аналитической БД.
        """
        analytics_models = [
            'ProductAnalytics',
            'UserAnalytics',
            'SalesAnalytics',
            'PerformanceMetrics'
        ]
        
        if (obj1._meta.model_name in analytics_models and 
            obj2._meta.model_name in analytics_models):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Разрешает миграции аналитических моделей только в аналитической БД.
        """
        analytics_models = [
            'productanalytics',
            'useranalytics',
            'salesanalytics',
            'performancemetrics'
        ]
        
        if model_name in analytics_models:
            return db == 'analytics'
        return None


class CacheRouter:
    """
    Router для кэширования операций.
    """
    
    def db_for_read(self, model, **hints):
        """
        Предлагает кэшированную БД для чтения.
        """
        # Используем кэш для часто читаемых данных
        cache_models = [
            'Product',
            'Category',
            'PopularProduct'
        ]
        
        if model._meta.model_name in cache_models:
            # Проверяем кэш перед обращением к БД
            return 'default'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Предлагает основную БД для записи с инвалидацией кэша.
        """
        cache_models = [
            'Product',
            'Category',
            'PopularProduct'
        ]
        
        if model._meta.model_name in cache_models:
            # Инвалидируем кэш при записи
            return 'default'
        return None


class ReadOnlyRouter:
    """
    Router для принудительного использования реплики для чтения.
    """
    
    def __init__(self, read_db='replica', write_db='default'):
        self.read_db = read_db
        self.write_db = write_db
    
    def db_for_read(self, model, **hints):
        """
        Принудительно использует реплику для чтения.
        """
        return self.read_db
    
    def db_for_write(self, model, **hints):
        """
        Использует основную БД для записи.
        """
        return self.write_db
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Разрешает отношения только в рамках одной БД.
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Разрешает миграции только на основной БД.
        """
        return db == self.write_db


class ShardingRouter:
    """
    Router для шардинга данных по разным БД.
    """
    
    def __init__(self):
        # Определяем правила шардинга
        self.sharding_rules = {
            'products': {
                'shard_key': 'id',
                'shards': ['default', 'replica', 'analytics'],
                'shard_count': 3
            }
        }
    
    def get_shard_db(self, model, **hints):
        """
        Определяет шард БД на основе ключа шардинга.
        """
        if model._meta.app_label in self.sharding_rules:
            rule = self.sharding_rules[model._meta.app_label]
            shard_key = rule['shard_key']
            
            # Простая хэш-функция для определения шарда
            if 'instance' in hints:
                instance = hints['instance']
                if hasattr(instance, shard_key):
                    key_value = getattr(instance, shard_key)
                    shard_index = hash(str(key_value)) % rule['shard_count']
                    return rule['shards'][shard_index]
        
        return 'default'
    
    def db_for_read(self, model, **hints):
        """
        Предлагает шард БД для чтения.
        """
        return self.get_shard_db(model, **hints)
    
    def db_for_write(self, model, **hints):
        """
        Предлагает шард БД для записи.
        """
        return self.get_shard_db(model, **hints)
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Разрешает отношения между объектами в одном шарде.
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Разрешает миграции на всех шардах.
        """
        return True


# Композитный роутер для сложных сценариев
class CompositeRouter:
    """
    Композитный роутер, объединяющий несколько стратегий роутинга.
    """
    
    def __init__(self):
        self.routers = [
            AnalyticsRouter(),
            CacheRouter(),
            DatabaseRouter()
        ]
    
    def db_for_read(self, model, **hints):
        """
        Пробует роутеры по порядку для определения БД для чтения.
        """
        for router in self.routers:
            try:
                db = router.db_for_read(model, **hints)
                if db:
                    return db
            except Exception:
                continue
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Пробует роутеры по порядку для определения БД для записи.
        """
        for router in self.routers:
            try:
                db = router.db_for_write(model, **hints)
                if db:
                    return db
            except Exception:
                continue
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Проверяет разрешение отношений через все роутеры.
        """
        for router in self.routers:
            try:
                result = router.allow_relation(obj1, obj2, **hints)
                if result is not None:
                    return result
            except Exception:
                continue
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Проверяет разрешение миграций через все роутеры.
        """
        for router in self.routers:
            try:
                result = router.allow_migrate(db, app_label, model_name, **hints)
                if result is not None:
                    return result
            except Exception:
                continue
        return True 