"""
ASGI config for store_platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.optimized')

# Инициализация Django
django.setup()

# Получение ASGI приложения Django
django_asgi_app = get_asgi_application()

# Импорт роутинга для WebSocket (если используется)
try:
    from .routing import websocket_urlpatterns
    has_websockets = True
except ImportError:
    has_websockets = False

# Настройка протоколов
if has_websockets:
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                )
            )
        ),
    })
else:
    # Только HTTP без WebSocket
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
    })

# Альтернативная конфигурация для высоких нагрузок
# Используйте эту конфигурацию для продакшена с большим количеством соединений

# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# from django.core.asgi import get_asgi_application
# from asgiref.sync import sync_to_async

# # Создание пула потоков для синхронных операций
# thread_pool = ThreadPoolExecutor(max_workers=100)

# async def async_django_app(scope, receive, send):
#     """Асинхронная обертка для Django приложения"""
#     if scope['type'] == 'http':
#         # Для HTTP запросов используем синхронное Django приложение
#         await sync_to_async(django_asgi_app)(scope, receive, send)
#     else:
#         # Для других протоколов (WebSocket) используем асинхронную обработку
#         await django_asgi_app(scope, receive, send)

# # Настройка для высоких нагрузок
# application = ProtocolTypeRouter({
#     "http": async_django_app,
#     "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             URLRouter(websocket_urlpatterns)
#         )
#     ) if has_websockets else None,
# })

# # Настройка event loop для лучшей производительности
# loop = asyncio.get_event_loop()
# loop.set_default_executor(thread_pool)
