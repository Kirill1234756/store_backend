from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class FilteringTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test products with different conditions
        self.products = []
        conditions = ['A', 'B', 'C']
        colors = ['black', 'white', 'gold']
        storages = ['64GB', '128GB', '256GB']
        phone_models = ['iPhone 13', 'iPhone 14', 'Samsung S21']
        
        for i in range(9):
            product = Product.objects.create(
                title=f'Test Product {i}',
                description=f'Test description {i}',
                price=1000 + (i * 100),
                condition=conditions[i % 3],
                category=self.category,
                phone_model=phone_models[i % 3],
                color=colors[i % 3],
                storage=storages[i % 3],
                screen_size=6.1,
                screen_condition='Good',
                body_condition='Good',
                battery_health=90,
                includes='Phone, charger',
                seller=self.user
            )
            self.products.append(product)

    def test_condition_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {'condition': 'A'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertTrue(all(item['condition'] == 'A' for item in response.data['results']))

    def test_color_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {'color': 'black'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertTrue(all(item['color'] == 'black' for item in response.data['results']))

    def test_storage_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {'storage': '128GB'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertTrue(all(item['storage'] == '128GB' for item in response.data['results']))

    def test_phone_model_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {'phone_model': 'iPhone 13'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertTrue(all(item['phone_model'] == 'iPhone 13' for item in response.data['results']))

    def test_price_range_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'price_min': 1000,
            'price_max': 1200
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertTrue(all(1000 <= float(item['price']) <= 1200 for item in response.data['results']))

    def test_multiple_filters(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'condition': 'A',
            'color': 'black',
            'storage': '128GB'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        product = response.data['results'][0]
        self.assertEqual(product['condition'], 'A')
        self.assertEqual(product['color'], 'black')
        self.assertEqual(product['storage'], '128GB')

    def test_search_filter(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iPhone'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 6)
        self.assertTrue(all('iPhone' in item['phone_model'] for item in response.data['results']))

    def test_ordering_with_filters(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'condition': 'A',
            'ordering': '-price'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        prices = [float(item['price']) for item in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_invalid_filter_values(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'condition': 'X',  # Invalid condition
            'color': 'purple',  # Invalid color
            'storage': '512GB'  # Invalid storage
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_with_pagination(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'condition': 'A',
            'page': 1,
            'limit': 2
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total'], 3)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['totalPages'], 2) 