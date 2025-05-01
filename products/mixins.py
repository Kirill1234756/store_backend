from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

class CacheMixin:
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @method_decorator(vary_on_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs) 