from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from products.models import Product, Category
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

class RateLimitTest(TestCase):
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
        self.product = Product.objects.create(
            title='Test Product',
            description='Test description',
            price=1000,
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

    def test_product_list_rate_limit(self):
        url = reverse('product-list')
        # Make 100 requests (within the limit)
        for _ in range(100):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        
        # 101st request should be blocked
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)  # Too Many Requests

    def test_product_detail_rate_limit(self):
        url = reverse('product-detail', args=[self.product.id])
        # Make 50 requests (within the limit)
        for _ in range(50):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        
        # 51st request should be blocked
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_product_create_rate_limit(self):
        url = reverse('product-list')
        data = {
            'title': 'New Product',
            'description': 'New description',
            'price': 2000,
            'condition': 'A',
            'category': self.category.id,
            'phone_model': 'iPhone 14',
            'color': 'white',
            'storage': '256GB',
            'screen_size': 6.1,
            'screen_condition': 'Good',
            'body_condition': 'Good',
            'battery_health': 90,
            'includes': 'Phone, charger'
        }
        
        # Make 10 requests (within the limit)
        for _ in range(10):
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, 201)
        
        # 11th request should be blocked
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 429)

    def test_product_update_rate_limit(self):
        url = reverse('product-detail', args=[self.product.id])
        data = {'title': 'Updated Product'}
        
        # Make 20 requests (within the limit)
        for _ in range(20):
            response = self.client.patch(url, data, format='json')
            self.assertEqual(response.status_code, 200)
        
        # 21st request should be blocked
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 429)

    def test_product_delete_rate_limit(self):
        url = reverse('product-detail', args=[self.product.id])
        
        # Make 5 requests (within the limit)
        for _ in range(5):
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)
            # Recreate the product for next test
            self.product = Product.objects.create(
                title='Test Product',
                description='Test description',
                price=1000,
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
        
        # 6th request should be blocked
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_reset(self):
        url = reverse('product-list')
        
        # Make 100 requests to hit the limit
        for _ in range(100):
            self.client.get(url)
        
        # Clear the rate limit cache
        cache.clear()
        
        # Should be able to make requests again
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_different_ip_rate_limits(self):
        url = reverse('product-list')
        
        # First IP hits the limit
        for _ in range(100):
            self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)
        
        # Second IP should have its own limit
        self.client = APIClient(REMOTE_ADDR='127.0.0.2')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_with_different_users(self):
        url = reverse('product-list')
        
        # First user hits the limit
        for _ in range(100):
            self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)
        
        # Second user should have its own limit
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 