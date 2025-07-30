from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg, F, Q
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from .cache_service import CacheService, cache_products, cache_search, cache_facets, cache_suggestions, cache_stats
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Product, Category, Review
from .media_models import MediaImage
from .serializers import ProductSerializer, CategorySerializer, ReviewSerializer, MediaImageSerializer
from .validators import validate_image
from .filters import ProductFilter
from .pagination import CustomPagination
from .throttling import ProductRateThrottle
from .utils import get_product_stats, detect_user_city, search_cities, get_popular_cities, normalize_city_name, validate_city_name
from decimal import Decimal
from rest_framework import serializers
from django.http import HttpResponse
import base64
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import requests
from django.http import FileResponse, Http404

# Elasticsearch imports
try:
    from .search_service import ProductSearchService
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY')
GOOGLE_VISION_ENDPOINT = 'https://vision.googleapis.com/v1/images:annotate'


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
        'price', '-price', 'created_at', '-created_at', 'battery_health', '-battery_health',
        'condition', '-condition', 'body_condition', '-body_condition', 'screen_condition', '-screen_condition'
    ]
    ordering = ['-created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем Elasticsearch сервис если доступен
        if ELASTICSEARCH_AVAILABLE and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            self.search_service = ProductSearchService()
        else:
            self.search_service = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'seller').prefetch_related('product_images')
        
        # Log all query parameters
        print("\n=== Query Parameters ===")
        print(self.request.query_params)
        
        # If no filters are provided, return all products
        if not self.request.query_params:
            print("No filters provided, returning all products")
            return queryset
        
        filters = {}
        
        # Apply search if present
        search_query = self.request.query_params.get('search')
        if search_query:
            print(f"\nSearch query: {search_query}")
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(phone_model__icontains=search_query)
            )
        
        # Price range filter
        price_range = self.request.query_params.get('priceRange')
        if price_range:
            print(f"\nPrice range: {price_range}")
            try:
                min_price, max_price = map(float, price_range.split(','))
                print(f"Parsed prices: min={min_price}, max={max_price}")
                
                # Convert prices to Decimal for proper comparison
                min_price = Decimal(str(min_price)).quantize(Decimal('0.01'))
                max_price = Decimal(str(max_price)).quantize(Decimal('0.01'))
                
                if min_price >= 0 and max_price >= min_price:
                    filters['price__gte'] = min_price
                    filters['price__lte'] = max_price
                    print(f"Applied price filters: {filters['price__gte']} - {filters['price__lte']}")
                else:
                    print(f"Invalid price range: min={min_price}, max={max_price}")
            except (ValueError, AttributeError) as e:
                print(f"Error parsing price range: {e}")
                pass

        # Battery health filter
        battery_health = self.request.query_params.get('batteryHealth')
        if battery_health:
            print(f"\nBattery health: {battery_health}")
            try:
                min_health, max_health = map(float, battery_health.split(','))
                if 0 <= min_health <= 100 and 0 <= max_health <= 100 and min_health <= max_health:
                    filters['battery_health__gte'] = min_health
                    filters['battery_health__lte'] = max_health
                    print(f"Applied battery health filters: {filters['battery_health__gte']} - {filters['battery_health__lte']}")
                else:
                    print(f"Invalid battery health range: min={min_health}, max={max_health}")
            except (ValueError, AttributeError) as e:
                print(f"Error parsing battery health: {e}")
                pass

        # комплектация filter
        комплектация = self.request.query_params.get('комплектация')
        if комплектация:
            print(f"\nкомплектация: {комплектация}")
            items = комплектация.split(',')
            if items:
                filters['package_contents__contains'] = items
                print(f"Applied комплектация filters: {items}")

        # Apply other filters
        filter_params = {
            'category': 'category',
            'phone_model': 'phone_model',
            'storage': 'storage',
            'condition': 'condition',
            'color': 'color',
            'body_condition': 'body_condition',
            'screen_condition': 'screen_condition'
        }

        for param, field in filter_params.items():
            value = self.request.query_params.get(param)
            if value:
                print(f"\n{param}: {value}")
                filters[field] = value

        # Handle turbo filter separately to convert string to boolean
        turbo_value = self.request.query_params.get('turbo')
        if turbo_value is not None:
            print(f"\nTurbo: {turbo_value}")
            filters['turbo'] = turbo_value.lower() == 'true'

        # City filter
        city = self.request.query_params.get('city')
        if city:
            print(f"\nCity filter: {city}")
            # Нормализуем название города для поиска
            normalized_city = normalize_city_name(city)
            filters['city__icontains'] = normalized_city
            print(f"Applied city filter: {normalized_city}")

        # Apply all filters
        if filters:
            print("\n=== Applied Filters ===")
            print(filters)
            queryset = queryset.filter(**filters)
            print(f"\nQuery result count: {queryset.count()}")
            print(f"Query SQL: {str(queryset.query)}")
        
        # Debug: Print all products with their prices
        print("\n=== All Products with Prices ===")
        for p in Product.objects.values('id', 'title', 'price'):
            print(f"ID: {p['id']}, Title: {p['title']}, Price: {p['price']}")
        
        return queryset

    def list(self, request, *args, **kwargs):
        # Проверяем кэш для GET-запросов
        if request.method == 'GET':
            # Собираем параметры для ключа кэша
            filters = self._collect_filters(request)
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Пытаемся получить из кэша
            cached_result = CacheService.get_cached_products(filters, page, page_size)
            if cached_result:
                return Response(cached_result)
        
        # Проверяем, используем ли мы Elasticsearch
        use_elasticsearch = (
            self.search_service is not None and
            getattr(settings, 'ELASTICSEARCH_ENABLED', False)
        )
        
        if use_elasticsearch:
            return self._elasticsearch_list(request, *args, **kwargs)
        else:
            return self._postgresql_list(request, *args, **kwargs)
    
    def _elasticsearch_list(self, request, *args, **kwargs):
        """Поиск через Elasticsearch"""
        try:
            # Получаем параметры запроса
            search_query = request.query_params.get('search', '')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('limit', 20))
            ordering = request.query_params.get('ordering', '')
            
            # Собираем фильтры
            filters = self._collect_filters(request)
            
            # Определяем город пользователя если не указан
            if not filters.get('city') and not search_query:
                user_city = detect_user_city(request)
                if user_city:
                    filters['city'] = user_city
            
            # Выполняем поиск через Elasticsearch
            products, total_count = self.search_service.search_products(
                query=search_query,
                filters=filters,
                sort=ordering,
                page=page,
                page_size=page_size
            )
            
            # Сериализуем результаты
            serializer = self.get_serializer(products, many=True)
            
            # Формируем ответ
            response_data = {
                'count': total_count,
                'next': self._get_next_url(page, page_size, total_count, request),
                'previous': self._get_previous_url(page, request),
                'results': serializer.data,
                'page': page,
                'limit': page_size,
                'totalPages': (total_count + page_size - 1) // page_size,
                'search_engine': 'elasticsearch'
            }
            
            # Сохраняем в кэш
            CacheService.set_cached_products(response_data, filters, page, page_size)
            
            return Response(response_data)
            
        except Exception as e:
            # Fallback к PostgreSQL при ошибке Elasticsearch
            print(f"Elasticsearch error: {e}")
            return self._postgresql_list(request, *args, **kwargs)
    
    def _postgresql_list(self, request, *args, **kwargs):
        """Поиск через PostgreSQL (fallback)"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['search_engine'] = 'postgresql'
            
            # Сохраняем в кэш для GET-запросов
            if request.method == 'GET':
                filters = self._collect_filters(request)
                page_num = int(request.GET.get('page', 1))
                page_size = int(request.GET.get('page_size', 20))
                CacheService.set_cached_products(response.data, filters, page_num, page_size)
            
            return response
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        response_data.append({'search_engine': 'postgresql'})
        
        # Сохраняем в кэш для GET-запросов
        if request.method == 'GET':
            filters = self._collect_filters(request)
            page_num = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            CacheService.set_cached_products(response_data, filters, page_num, page_size)
        
        return Response(response_data)
    
    def _collect_filters(self, request):
        """Сбор фильтров из параметров запроса"""
        filters = {}
        
        # Базовые фильтры
        filter_params = {
            'priceRange': 'priceRange',
            'batteryHealth': 'batteryHealth',
            'condition': 'condition',
            'color': 'color',
            'storage': 'storage',
            'body_condition': 'body_condition',
            'screen_condition': 'screen_condition',
            'turbo': 'turbo',
            'city': 'city',
            'category': 'category',
            'phone_model': 'phone_model',
        }
        
        for param, key in filter_params.items():
            value = request.query_params.get(param)
            if value is not None and value != '':
                if param == 'turbo':
                    filters[key] = value.lower() == 'true'
                else:
                    filters[key] = value
        
        # Фильтр по комплектации
        комплектация = request.query_params.get('комплектация')
        if комплектация:
            if isinstance(комплектация, str):
                filters['комплектация'] = [item.strip() for item in комплектация.split(',')]
            else:
                filters['комплектация'] = комплектация
        
        return filters
    
    def _get_next_url(self, page, page_size, total_count, request):
        """Генерация URL для следующей страницы"""
        if page * page_size >= total_count:
            return None
        
        params = request.query_params.copy()
        params['page'] = page + 1
        return f"?{params.urlencode()}"
    
    def _get_previous_url(self, page, request):
        """Генерация URL для предыдущей страницы"""
        if page <= 1:
            return None
        
        params = request.query_params.copy()
        params['page'] = page - 1
        return f"?{params.urlencode()}"

    def perform_create(self, serializer):
        try:
            # Get category from request data
            category_name = self.request.data.get('category')
            if category_name:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Category for {category_name}'}
                )
                serializer.validated_data['category'] = category

            # Save the product first
            product = serializer.save()

            # Handle images
            images = self.request.FILES.getlist('images')
            if images:
                # First image as main
                product.main_image = images[0]
                product.save()
                
                # Rest as additional images
                for image in images[1:]:
                    try:
                        validate_image(image)
                        media_image = MediaImage.objects.create(
                            image_file=image,
                            product=product,
                            title=f"{product.title} - image {product.product_images.count() + 1}"
                        )
                        product.product_images.add(media_image)
                    except Exception as e:
                        raise serializers.ValidationError(f'Error processing image: {str(e)}')

            return product
        except Exception as e:
            raise serializers.ValidationError(str(e))

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

    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Загрузка изображений для товара"""
        product = self.get_object()
        images = request.FILES.getlist('images', [])
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_images = []
        for image in images:
            try:
                validate_image(image)
                # Create media image
                media_image = MediaImage.objects.create(
                    image_file=image,
                    product=product,
                    title=f"{product.title} - image {len(uploaded_images) + 1}"
                )
                uploaded_images.append(media_image)
            except Exception as e:
                return Response(
                    {'error': f'Error processing image: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            MediaImageSerializer(uploaded_images, many=True, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def set_main_image(self, request, pk=None):
        """Установка главного изображения товара"""
        product = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'image_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = product.media_images.get(id=image_id)
            # Устанавливаем новое главное изображение
            product.main_image = image.image_data
            product.save()
            return Response(MediaImageSerializer(image, context={'request': request}).data)
        except MediaImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def delete_image(self, request, pk=None):
        """Удаление изображения товара"""
        product = self.get_object()
        image_id = request.query_params.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'image_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = product.media_images.get(id=image_id)
            # Если удаляем главное изображение, сбрасываем его
            if product.main_image and product.main_image == image.image_data:
                product.main_image = None
                product.save()
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MediaImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='raise-to-top')
    def raise_to_top(self, request, pk=None):
        product = self.get_object()
        product.is_top = True
        product.save(update_fields=['is_top'])
        return Response({'status': 'raised to top', 'id': product.id, 'is_top': product.is_top})

    @action(detail=True, methods=['delete'], url_path='remove-from-top')
    def remove_from_top(self, request, pk=None):
        product = self.get_object()
        product.is_top = False
        product.save(update_fields=['is_top'])
        return Response({'status': 'removed from top', 'id': product.id, 'is_top': product.is_top})
    
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """Получение подсказок для автодополнения"""
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 5))
        
        if not query or len(query.strip()) < 2:
            return Response({'suggestions': []})
        
        # Пытаемся получить из кэша
        cached_suggestions = CacheService.get_cached_suggestions(query, limit)
        if cached_suggestions is not None:
            return Response({'suggestions': cached_suggestions})
        
        if not self.search_service:
            return Response({'suggestions': []})
        
        try:
            suggestions = self.search_service.suggest_products(query, limit)
            
            # Сохраняем в кэш
            CacheService.set_cached_suggestions(suggestions, query, limit)
            
            return Response({'suggestions': suggestions})
        except Exception as e:
            print(f"Error in suggestions: {e}")
            return Response({'suggestions': []})
    
    @action(detail=False, methods=['get'])
    def facets(self, request):
        """Получение агрегаций для фасетного поиска"""
        # Пытаемся получить из кэша
        filters = self._collect_filters(request)
        cached_facets = CacheService.get_cached_facets(filters)
        if cached_facets is not None:
            return Response(cached_facets)
        
        if not self.search_service:
            return Response({})
        
        try:
            facets = self.search_service.get_facets(filters)
            
            # Сохраняем в кэш
            CacheService.set_cached_facets(facets, filters)
            
            return Response(facets)
        except Exception as e:
            print(f"Error in facets: {e}")
            return Response({})
    
    @action(detail=False, methods=['get'])
    def search_analytics(self, request):
        """Аналитика поиска"""
        if not self.search_service:
            return Response({'error': 'Elasticsearch not available'})
        
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Query parameter required'})
        
        try:
            # Получаем результаты поиска
            products, total_count = self.search_service.search_products(
                query=query,
                page=1,
                page_size=100  # Больше результатов для анализа
            )
            
            # Анализируем результаты
            analytics = {
                'query': query,
                'total_results': total_count,
                'price_range': {
                    'min': min([p.price for p in products]) if products else 0,
                    'max': max([p.price for p in products]) if products else 0,
                    'avg': sum([p.price for p in products]) / len(products) if products else 0
                },
                'conditions': {},
                'cities': {},
                'models': {}
            }
            
            # Подсчитываем статистику
            for product in products:
                # Состояния
                analytics['conditions'][product.condition] = analytics['conditions'].get(product.condition, 0) + 1
                
                # Города
                if product.city:
                    analytics['cities'][product.city] = analytics['cities'].get(product.city, 0) + 1
                
                # Модели
                if product.phone_model:
                    analytics['models'][product.phone_model] = analytics['models'].get(product.phone_model, 0) + 1
            
            return Response(analytics)
        except Exception as e:
            print(f"Error in search analytics: {e}")
            return Response({'error': 'Failed to analyze search'})


