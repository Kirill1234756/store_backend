from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from products.models import Product, Category, Review
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
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

    def test_product_creation(self):
        self.assertEqual(self.product.title, 'Test Product')
        self.assertEqual(self.product.price, Decimal('1000'))
        self.assertEqual(self.product.condition, 'A')
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.seller, self.user)

    def test_product_slug_creation(self):
        self.assertEqual(self.product.slug, 'test-product')

    def test_product_str_representation(self):
        self.assertEqual(str(self.product), 'Test Product')

    def test_product_rating_calculation(self):
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product'
        )
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            comment='Good product'
        )
        self.assertEqual(self.product.calculate_rating(), 4.5)

    def test_product_clean_method(self):
        # Test with valid data
        self.product.clean()

        # Test with invalid battery health
        self.product.battery_health = 101
        with self.assertRaises(Exception):
            self.product.clean()

    def test_product_save_method(self):
        # Test slug generation
        self.product.title = 'New Test Product'
        self.product.save()
        self.assertEqual(self.product.slug, 'new-test-product')

    def test_product_delete_method(self):
        # Create an image for the product
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        self.product.main_image = image
        self.product.save()

        # Delete the product
        self.product.delete()
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')

    def test_category_slug_creation(self):
        category = Category.objects.create(name='New Category')
        self.assertEqual(category.slug, 'new-category')

    def test_category_str_representation(self):
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_delete_method(self):
        self.category.delete()
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
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
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product'
        )

    def test_review_creation(self):
        self.assertEqual(self.review.product, self.product)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, 'Great product')

    def test_review_str_representation(self):
        self.assertEqual(str(self.review), f'Review by {self.user.username} for {self.product.title}')

    def test_review_save_method(self):
        # Test rating validation
        self.review.rating = 6
        with self.assertRaises(Exception):
            self.review.save()

    def test_review_delete_method(self):
        self.review.delete()
        self.assertFalse(Review.objects.filter(id=self.review.id).exists()) 