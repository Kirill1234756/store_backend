from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class PaginationTest(TestCase):
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
        
        # Create 25 test products
        for i in range(25):
            Product.objects.create(
                title=f'Test Product {i}',
                description=f'Test description {i}',
                price=1000 + i,
                condition='A',
                category=self.category,
                phone_model='iPhone 13',
                color='black',
                storage='128GB',
                screen_size=6.1,
                screen_condition='Good',
                body_condition='Good',
                battery_health=90,
                includes='Phone, charger',
                seller=self.user
            )

    def test_default_pagination(self):
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertEqual(response.data['total'], 25)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['totalPages'], 3)

    def test_custom_page_size(self):
        url = reverse('product-list')
        response = self.client.get(url, {'limit': 20})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['total'], 25)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['totalPages'], 2)

    def test_page_navigation(self):
        url = reverse('product-list')
        
        # First page
        response1 = self.client.get(url, {'page': 1})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.data['results']), 10)
        self.assertEqual(response1.data['page'], 1)
        
        # Second page
        response2 = self.client.get(url, {'page': 2})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.data['results']), 10)
        self.assertEqual(response2.data['page'], 2)
        
        # Third page
        response3 = self.client.get(url, {'page': 3})
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(len(response3.data['results']), 5)
        self.assertEqual(response3.data['page'], 3)

    def test_invalid_page_number(self):
        url = reverse('product-list')
        response = self.client.get(url, {'page': 0})
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get(url, {'page': 4})
        self.assertEqual(response.status_code, 404)

    def test_max_page_size(self):
        url = reverse('product-list')
        response = self.client.get(url, {'limit': 200})  # Try to exceed max page size
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 100)  # Should be capped at max_page_size

    def test_pagination_with_filtering(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'condition': 'A',
            'page': 1,
            'limit': 10
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['total'], 25)

    def test_pagination_with_ordering(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'ordering': 'price',
            'page': 1,
            'limit': 10
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['results'][0]['price'], '1000.00')
        self.assertEqual(response.data['results'][-1]['price'], '1009.00')

    def test_pagination_with_search(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'search': 'Test Product 1',
            'page': 1,
            'limit': 10
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all('Test Product 1' in item['title'] for item in response.data['results']))

    def test_pagination_metadata(self):
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertIn('results', response.data)
        self.assertIn('total', response.data)
        self.assertIn('page', response.data)
        self.assertIn('limit', response.data)
        self.assertIn('totalPages', response.data) 