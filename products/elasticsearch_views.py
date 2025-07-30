from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .search_service import ProductSearchService
from .pagination import CustomPagination
from .throttling import ProductRateThrottle
from .utils import detect_user_city, normalize_city_name
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ElasticsearchProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet для продуктов с поддержкой Elasticsearch
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    pagination_class = CustomPagination
    throttle_classes = [ProductRateThrottle]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = ProductSearchService()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """
        Список продуктов с поддержкой Elasticsearch
        """
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
                'next': self._get_next_url(page, page_size, total_count),
                'previous': self._get_previous_url(page),
                'results': serializer.data,
                'page': page,
                'limit': page_size,
                'totalPages': (total_count + page_size - 1) // page_size
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in product list: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _collect_filters(self, request) -> Dict[str, Any]:
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
    
    def _get_next_url(self, page: int, page_size: int, total_count: int) -> str:
        """Генерация URL для следующей страницы"""
        if page * page_size >= total_count:
            return None
        
        params = self.request.query_params.copy()
        params['page'] = page + 1
        return f"?{params.urlencode()}"
    
    def _get_previous_url(self, page: int) -> str:
        """Генерация URL для предыдущей страницы"""
        if page <= 1:
            return None
        
        params = self.request.query_params.copy()
        params['page'] = page - 1
        return f"?{params.urlencode()}"
    
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """
        Получение подсказок для автодополнения
        """
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 5))
        
        if not query or len(query.strip()) < 2:
            return Response({'suggestions': []})
        
        try:
            suggestions = self.search_service.suggest_products(query, limit)
            return Response({'suggestions': suggestions})
        except Exception as e:
            logger.error(f"Error in suggestions: {e}")
            return Response({'suggestions': []})
    
    @action(detail=False, methods=['get'])
    def facets(self, request):
        """
        Получение агрегаций для фасетного поиска
        """
        try:
            filters = self._collect_filters(request)
            facets = self.search_service.get_facets(filters)
            return Response(facets)
        except Exception as e:
            logger.error(f"Error in facets: {e}")
            return Response({})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Статистика продуктов
        """
        try:
            # Получаем базовые фильтры
            filters = self._collect_filters(request)
            
            # Получаем агрегации
            facets = self.search_service.get_facets(filters)
            
            # Дополнительная статистика
            stats = {
                'total_products': facets.get('total', 0),
                'price_ranges': facets.get('price_ranges', {}),
                'conditions': facets.get('conditions', {}),
                'cities': facets.get('cities', {}),
                'colors': facets.get('colors', {}),
                'storage': facets.get('storage', {})
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"Error in stats: {e}")
            return Response({'error': 'Failed to get stats'})
    
    @method_decorator(cache_page(60 * 5))  # Кэш на 5 минут
    @method_decorator(vary_on_cookie)
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Популярные продукты
        """
        try:
            # Получаем топовые продукты
            products, _ = self.search_service.search_products(
                filters={'is_top': True},
                sort='-rating',
                page=1,
                page_size=10
            )
            
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in popular products: {e}")
            return Response([])
    
    @action(detail=False, methods=['get'])
    def search_analytics(self, request):
        """
        Аналитика поиска
        """
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
            logger.error(f"Error in search analytics: {e}")
            return Response({'error': 'Failed to analyze search'}) 