class ProductStatsView(viewsets.ViewSet):
    def list(self, request):
        stats = get_product_stats()
        return Response(stats)


class MediaImageViewSet(viewsets.ModelViewSet):
    queryset = MediaImage.objects.all()
    serializer_class = MediaImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save()


@api_view(['GET'])
def get_product_image(request, pk, image_type):
    """Serve product images (main or additional)"""
    try:
        product = Product.objects.get(id=pk)
        
        if image_type == 'main':
            # If no main image, try to get first additional image
            if not product.main_image:
                first_image = MediaImage.objects.filter(product=product).first()
                if first_image and first_image.image_file:
                    # Set as main image and save
                    product.main_image = first_image.image_file
                    product.save(update_fields=['main_image'])
                    # Return the image file
                    return FileResponse(first_image.image_file.open('rb'), content_type='image/webp')
                return HttpResponse(status=404)
            
            # Return existing main image
            if product.main_image:
                return FileResponse(product.main_image.open('rb'), content_type='image/webp')
            return HttpResponse(status=404)
        else:
            # Get additional image
            try:
                image = MediaImage.objects.get(id=image_type, product=product)
                if not image.image_file:
                    return HttpResponse(status=404)
                return FileResponse(image.image_file.open('rb'), content_type='image/webp')
            except MediaImage.DoesNotExist:
                return HttpResponse(status=404)
    except Product.DoesNotExist:
        return HttpResponse(status=404)

