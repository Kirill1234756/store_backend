from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
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
            name='Test Category',
            slug='test-category'
        )
        self.product_data = {
            'title': 'Test Product',
            'description': 'Test description',
            'price': 1000,
            'condition': 'A',
            'category': self.category.id,
            'phone_model': 'iPhone 13',
            'color': 'black',
            'storage': '128GB',
            'screen_size': 6.1,
            'screen_condition': 'Good',
            'body_condition': 'Good',
            'battery_health': 90,
            'includes': 'Phone, charger'
        }

    def test_valid_product_serialization(self):
        serializer = ProductSerializer(data=self.product_data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save(seller=self.user)
        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.price, 1000)
        self.assertEqual(product.condition, 'A')

    def test_invalid_price(self):
        invalid_data = self.product_data.copy()
        invalid_data['price'] = -100
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_invalid_condition(self):
        invalid_data = self.product_data.copy()
        invalid_data['condition'] = 'X'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('condition', serializer.errors)

    def test_invalid_title(self):
        invalid_data = self.product_data.copy()
        invalid_data['title'] = '<script>alert("xss")</script>'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_image_validation(self):
        # Create a small valid JPEG image
        image_content = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01'
            b'\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06'
            b'\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b'
            b'\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff'
            b'\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!'
            b'21222222222222222222222222222222'
            b'222222222222222222222222\xff\xc0'
            b'\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01'
            b'\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01'
            b'\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01'
            b'\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5'
            b'\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04'
            b'\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06'
            b'\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R'
            b'\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZ'
            b'cdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92'
            b'\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
            b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba'
            b'\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5'
            b'\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8'
            b'\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff'
            b'\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01'
            b'\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05'
            b'\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01'
            b'\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00'
            b'\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2'
            b'\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1'
            b'\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZ'
            b'cdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a'
            b'\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5'
            b'\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
            b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4'
            b'\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8'
            b'\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda'
            b'\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf9\xfe'
            b'\x8a(\xa0\x0f\xff\xd9'
        )
        valid_image = SimpleUploadedFile(
            name='test.jpg',
            content=image_content,
            content_type='image/jpeg'
        )
        data = self.product_data.copy()
        data['main_image'] = valid_image
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_image(self):
        invalid_image = SimpleUploadedFile(
            name='test.txt',
            content=b'',
            content_type='text/plain'
        )
        data = self.product_data.copy()
        data['main_image'] = invalid_image
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('main_image', serializer.errors)

    def test_serializer_to_representation(self):
        product = Product.objects.create(
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
        serializer = ProductSerializer(product)
        data = serializer.data
        self.assertIn('rating', data)
        self.assertIn('reviews_count', data)
        self.assertIn('category_name', data)
        self.assertEqual(data['category_name'], 'Test Category')

    def test_serializer_update(self):
        product = Product.objects.create(
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
        update_data = {
            'title': 'Updated Product',
            'price': 1500
        }
        serializer = ProductSerializer(product, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_product = serializer.save()
        self.assertEqual(updated_product.title, 'Updated Product')
        self.assertEqual(updated_product.price, 1500) 