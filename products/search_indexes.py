from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from .models import Product, Category

# Создаем индекс для продуктов
product_index = Index('products')
product_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@product_index.document
class ProductDocument(Document):
    # Основные поля
    title = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    description = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
        }
    )
    phone_model = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    
    # Цена и состояние
    price = fields.FloatField()
    condition = fields.KeywordField()
    is_active = fields.BooleanField()
    is_top = fields.BooleanField()
    
    # Характеристики
    color = fields.KeywordField()
    storage = fields.KeywordField()
    screen_size = fields.FloatField()
    body_condition = fields.KeywordField()
    screen_condition = fields.KeywordField()
    battery_health = fields.IntegerField()
    turbo = fields.BooleanField()
    
    # География
    city = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
        }
    )
    
    # Комплектация (как массив)
    package_contents = fields.ListField(fields.KeywordField())
    
    # Даты
    created_at = fields.DateField()
    updated_at = fields.DateField()
    
    # Связанные поля
    category_name = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
        }
    )
    seller_username = fields.KeywordField()
    
    # Рейтинг
    rating = fields.FloatField()
    
    # Изображения
    main_image_url = fields.KeywordField()
    image_count = fields.IntegerField()
    
    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'russian': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'russian_stop', 'russian_stemmer']
                    }
                },
                'filter': {
                    'russian_stop': {
                        'type': 'stop',
                        'stopwords': '_russian_'
                    },
                    'russian_stemmer': {
                        'type': 'stemmer',
                        'language': 'russian'
                    }
                }
            }
        }
    
    class Django:
        model = Product
        fields = []
        
        # Исключаем поля, которые не нужно индексировать
        ignore_signals = False
        auto_refresh = True
    
    def get_queryset(self):
        """Оптимизированный queryset с prefetch_related"""
        return super().get_queryset().select_related(
            'category', 'seller'
        ).prefetch_related(
            'product_images'
        )
    
    def get_indexing_queryset(self):
        """Queryset для индексации"""
        return self.get_queryset().filter(is_active=True)
    
    def prepare_category_name(self, instance):
        """Подготовка названия категории"""
        return instance.category.name if instance.category else ''
    
    def prepare_seller_username(self, instance):
        """Подготовка имени продавца"""
        return instance.seller.username if instance.seller else ''
    
    def prepare_main_image_url(self, instance):
        """Подготовка URL главного изображения"""
        if instance.main_image:
            return instance.main_image.url
        return ''
    
    def prepare_image_count(self, instance):
        """Подготовка количества изображений"""
        return instance.product_images.count()
    
    def prepare_package_contents(self, instance):
        """Подготовка комплектации"""
        return instance.package_contents if instance.package_contents else []
    
    def prepare_rating(self, instance):
        """Подготовка рейтинга"""
        return float(instance.cached_rating) if instance.cached_rating else 0.0 