@api_view(['GET'])
def get_product_images(request, pk):
    try:
        product = Product.objects.get(id=pk)
        images = []
        
        # Add main image if exists
        if product.main_image:
            images.append({
                'id': 'main',
                'type': 'webp',
                'url': f'/api/products/{pk}/image/main/'
            })
        
        # Add additional images
        additional_images = MediaImage.objects.filter(product=product)
        for img in additional_images:
            if img.image_file:
                images.append({
                    'id': img.id,
                    'type': 'webp',
                    'url': f'/api/products/{pk}/image/{img.id}/'
                })
        
        return Response(images)
    except Product.DoesNotExist:
        return Response(status=404)

@api_view(['POST'])
def set_main_image(request, pk):
    """Set main image from additional images"""
    try:
        product = Product.objects.get(id=pk)
        image_id = request.data.get('image_id')
        if not image_id:
            return Response({'error': 'No image_id provided'}, status=400)
            
        try:
            image = MediaImage.objects.get(id=image_id, product=product)
            if not image.image_data or not image.image_type:
                return Response({'error': 'Image has no data'}, status=400)
                
            # Set as main image
            product.main_image = image.image_data
            product.main_image_type = image.image_type
            product.save()
            
            return Response({'status': 'success'})
        except MediaImage.DoesNotExist:
            return Response({'error': 'Image not found'}, status=404)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)


