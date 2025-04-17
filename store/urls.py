from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import RedirectView
from products.views import StaticViewSitemap, ProductSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # 301 Redirects
    path('old-catalog/', RedirectView.as_view(url='/catalog/', permanent=True)),
    path('products/', RedirectView.as_view(url='/catalog/', permanent=True)),
    path('phones/', RedirectView.as_view(url='/catalog/', permanent=True)),
] 