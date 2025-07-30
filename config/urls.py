from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, MediaImageViewSet
from products.views import ai_upload_image
from products import views
from products.views import product_main_image, product_additional_image

# Импорт асинхронных представлений
from products.async_views import (
    async_create_product, async_product_list, async_upload_images,
    async_process_order, async_product_analytics, async_search_products,
    async_system_status, async_bulk_operations, async_task_status
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'media/images', MediaImageViewSet)

# Define API URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:pk>/image/main/', product_main_image, name='product-main-image'),
    path('products/<int:product_id>/image/<int:image_id>/', product_additional_image, name='product-additional-image'),
    path('products/<int:pk>/images/', views.get_product_images, name='product-images'),
    path('products/<int:pk>/set_main_image/', views.set_main_image, name='set-main-image'),
    # City API endpoints
    path('cities/detect/', views.detect_city, name='detect-city'),
    path('cities/search/', views.search_cities_api, name='search-cities'),
    path('cities/popular/', views.popular_cities_api, name='popular-cities'),
    path('cities/validate/', views.validate_city_api, name='validate-city'),
    path('ai/upload/', ai_upload_image, name='ai-upload-image'),
    
    # Асинхронные API endpoints
    path('async/products/create/', async_create_product, name='async-create-product'),
    path('async/products/', async_product_list, name='async-product-list'),
    path('async/products/<int:product_id>/upload-images/', async_upload_images, name='async-upload-images'),
    path('async/products/<int:product_id>/analytics/', async_product_analytics, name='async-product-analytics'),
    path('async/search/', async_search_products, name='async-search-products'),
    path('async/orders/process/', async_process_order, name='async-process-order'),
    path('async/system/status/', async_system_status, name='async-system-status'),
    path('async/bulk-operations/', async_bulk_operations, name='async-bulk-operations'),
    path('async/tasks/<str:task_id>/status/', async_task_status, name='async-task-status'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'))),
]

# Добавляем статические файлы для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
