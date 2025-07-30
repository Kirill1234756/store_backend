#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from elasticsearch import Elasticsearch
from products.models import Product
import json

def index_data():
    """Индексация данных в Elasticsearch"""
    try:
        # Подключаемся к Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])
        
        # Проверяем подключение
        if not es.ping():
            print("❌ Не удалось подключиться к Elasticsearch")
            return False
        
        print("✅ Подключение к Elasticsearch успешно")
        
        # Получаем все активные продукты
        products = Product.objects.filter(is_active=True).select_related('category', 'seller').prefetch_related('product_images')
        
        print(f"📦 Найдено {products.count()} продуктов для индексации")
        
        # Индексируем продукты
        for i, product in enumerate(products, 1):
            # Подготавливаем данные
            doc = {
                'title': product.title,
                'description': product.description,
                'phone_model': product.phone_model,
                'price': float(product.price),
                'condition': product.condition,
                'is_active': product.is_active,
                'is_top': product.is_top,
                'color': product.color,
                'storage': product.storage,
                'screen_size': float(product.screen_size) if product.screen_size else None,
                'body_condition': product.body_condition,
                'screen_condition': product.screen_condition,
                'battery_health': product.battery_health,
                'turbo': product.turbo,
                'city': product.city,
                'package_contents': product.package_contents,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
                'category_name': product.category.name if product.category else '',
                'seller_username': product.seller.username if product.seller else '',
                'rating': float(product.rating) if product.rating else 0.0,
                'main_image_url': str(product.main_image.url) if product.main_image else '',
                'image_count': product.product_images.count(),
                'display': product.display,
                'imei': product.imei,
                'sim': product.sim,
                'face': product.face,
                'market': product.market
            }
            
            # Удаляем None значения
            doc = {k: v for k, v in doc.items() if v is not None}
            
            # Индексируем документ
            es.index(index='products', id=product.id, body=doc)
            
            if i % 100 == 0:
                print(f"📝 Проиндексировано {i} продуктов...")
        
        # Обновляем индекс
        es.indices.refresh(index='products')
        
        print(f"✅ Успешно проиндексировано {products.count()} продуктов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка индексации: {e}")
        return False

if __name__ == "__main__":
    success = index_data()
    sys.exit(0 if success else 1) 