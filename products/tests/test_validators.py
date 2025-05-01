from django.test import TestCase
from django.core.exceptions import ValidationError
from products.validators import (
    sanitize_input,
    validate_price,
    validate_name,
    validate_description,
    validate_image
)
from django.core.files.uploadedfile import SimpleUploadedFile


class ValidatorsTest(TestCase):
    def test_sanitize_input(self):
        # Test HTML sanitization
        self.assertEqual(sanitize_input('<script>alert("xss")</script>'), '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
        
        # Test SQL injection sanitization
        self.assertEqual(sanitize_input('SELECT * FROM users'), '')
        self.assertEqual(sanitize_input('DROP TABLE users'), '')
        
        # Test normal input
        self.assertEqual(sanitize_input('normal text'), 'normal text')
        self.assertEqual(sanitize_input(123), 123)

    def test_validate_price(self):
        # Test valid prices
        validate_price(0.01)
        validate_price(1000)
        validate_price(999999)
        
        # Test invalid prices
        with self.assertRaises(ValidationError):
            validate_price(-1)
        with self.assertRaises(ValidationError):
            validate_price(1000001)
        with self.assertRaises(ValidationError):
            validate_price('not a number')

    def test_validate_name(self):
        # Test valid names
        validate_name('iPhone 13')
        validate_name('Samsung Galaxy S21')
        validate_name('Test-Product_123')
        
        # Test invalid names
        with self.assertRaises(ValidationError):
            validate_name('a')  # Too short
        with self.assertRaises(ValidationError):
            validate_name('a' * 101)  # Too long
        with self.assertRaises(ValidationError):
            validate_name('Product@#$')  # Invalid characters

    def test_validate_description(self):
        # Test valid descriptions
        validate_description('This is a valid description')
        validate_description('a' * 10)  # Minimum length
        validate_description('a' * 1000)  # Maximum length
        
        # Test invalid descriptions
        with self.assertRaises(ValidationError):
            validate_description('short')  # Too short
        with self.assertRaises(ValidationError):
            validate_description('a' * 1001)  # Too long

    def test_validate_image(self):
        # Test valid image
        valid_image = SimpleUploadedFile(
            name='test.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        validate_image(valid_image)
        
        # Test invalid image types
        invalid_type = SimpleUploadedFile(
            name='test.txt',
            content=b'',
            content_type='text/plain'
        )
        with self.assertRaises(ValidationError):
            validate_image(invalid_type)
        
        # Test invalid file extension
        invalid_extension = SimpleUploadedFile(
            name='test.pdf',
            content=b'',
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            validate_image(invalid_extension)
        
        # Test too large image
        large_image = SimpleUploadedFile(
            name='test.jpg',
            content=b'0' * (5 * 1024 * 1024 + 1),  # 5MB + 1 byte
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            validate_image(large_image) 