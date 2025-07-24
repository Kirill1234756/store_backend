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
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),  # Include all API URLs under api/ prefix
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('@iconmain.jpg', RedirectView.as_view(
        url='/static/images/iconmain.jpg',
        permanent=False
    )),
    path('products/<int:pk>/images/', views.get_product_images, name='product-images-direct'),
    path('products/<int:pk>/set_main_image/', views.set_main_image, name='set-main-image-direct'),
    path('bitrix24/contact_update/', views.bitrix24_contact_update, name='bitrix24_contact_update'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
