from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Smartphones',
            slug='smartphones'
        )
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=1000,
            phone_model='iPhone 13',
            storage=128,
            color='Black',
            condition='A',
            category=self.category,
            seller=self.user
        )
        self.client.force_authenticate(user=self.user)

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
            'description': 'New Description',
            'price': 2000,
            'phone_model': 'iPhone 14',
            'storage': 256,
            'color': 'White',
            'condition': 'B',
            'category': self.category.id
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