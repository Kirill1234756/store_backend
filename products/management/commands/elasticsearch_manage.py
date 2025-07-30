from django.core.management.base import BaseCommand, CommandError
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.management.commands import search_index
from products.models import Product
from products.search_indexes import ProductDocument
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Управление индексами Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create', 'delete', 'rebuild', 'update', 'status'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            help='Список моделей для обработки'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Размер батча для индексации'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительное выполнение'
        )

    def handle(self, *args, **options):
        action = options['action']
        models = options['models']
        batch_size = options['batch_size']
        force = options['force']

        if action == 'create':
            self.create_indexes(models)
        elif action == 'delete':
            self.delete_indexes(models, force)
        elif action == 'rebuild':
            self.rebuild_indexes(models, batch_size)
        elif action == 'update':
            self.update_indexes(models, batch_size)
        elif action == 'status':
            self.show_status()

    def create_indexes(self, models=None):
        """Создание индексов"""
        self.stdout.write('Создание индексов Elasticsearch...')
        
        try:
            # Создаем индексы
            for doc in registry.get_documents():
                if models is None or doc.Django.model.__name__ in models:
                    self.stdout.write(f'Создание индекса для {doc.Django.model.__name__}...')
                    # Создаем экземпляр документа и создаем индекс
                    doc_instance = doc()
                    doc_instance._index.create()
                    self.stdout.write(
                        self.style.SUCCESS(f'Индекс для {doc.Django.model.__name__} создан')
                    )
            
            self.stdout.write(self.style.SUCCESS('Все индексы созданы успешно'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка создания индексов: {e}'))

    def delete_indexes(self, models=None, force=False):
        """Удаление индексов"""
        if not force:
            confirm = input('Вы уверены, что хотите удалить индексы? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Операция отменена')
                return

        self.stdout.write('Удаление индексов Elasticsearch...')
        
        try:
            for doc in registry.get_documents():
                if models is None or doc.Django.model.__name__ in models:
                    self.stdout.write(f'Удаление индекса для {doc.Django.model.__name__}...')
                    doc._index.delete(ignore=404)
                    self.stdout.write(
                        self.style.SUCCESS(f'Индекс для {doc.Django.model.__name__} удален')
                    )
            
            self.stdout.write(self.style.SUCCESS('Все индексы удалены успешно'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка удаления индексов: {e}'))

    def rebuild_indexes(self, models=None, batch_size=1000):
        """Пересоздание индексов"""
        self.stdout.write('Пересоздание индексов Elasticsearch...')
        
        try:
            # Удаляем старые индексы
            self.delete_indexes(models, force=True)
            
            # Создаем новые индексы
            self.create_indexes(models)
            
            # Индексируем данные
            self.update_indexes(models, batch_size)
            
            self.stdout.write(self.style.SUCCESS('Индексы пересозданы успешно'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка пересоздания индексов: {e}'))

    def update_indexes(self, models=None, batch_size=1000):
        """Обновление индексов"""
        self.stdout.write('Обновление индексов Elasticsearch...')
        
        try:
            for doc in registry.get_documents():
                if models is None or doc._doc_type.model.__name__ in models:
                    model = doc._doc_type.model
                    self.stdout.write(f'Индексация {model.__name__}...')
                    
                    # Получаем queryset для индексации
                    queryset = doc().get_indexing_queryset()
                    total_count = queryset.count()
                    
                    if total_count == 0:
                        self.stdout.write(f'Нет данных для индексации в {model.__name__}')
                        continue
                    
                    # Индексируем батчами
                    processed = 0
                    for batch_start in range(0, total_count, batch_size):
                        batch_end = min(batch_start + batch_size, total_count)
                        batch_queryset = queryset[batch_start:batch_end]
                        
                        # Индексируем батч
                        doc().update(batch_queryset)
                        
                        processed += len(batch_queryset)
                        self.stdout.write(f'Обработано {processed}/{total_count} записей')
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'{model.__name__} проиндексирован: {total_count} записей')
                    )
            
            self.stdout.write(self.style.SUCCESS('Все индексы обновлены успешно'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка обновления индексов: {e}'))

    def show_status(self):
        """Показать статус индексов"""
        self.stdout.write('Статус индексов Elasticsearch:')
        
        try:
            for doc in registry.get_documents():
                index_name = doc._index._name
                model_name = doc._doc_type.model.__name__
                
                # Проверяем существование индекса
                if doc._index.exists():
                    # Получаем статистику
                    stats = doc._index.stats()
                    doc_count = stats['indices'][index_name]['total']['docs']['count']
                    
                    self.stdout.write(
                        f'✓ {model_name} -> {index_name} ({doc_count} документов)'
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'✗ {model_name} -> {index_name} (не существует)')
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка получения статуса: {e}'))

    def get_index_stats(self):
        """Получение статистики индексов"""
        try:
            stats = {}
            for doc in registry.get_documents():
                index_name = doc._index._name
                if doc._index.exists():
                    index_stats = doc._index.stats()
                    stats[index_name] = {
                        'doc_count': index_stats['indices'][index_name]['total']['docs']['count'],
                        'size': index_stats['indices'][index_name]['total']['store']['size_in_bytes']
                    }
            return stats
        except Exception as e:
            logger.error(f'Error getting index stats: {e}')
            return {} 