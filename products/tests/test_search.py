from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchTest(TestCase):
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
        
        # Create test products with different titles and descriptions
        self.products = [
            Product.objects.create(
                title='iPhone 13 Pro Max',
                description='Apple iPhone 13 Pro Max 256GB Sierra Blue',
                price=1000,
                condition='A',
                category=self.category,
                phone_model='iPhone 13 Pro Max',
                color='blue',
                storage='256GB',
                screen_size=6.7,
                screen_condition='Good',
                body_condition='Good',
                battery_health=90,
                includes='Phone, charger',
                seller=self.user
            ),
            Product.objects.create(
                title='Samsung Galaxy S21 Ultra',
                description='Samsung Galaxy S21 Ultra 5G 256GB Phantom Black',
                price=900,
                condition='A',
                category=self.category,
                phone_model='Samsung Galaxy S21 Ultra',
                color='black',
                storage='256GB',
                screen_size=6.8,
                screen_condition='Good',
                body_condition='Good',
                battery_health=90,
                includes='Phone, charger',
                seller=self.user
            ),
            Product.objects.create(
                title='Google Pixel 6 Pro',
                description='Google Pixel 6 Pro 128GB Stormy Black',
                price=800,
                condition='A',
                category=self.category,
                phone_model='Google Pixel 6 Pro',
                color='black',
                storage='128GB',
                screen_size=6.7,
                screen_condition='Good',
                body_condition='Good',
                battery_health=90,
                includes='Phone, charger',
                seller=self.user
            )
        ]

    def test_search_by_title(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iPhone'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 13 Pro Max')

    def test_search_by_description(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Sierra Blue'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 13 Pro Max')

    def test_search_by_phone_model(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Pixel'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Google Pixel 6 Pro')

    def test_search_case_insensitive(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iphone'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 13 Pro Max')

    def test_search_partial_match(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Pro'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        titles = [item['title'] for item in response.data['results']]
        self.assertIn('iPhone 13 Pro Max', titles)
        self.assertIn('Google Pixel 6 Pro', titles)

    def test_search_multiple_words(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Samsung Galaxy'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Samsung Galaxy S21 Ultra')

    def test_search_no_results(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Xiaomi'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_search_with_special_characters(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iPhone 13 Pro Max!'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 13 Pro Max')

    def test_search_with_numbers(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': '256GB'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        titles = [item['title'] for item in response.data['results']]
        self.assertIn('iPhone 13 Pro Max', titles)
        self.assertIn('Samsung Galaxy S21 Ultra', titles)

    def test_search_with_filters(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'search': 'Pro',
            'color': 'black'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Google Pixel 6 Pro')

    def test_search_with_pagination(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'search': 'Pro',
            'page': 1,
            'limit': 1
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['totalPages'], 2) 