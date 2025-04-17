from django.test import TestCase
from products.models import Product, Category
from products.serializers import ProductSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Smartphones',
            slug='smartphones'
        )
        self.product_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 1000,
            'phone_model': 'iPhone 13',
            'storage': 128,
            'color': 'Black',
            'condition': 'A',
            'category': self.category,
            'seller': self.user
        }
        self.product = Product.objects.create(**self.product_data)
        self.serializer = ProductSerializer(instance=self.product)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), {
            'id', 'title', 'description', 'price',
            'main_image', 'phone_model', 'storage',
            'color', 'condition', 'category', 'seller',
            'created_at', 'updated_at'
        })

    def test_title_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['title'], self.product_data['title'])

    def test_price_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['price'], str(self.product_data['price']))

    def test_invalid_condition(self):
        invalid_product_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 1000,
            'condition': 'X',  # Invalid condition
            'category': self.category.id
        }
        serializer = ProductSerializer(data=invalid_product_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('condition', serializer.errors)

    def test_negative_price(self):
        invalid_product_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': -100,  # Negative price
            'category': self.category.id
        }
        serializer = ProductSerializer(data=invalid_product_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors) 