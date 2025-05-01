import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__name')
    phone_model = django_filters.CharFilter(field_name='phone_model', lookup_expr='icontains')
    storage = django_filters.CharFilter(field_name='storage')
    condition = django_filters.CharFilter(field_name='condition')
    color = django_filters.CharFilter(field_name='color')
    body_condition = django_filters.CharFilter(field_name='body_condition')
    screen_condition = django_filters.CharFilter(field_name='screen_condition')
    turbo = django_filters.BooleanFilter(field_name='turbo')
    
    priceRange = django_filters.CharFilter(method='filter_price_range')
    batteryHealth = django_filters.CharFilter(method='filter_battery_health')
    комплектация = django_filters.CharFilter(method='filter_комплектация')

    class Meta:
        model = Product
        fields = [
            'min_price', 'max_price', 'category', 'phone_model', 'storage', 
            'condition', 'color', 'body_condition', 'screen_condition', 'turbo',
            'priceRange', 'batteryHealth', 'комплектация'
        ]

    def filter_price_range(self, queryset, name, value):
        try:
            min_price, max_price = map(float, value.split(','))
            return queryset.filter(price__gte=min_price, price__lte=max_price)
        except (ValueError, AttributeError):
            return queryset

    def filter_battery_health(self, queryset, name, value):
        try:
            min_health, max_health = map(float, value.split(','))
            return queryset.filter(battery_health__gte=min_health, battery_health__lte=max_health)
        except (ValueError, AttributeError):
            return queryset

    def filter_комплектация(self, queryset, name, value):
        try:
            items = value.split(',')
            for item in items:
                queryset = queryset.filter(комплектация__contains=[item])
            return queryset
        except (ValueError, AttributeError):
            return queryset 