from django.urls import path
from .views import (
    ProductListView, ProductDetailView, ProductCreateView,
    ProductUpdateView, ProductDeleteView, ProductStatsView,
    ProductListCreateView, ProductRetrieveUpdateDestroyView
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list'),
    path('stats', ProductStatsView.as_view(), name='product-stats'),
    path('<int:pk>', ProductRetrieveUpdateDestroyView.as_view(),
         name='product-detail'),
]
