from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, NumberFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django.db.models import Count, Avg, Min, Max, Sum
from .models import Product
from .serializers import ProductSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
import time
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .validators import sanitize_input, validate_name, validate_description, validate_price, validate_image
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class ProductFilter(FilterSet):
    condition = CharFilter(field_name='condition', lookup_expr='iexact')
    storage = CharFilter(field_name='storage', lookup_expr='iexact')
    phone_model = CharFilter(field_name='phone_model', lookup_expr='iexact')
    price_min = NumberFilter(field_name='price', lookup_expr='gte')
    price_max = NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['condition', 'storage',
                  'phone_model', 'price_min', 'price_max']


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'products': data,
            'total': self.page.paginator.count,
            'page': self.page.number,
            'limit': self.get_page_size(self.request),
            'totalPages': self.page.paginator.num_pages
        })


class RateLimitedView(generics.GenericAPIView):
    @method_decorator(ratelimit(key='ip', rate='100/hour', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ProductListView(RateLimitedView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Sanitize and validate query parameters
        search = sanitize_input(self.request.GET.get('search', ''))
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        queryset = Product.objects.all()

        if search:
            queryset = queryset.filter(name__icontains=search)

        if min_price:
            try:
                min_price = float(min_price)
                validate_price(min_price)
                queryset = queryset.filter(price__gte=min_price)
            except (ValueError, ValidationError):
                pass

        if max_price:
            try:
                max_price = float(max_price)
                validate_price(max_price)
                queryset = queryset.filter(price__lte=max_price)
            except (ValueError, ValidationError):
                pass

        return queryset

    def get(self, request):
        cache_key = f'products_list_{request.GET.urlencode()}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        cache.set(cache_key, data, timeout=300)
        return Response(data)


class ProductDetailView(RateLimitedView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    @method_decorator(ratelimit(key='ip', rate='50/hour', block=True))
    def get(self, request, pk):
        cache_key = f'product_detail_{pk}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        try:
            product = self.get_object()
            serializer = self.get_serializer(product)
            data = serializer.data
            cache.set(cache_key, data, timeout=300)
            return Response(data)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductCreateView(RateLimitedView):
    serializer_class = ProductSerializer

    @method_decorator(ratelimit(key='ip', rate='10/hour', block=True))
    def post(self, request):
        try:
            # Validate and sanitize input data
            data = request.data.copy()
            data['name'] = sanitize_input(data.get('name', ''))
            data['description'] = sanitize_input(data.get('description', ''))

            validate_name(data['name'])
            validate_description(data['description'])
            validate_price(float(data.get('price', 0)))

            if 'image' in request.FILES:
                validate_image(request.FILES['image'])

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Clear relevant caches
            cache.delete_pattern('products_list_*')

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(RateLimitedView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    @method_decorator(ratelimit(key='ip', rate='20/hour', block=True))
    def put(self, request, pk):
        try:
            product = self.get_object()
            data = request.data.copy()

            # Validate and sanitize input data
            if 'name' in data:
                data['name'] = sanitize_input(data['name'])
                validate_name(data['name'])

            if 'description' in data:
                data['description'] = sanitize_input(data['description'])
                validate_description(data['description'])

            if 'price' in data:
                validate_price(float(data['price']))

            if 'image' in request.FILES:
                validate_image(request.FILES['image'])

            serializer = self.get_serializer(product, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Clear relevant caches
            cache.delete_pattern('products_list_*')
            cache.delete(f'product_detail_{pk}')

            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductDeleteView(RateLimitedView):
    queryset = Product.objects.all()

    @method_decorator(ratelimit(key='ip', rate='5/hour', block=True))
    def delete(self, request, pk):
        try:
            product = self.get_object()
            product.delete()

            # Clear relevant caches
            cache.delete_pattern('products_list_*')
            cache.delete(f'product_detail_{pk}')

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description', 'phone_model']
    ordering_fields = ['price', 'created_at', 'battery_health']
    pagination_class = StandardResultsSetPagination
    permission_classes = []

    def options(self, request, *args, **kwargs):
        response = super().options(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            price_min = self.request.query_params.get('price_min')
            price_max = self.request.query_params.get('price_max')

            if price_min:
                try:
                    queryset = queryset.filter(price__gte=float(price_min))
                except ValueError:
                    pass

            if price_max:
                try:
                    queryset = queryset.filter(price__lte=float(price_max))
                except ValueError:
                    pass

            return queryset
        except Exception as e:
            print(f"Error in get_queryset: {str(e)}")
            return Product.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            # Generate a stable cache key
            params = dict(request.query_params)
            ordering = params.pop('ordering', ['-created_at'])[0]
            cache_key = f"product_list_{ordering}_{hash(frozenset(params.items()))}"

            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

            # Get queryset and serialize
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = self.get_paginated_response(
                    serializer.data).data
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data)
        except Exception as e:
            print(f"Error in list: {str(e)}")
            return Response({"error": "Internal server error"}, status=500)

    def perform_create(self, serializer):
        instance = serializer.save()
        # Clear all caches
        cache.clear()

    def perform_update(self, serializer):
        instance = serializer.save()
        # Clear all caches
        cache.clear()

    def perform_destroy(self, instance):
        instance.delete()
        # Clear all caches
        cache.clear()


class ProductStatsView(generics.GenericAPIView):
    permission_classes = []

    def get(self, request):
        try:
            stats = Product.objects.aggregate(
                total_products=Count('id'),
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                total_value=Sum('price')
            )
            return Response(stats)
        except Exception as e:
            print(f"Error in stats: {str(e)}")
            return Response({
                'total_products': 0,
                'avg_price': 0,
                'min_price': 0,
                'max_price': 0,
                'total_value': 0
            })


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = []

    def perform_update(self, serializer):
        instance = serializer.save()
        # Clear all caches
        cache.clear()

    def perform_destroy(self, instance):
        instance.delete()
        # Clear all caches
        cache.clear()


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ['home', 'catalog', 'about']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/catalog/{obj.brand}/{obj.model}/'
