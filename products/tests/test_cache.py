from django.test import TestCase
from django.core.cache import cache
from products.models import Product, Category, Review
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()

class CacheTest(TestCase):
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

    def test_product_detail_cache(self):
        url = reverse('product-detail', args=[self.product.id])
        
        # First request should cache the response
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use cached response
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.data, response2.data)

    def test_product_list_cache(self):
        url = reverse('product-list')
        
        # First request should cache the response
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use cached response
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.data, response2.data)

    def test_cache_invalidation_on_update(self):
        url = reverse('product-detail', args=[self.product.id])
        
        # First request to cache the response
        self.client.get(url)
        
        # Update the product
        update_url = reverse('product-detail', args=[self.product.id])
        self.client.patch(update_url, {'title': 'Updated Product'})
        
        # New request should get fresh data
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Updated Product')

    def test_cache_invalidation_on_delete(self):
        url = reverse('product-detail', args=[self.product.id])
        
        # First request to cache the response
        self.client.get(url)
        
        # Delete the product
        delete_url = reverse('product-detail', args=[self.product.id])
        self.client.delete(delete_url)
        
        # New request should get 404
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_review_cache(self):
        # Create a review
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product'
        )
        
        url = reverse('product-detail', args=[self.product.id])
        
        # First request should cache the response
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data['rating'], 5.0)
        
        # Second request should use cached response
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data['rating'], 5.0)

    def test_cache_timeout(self):
        url = reverse('product-detail', args=[self.product.id])
        
        # First request to cache the response
        self.client.get(url)
        
        # Simulate cache timeout by clearing the cache
        cache.clear()
        
        # New request should get fresh data
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cache_key_uniqueness(self):
        url1 = reverse('product-detail', args=[self.product.id])
        url2 = reverse('product-detail', args=[self.product.id])
        
        # Both URLs should use the same cache key
        response1 = self.client.get(url1)
        response2 = self.client.get(url2)
        self.assertEqual(response1.data, response2.data)

    def test_cache_with_different_users(self):
        # Create another user
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        url = reverse('product-detail', args=[self.product.id])
        
        # Request from first user
        self.client.force_authenticate(user=self.user)
        response1 = self.client.get(url)
        
        # Request from second user
        self.client.force_authenticate(user=user2)
        response2 = self.client.get(url)
        
        # Both users should get the same response
        self.assertEqual(response1.data, response2.data) 