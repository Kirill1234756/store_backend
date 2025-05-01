from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg, F, Q
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from .models import Product, Category, Review, MediaImage
from .serializers import ProductSerializer, CategorySerializer, ReviewSerializer, MediaImageSerializer
from .validators import validate_image
from .filters import ProductFilter
from .pagination import CustomPagination
from .throttling import ProductRateThrottle
from .utils import get_product_stats


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products')
        ).order_by('name')


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.select_related('user', 'product').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = CustomPagination
    search_fields = ['title', 'description', 'phone_model', 'storage', 'color']
    ordering_fields = [
        'price', 'created_at', 'battery_health', 'condition',
        'body_condition', 'screen_condition'
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'seller').prefetch_related('additional_images')
        
        # Log all query parameters
        print("Query parameters:", self.request.query_params)
        
        # Apply search if present
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(phone_model__icontains=search_query) |
                Q(storage__icontains=search_query) |
                Q(color__icontains=search_query)
            )
        
        # Apply filters
        filters = {}
        
        # Price range filter
        price_range = self.request.query_params.get('priceRange')
        if price_range:
            try:
                min_price, max_price = map(float, price_range.split(','))
                if min_price >= 0 and max_price >= min_price:
                    filters['price__gte'] = min_price
                    filters['price__lte'] = max_price
            except (ValueError, AttributeError) as e:
                print(f"Error parsing price range: {e}")
                pass

        # Battery health filter
        battery_health = self.request.query_params.get('batteryHealth')
        if battery_health:
            try:
                min_health, max_health = map(float, battery_health.split(','))
                filters['battery_health__gte'] = min_health
                filters['battery_health__lte'] = max_health
            except (ValueError, AttributeError):
                pass

        # комплектация filter
        комплектация = self.request.query_params.get('комплектация')
        if комплектация:
            items = комплектация.split(',')
            for item in items:
                queryset = queryset.filter(комплектация__contains=[item])

        # Apply other filters
        for param in ['category', 'phone_model', 'storage', 'condition', 
                     'color', 'body_condition', 'screen_condition']:
            value = self.request.query_params.get(param)
            if value:
                filters[f'{param}'] = value

        # Handle turbo filter separately to convert string to boolean
        turbo_value = self.request.query_params.get('turbo')
        if turbo_value is not None:
            filters['turbo'] = turbo_value.lower() == 'true'

        if filters:
            queryset = queryset.filter(**filters)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        image = self.request.FILES.get('image')
        if image:
            validate_image(image)
        serializer.save()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = get_product_stats()
        return Response(stats)

    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductStatsView(viewsets.ViewSet):
    def list(self, request):
        stats = get_product_stats()
        return Response(stats)


class MediaImageViewSet(viewsets.ModelViewSet):
    queryset = MediaImage.objects.all()
    serializer_class = MediaImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()
