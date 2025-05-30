from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('', RedirectView.as_view(url='/api/products/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/products/', include('products.urls')),
    path('favicon.ico', RedirectView.as_view(
        url='/static/images/favicon.ico',
        permanent=False
    )),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
