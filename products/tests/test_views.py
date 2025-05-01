from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from products.models import Product, Category, Review
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()

class ProductViewTest(APITestCase):
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

    def test_get_products_list(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_product_detail(self):
        url = reverse('product-detail', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Product')

    def test_create_product(self):
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_update_product(self):
        url = reverse('product-detail', args=[self.product.id])
        data = {
            'title': 'Updated Product',
            'price': 1500
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Updated Product')
        self.assertEqual(self.product.price, 1500)

    def test_delete_product(self):
        url = reverse('product-detail', args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_filter_products(self):
        url = reverse('product-list')
        response = self.client.get(url, {'condition': 'A', 'min_price': 500})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(url, {'condition': 'B', 'min_price': 2000})
        self.assertEqual(len(response.data['results']), 0)

    def test_search_products(self):
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iPhone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(url, {'search': 'Samsung'})
        self.assertEqual(len(response.data['results']), 0)

    def test_product_image_upload(self):
        url = reverse('product-detail', args=[self.product.id])
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        data = {'main_image': image}
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_product_image(self):
        url = reverse('product-detail', args=[self.product.id])
        image = SimpleUploadedFile(
            name='test.txt',
            content=b'',
            content_type='text/plain'
        )
        data = {'main_image': image}
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_rating(self):
        # Create a review
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product'
        )
        url = reverse('product-detail', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5.0)

    def test_product_cache(self):
        url = reverse('product-detail', args=[self.product.id])
        # First request should cache the response
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request should use cached response
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # List is public

        url = reverse('product-detail', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Detail is public

        # Try to create a product
        data = {
            'title': 'New Product',
            'description': 'New description',
            'price': 2000,
            'condition': 'A',
            'category': self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 