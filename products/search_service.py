from elasticsearch_dsl import Search, Q
from elasticsearch import Elasticsearch
from django_elasticsearch_dsl.search import Search as DjangoSearch
from .search_indexes import ProductDocument
from .models import Product
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProductSearchService:
    """Сервис для поиска продуктов через Elasticsearch"""
    
    def __init__(self):
        # Прямое подключение к Elasticsearch
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index_name = 'products'
    
    def search_products(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict] = None,
        sort: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Product], int]:
        """
        Поиск продуктов с фильтрацией и сортировкой через прямое подключение к Elasticsearch
        
        Args:
            query: Поисковый запрос
            filters: Словарь фильтров
            sort: Поле для сортировки
            page: Номер страницы
            page_size: Размер страницы
            
        Returns:
            Tuple[List[Product], int]: Список продуктов и общее количество
        """
        try:
            # Создаем поисковый запрос
            search_body = {
                "query": {
                    "bool": {
                        "must": [],
                        "filter": []
                    }
                },
                "sort": [
                    {"is_top": {"order": "desc"}},
                    {"created_at": {"order": "desc"}}
                ],
                "from": (page - 1) * page_size,
                "size": page_size
            }
            
            # Добавляем поисковый запрос
            if query:
                search_body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "description^2", "phone_model^2", "category_name"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            
            # Применяем фильтры
            if filters:
                self._apply_filters_direct(search_body, filters)
            
            # Применяем сортировку
            if sort:
                self._apply_sorting_direct(search_body, sort)
            
            # Выполняем поиск
            response = self.es.search(index=self.index_name, body=search_body)
            
            # Получаем ID найденных продуктов
            product_ids = [int(hit['_id']) for hit in response['hits']['hits']]
            
            # Получаем продукты из базы данных в том же порядке
            products = list(Product.objects.filter(id__in=product_ids))
            products_dict = {p.id: p for p in products}
            ordered_products = [products_dict[pid] for pid in product_ids if pid in products_dict]
            
            return ordered_products, response['hits']['total']['value']
            
        except Exception as e:
            logger.error(f"Error in Elasticsearch search: {e}")
            # Fallback к Django ORM
            return self._fallback_search(query, filters, sort, page, page_size)
    
    def _apply_filters_direct(self, search_body: Dict, filters: Dict):
        """Применение фильтров к поисковому запросу через прямое подключение"""
        
        # Фильтр по цене
        if 'priceRange' in filters:
            try:
                min_price, max_price = map(float, filters['priceRange'].split(','))
                search_body["query"]["bool"]["filter"].append({
                    "range": {"price": {"gte": min_price, "lte": max_price}}
                })
            except (ValueError, AttributeError):
                pass
        
        # Фильтр по состоянию батареи
        if 'batteryHealth' in filters:
            try:
                min_health, max_health = map(float, filters['batteryHealth'].split(','))
                search_body["query"]["bool"]["filter"].append({
                    "range": {"battery_health": {"gte": min_health, "lte": max_health}}
                })
            except (ValueError, AttributeError):
                pass
        
        # Фильтр по состоянию
        if 'condition' in filters and filters['condition']:
            search_body["query"]["bool"]["filter"].append({
                "term": {"condition": filters['condition']}
            })
        
        # Фильтр по цвету
        if 'color' in filters and filters['color']:
            search_body["query"]["bool"]["filter"].append({
                "term": {"color": filters['color']}
            })
        
        # Фильтр по памяти
        if 'storage' in filters and filters['storage']:
            search_body["query"]["bool"]["filter"].append({
                "term": {"storage": filters['storage']}
            })
        
        # Фильтр по состоянию корпуса
        if 'body_condition' in filters and filters['body_condition']:
            search_body["query"]["bool"]["filter"].append({
                "term": {"body_condition": filters['body_condition']}
            })
        
        # Фильтр по состоянию экрана
        if 'screen_condition' in filters and filters['screen_condition']:
            search_body["query"]["bool"]["filter"].append({
                "term": {"screen_condition": filters['screen_condition']}
            })
        
        # Фильтр по турбо
        if 'turbo' in filters and filters['turbo'] is not None:
            search_body["query"]["bool"]["filter"].append({
                "term": {"turbo": filters['turbo']}
            })
        
        # Фильтр по городу
        if 'city' in filters and filters['city']:
            search_body["query"]["bool"]["filter"].append({
                "match": {"city": filters['city']}
            })
        
        # Фильтр по комплектации
        if 'комплектация' in filters and filters['комплектация']:
            if isinstance(filters['комплектация'], list):
                for item in filters['комплектация']:
                    search_body["query"]["bool"]["filter"].append({
                        "term": {"package_contents": item}
                    })
            elif isinstance(filters['комплектация'], str):
                items = filters['комплектация'].split(',')
                for item in items:
                    search_body["query"]["bool"]["filter"].append({
                        "term": {"package_contents": item.strip()}
                    })
        
        # Фильтр по категории
        if 'category' in filters and filters['category']:
            search_body["query"]["bool"]["filter"].append({
                "match": {"category_name": filters['category']}
            })
        
        # Фильтр по модели телефона
        if 'phone_model' in filters and filters['phone_model']:
            search_body["query"]["bool"]["filter"].append({
                "match": {"phone_model": filters['phone_model']}
            })
        
        # Фильтр по активности
        search_body["query"]["bool"]["filter"].append({
            "term": {"is_active": True}
        })
    
    def _apply_sorting_direct(self, search_body: Dict, sort: str):
        """Применение сортировки к поисковому запросу через прямое подключение"""
        
        sort_mapping = {
            'price': {"price": {"order": "asc"}},
            '-price': {"price": {"order": "desc"}},
            'created_at': {"created_at": {"order": "asc"}},
            '-created_at': {"created_at": {"order": "desc"}},
            'battery_health': {"battery_health": {"order": "asc"}},
            '-battery_health': {"battery_health": {"order": "desc"}},
            'rating': {"rating": {"order": "asc"}},
            '-rating': {"rating": {"order": "desc"}},
            'title': {"title.raw": {"order": "asc"}},
            '-title': {"title.raw": {"order": "desc"}},
        }
        
        if sort in sort_mapping:
            search_body["sort"] = [sort_mapping[sort]]
        else:
            # Сортировка по умолчанию
            search_body["sort"] = [
                {"is_top": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
    
    def _fallback_search(self, query, filters, sort, page, page_size):
        """Fallback к Django ORM при ошибке Elasticsearch"""
        queryset = Product.objects.filter(is_active=True)
        
        if query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(phone_model__icontains=query)
            )
        
        # Применяем базовые фильтры
        if filters:
            if 'priceRange' in filters:
                try:
                    min_price, max_price = map(float, filters['priceRange'].split(','))
                    queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
                except (ValueError, AttributeError):
                    pass
            
            if 'condition' in filters and filters['condition']:
                queryset = queryset.filter(condition=filters['condition'])
            
            if 'color' in filters and filters['color']:
                queryset = queryset.filter(color=filters['color'])
        
        # Сортировка
        if sort == 'price':
            queryset = queryset.order_by('price')
        elif sort == '-price':
            queryset = queryset.order_by('-price')
        elif sort == 'created_at':
            queryset = queryset.order_by('created_at')
        elif sort == '-created_at':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-is_top', '-created_at')
        
        total = queryset.count()
        products = queryset[(page - 1) * page_size:page * page_size]
        
        return list(products), total
    
    def suggest_products(self, query: str, limit: int = 5) -> List[str]:
        """Получение подсказок для автодополнения"""
        try:
            search = self.search.suggest('suggestions', query, {
                'completion': {
                    'field': 'title.suggest',
                    'size': limit,
                    'skip_duplicates': True
                }
            })
            
            response = search.execute()
            suggestions = []
            
            if hasattr(response, 'suggest') and 'suggestions' in response.suggest:
                for suggestion in response.suggest.suggestions[0].options:
                    suggestions.append(suggestion.text)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in Elasticsearch suggestions: {e}")
            return []
    
    def get_facets(self, filters: Optional[Dict] = None) -> Dict:
        """Получение агрегаций для фасетного поиска"""
        try:
            search = self.search
            
            if filters:
                search = self._apply_filters(search, filters)
            
            # Агрегации
            search.aggs.bucket('conditions', 'terms', field='condition')
            search.aggs.bucket('colors', 'terms', field='color')
            search.aggs.bucket('storage', 'terms', field='storage')
            search.aggs.bucket('cities', 'terms', field='city.raw', size=20)
            search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
                {'from': 0, 'to': 10000},
                {'from': 10000, 'to': 50000},
                {'from': 50000, 'to': 100000},
                {'from': 100000}
            ])
            
            response = search.execute()
            
            return {
                'conditions': {bucket.key: bucket.doc_count for bucket in response.aggregations.conditions.buckets},
                'colors': {bucket.key: bucket.doc_count for bucket in response.aggregations.colors.buckets},
                'storage': {bucket.key: bucket.doc_count for bucket in response.aggregations.storage.buckets},
                'cities': {bucket.key: bucket.doc_count for bucket in response.aggregations.cities.buckets},
                'price_ranges': {bucket.key: bucket.doc_count for bucket in response.aggregations.price_ranges.buckets}
            }
            
        except Exception as e:
            logger.error(f"Error in Elasticsearch facets: {e}")
            return {} 