@csrf_exempt
def bitrix24_contact_update(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Проверка токена приложения
            token = data.get('auth', {}).get('application_token')
            if token != '85rjuk37xix2mqomrvx3c2vfvn792jz8':
                return JsonResponse({'error': 'Invalid token'}, status=403)
            print("Bitrix24 contact update:", data)
            # ... обработка события ...
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Only POST allowed'}, status=405)


@api_view(['GET'])
def detect_city(request):
    """
    Определяет город пользователя по IP адресу
    """
    try:
        city = detect_user_city(request)
        if city:
            normalized_city = normalize_city_name(city)
            return Response({
                'success': True,
                'city': normalized_city,
                'detected': True
            })
        else:
            return Response({
                'success': True,
                'city': None,
                'detected': False,
                'message': 'Не удалось определить город'
            })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def search_cities_api(request):
    """
    API для поиска городов
    """
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    if not query or len(query) < 2:
        return Response({
            'success': False,
            'error': 'Запрос должен содержать минимум 2 символа'
        }, status=400)
    
    try:
        cities = search_cities(query, limit)
        return Response({
            'success': True,
            'cities': cities,
            'count': len(cities)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def popular_cities_api(request):
    """
    API для получения списка популярных городов
    """
    try:
        cities = get_popular_cities()
        return Response({
            'success': True,
            'cities': cities,
            'count': len(cities)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def validate_city_api(request):
    """
    API для валидации названия города
    """
    city_name = request.data.get('city', '').strip()
    
    if not city_name:
        return Response({
            'success': False,
            'error': 'Название города не может быть пустым'
        }, status=400)
    
    try:
        is_valid = validate_city_name(city_name)
        normalized_city = normalize_city_name(city_name) if is_valid else None
        
        return Response({
            'success': True,
            'is_valid': is_valid,
            'normalized_city': normalized_city,
            'original_city': city_name
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def ai_upload_image(request):
    """
    Принимает изображение, сохраняет во временную папку, отправляет в Google Vision API, возвращает распознанные данные.
    """
    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'No image provided'}, status=400)
    # Сохраняем во временную папку
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'ai_temp')
    os.makedirs(temp_dir, exist_ok=True)
    file_name = default_storage.save(f'ai_temp/{image.name}', ContentFile(image.read()))
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    file_url = default_storage.url(file_name)

    # Читаем файл и кодируем в base64
    with open(file_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')

    # Готовим запрос к Vision API
    vision_payload = {
        "requests": [
            {
                "image": {"content": img_base64},
                "features": [
                    {"type": "TEXT_DETECTION"},
                    {"type": "LABEL_DETECTION"},
                    {"type": "OBJECT_LOCALIZATION"},
                    {"type": "LOGO_DETECTION"},
                ]
            }
        ]
    }
    vision_params = {"key": GOOGLE_VISION_API_KEY}
    vision_resp = requests.post(GOOGLE_VISION_ENDPOINT, params=vision_params, json=vision_payload)
    if vision_resp.status_code != 200:
        return Response({'error': 'Vision API error', 'details': vision_resp.text}, status=500)
    vision_data = vision_resp.json()

    return Response({
        'file_name': file_name,
        'file_url': file_url,
        'vision': vision_data
    }, status=201)

# --- Новый код для отдачи main_image и additional_image ---
from rest_framework.decorators import api_view

@api_view(['GET'])
def product_main_image(request, pk):
    """Отдаёт главное фото товара по id"""
    try:
        product = Product.objects.get(pk=pk)
        if not product.main_image or not product.main_image.name:
            raise Http404('Main image not found')
        # Проверка, что файл реально существует
        if not product.main_image.storage.exists(product.main_image.name):
            raise Http404('Main image file does not exist')
        return FileResponse(product.main_image.open('rb'), content_type='image/webp')
    except Product.DoesNotExist:
        raise Http404('Product not found')

@api_view(['GET'])
def product_additional_image(request, product_id, image_id):
    """Отдаёт дополнительное фото по id товара и id фото"""
    try:
        image = MediaImage.objects.get(pk=image_id, product_id=product_id)
        if not image.image_file:
            raise Http404('Image not found')
        return FileResponse(image.image_file.open('rb'), content_type='image/webp')
    except MediaImage.DoesNotExist:
        raise Http404('Image not found')
