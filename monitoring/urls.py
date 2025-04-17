from django.urls import path
from .views import LiveMetricsView

urlpatterns = [
    path('live/', LiveMetricsView.as_view(), name='live-metrics'),
]
    