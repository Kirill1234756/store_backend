from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from products.cache_service import CacheService
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Управление кэшем Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['clear', 'warm', 'stats', 'info', 'monitor'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            help='Префикс для очистки кэша'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Таймаут для операций (в секундах)'
        )

    def handle(self, *args, **options):
        action = options['action']
        prefix = options.get('prefix')
        timeout = options.get('timeout')

        if action == 'clear':
            self.clear_cache(prefix)
        elif action == 'warm':
            self.warm_cache()
        elif action == 'stats':
            self.show_stats()
        elif action == 'info':
            self.show_info()
        elif action == 'monitor':
            self.monitor_cache(timeout)

    def clear_cache(self, prefix=None):
        """Очистка кэша"""
        try:
            if prefix:
                # Очищаем кэш по префиксу
                CacheService.clear_cache_by_prefix(prefix)
                self.stdout.write(
                    self.style.SUCCESS(f'Кэш с префиксом "{prefix}" очищен')
                )
            else:
                # Очищаем весь кэш
                cache.clear()
                self.stdout.write(
                    self.style.SUCCESS('Весь кэш очищен')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка очистки кэша: {e}')
            )

    def warm_cache(self):
        """Прогрев кэша"""
        try:
            self.stdout.write('Начинаем прогрев кэша...')
            start_time = time.time()
            
            CacheService.warm_cache()
            
            duration = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(f'Прогрев кэша завершен за {duration:.2f} секунд')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка прогрева кэша: {e}')
            )

    def show_stats(self):
        """Показать статистику кэша"""
        try:
            stats = CacheService.get_cache_stats()
            
            self.stdout.write('📊 Статистика кэша:')
            self.stdout.write('=' * 40)
            
            for key, value in stats.items():
                self.stdout.write(f'{key}: {value}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка получения статистики: {e}')
            )

    def show_info(self):
        """Показать информацию о Redis"""
        try:
            redis_info = cache.client.info()
            
            self.stdout.write('🔍 Информация о Redis:')
            self.stdout.write('=' * 40)
            
            # Основная информация
            self.stdout.write(f'Версия Redis: {redis_info.get("redis_version", "N/A")}')
            self.stdout.write(f'Используемая память: {redis_info.get("used_memory_human", "N/A")}')
            self.stdout.write(f'Максимальная память: {redis_info.get("maxmemory_human", "N/A")}')
            self.stdout.write(f'Подключенные клиенты: {redis_info.get("connected_clients", 0)}')
            self.stdout.write(f'Всего команд: {redis_info.get("total_commands_processed", 0)}')
            
            # Статистика ключей
            self.stdout.write(f'Попадания в кэш: {redis_info.get("keyspace_hits", 0)}')
            self.stdout.write(f'Промахи кэша: {redis_info.get("keyspace_misses", 0)}')
            
            # Вычисляем hit rate
            hits = redis_info.get("keyspace_hits", 0)
            misses = redis_info.get("keyspace_misses", 0)
            total = hits + misses
            
            if total > 0:
                hit_rate = (hits / total) * 100
                self.stdout.write(f'Hit Rate: {hit_rate:.2f}%')
            else:
                self.stdout.write('Hit Rate: 0%')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка получения информации: {e}')
            )

    def monitor_cache(self, timeout):
        """Мониторинг кэша в реальном времени"""
        try:
            self.stdout.write(f'🔍 Мониторинг кэша (таймаут: {timeout}с)...')
            self.stdout.write('Нажмите Ctrl+C для остановки')
            
            start_time = time.time()
            initial_stats = cache.client.info()
            
            while time.time() - start_time < timeout:
                current_stats = cache.client.info()
                
                # Вычисляем изменения
                commands_diff = current_stats.get('total_commands_processed', 0) - initial_stats.get('total_commands_processed', 0)
                hits_diff = current_stats.get('keyspace_hits', 0) - initial_stats.get('keyspace_hits', 0)
                misses_diff = current_stats.get('keyspace_misses', 0) - initial_stats.get('keyspace_misses', 0)
                
                # Очищаем экран (для Unix-систем)
                self.stdout.write('\033[2J\033[H')
                
                self.stdout.write('📊 Мониторинг кэша в реальном времени')
                self.stdout.write('=' * 50)
                self.stdout.write(f'Время: {time.strftime("%H:%M:%S")}')
                self.stdout.write(f'Команд/сек: {commands_diff}')
                self.stdout.write(f'Hits/сек: {hits_diff}')
                self.stdout.write(f'Misses/сек: {misses_diff}')
                
                if hits_diff + misses_diff > 0:
                    current_hit_rate = (hits_diff / (hits_diff + misses_diff)) * 100
                    self.stdout.write(f'Текущий Hit Rate: {current_hit_rate:.2f}%')
                
                self.stdout.write(f'Используемая память: {current_stats.get("used_memory_human", "N/A")}')
                
                time.sleep(1)
                initial_stats = current_stats
                
        except KeyboardInterrupt:
            self.stdout.write('\nМониторинг остановлен')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка мониторинга: {e}')
            ) 