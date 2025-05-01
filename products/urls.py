from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, ReviewViewSet, MediaImageViewSet

router = DefaultRouter()
router.register(r'', ProductViewSet, basename='products')
router.register(r'categories', CategoryViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'media', MediaImageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
