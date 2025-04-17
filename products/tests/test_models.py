from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from products.models import Product, Category

class ProductModelTest(TestCase):
    def setUp(self):
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
            category=self.category
        )

    def test_product_creation(self):
        self.assertEqual(self.product.title, 'Test Product')
        self.assertEqual(self.product.price, 1000)
        self.assertEqual(self.product.phone_model, 'iPhone 13')
        self.assertEqual(self.product.storage, 128)
        self.assertEqual(self.product.color, 'Black')
        self.assertEqual(self.product.condition, 'A')
        self.assertEqual(self.product.category, self.category)

    def test_product_str_representation(self):
        self.assertEqual(str(self.product), 'Test Product')

    def test_product_price_validation(self):
        with self.assertRaises(ValueError):
            Product.objects.create(
                title='Invalid Price',
                description='Test',
                price=-100,
                category=self.category
            )

    def test_product_condition_choices(self):
        with self.assertRaises(ValueError):
            Product.objects.create(
                title='Invalid Condition',
                description='Test',
                price=1000,
                condition='X',
                category=self.category
            )

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Smartphones',
            slug='smartphones'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Smartphones')
        self.assertEqual(self.category.slug, 'smartphones')

    def test_category_str_representation(self):
        self.assertEqual(str(self.category), 'Smartphones')

    def test_category_slug_auto_generation(self):
        category = Category.objects.create(name='Test Category')
        self.assertEqual(category.slug, 'test-category') 