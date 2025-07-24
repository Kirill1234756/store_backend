from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal
import re
from django.core.cache import cache
from django.db.models import Index
from django.core.files.storage import FileSystemStorage
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .image_utils import save_image, delete_image
from django.contrib.auth import get_user_model

User = get_user_model()


class CompressedImageField(models.ImageField):
    def pre_save(self, model_instance, add):
        file = super().pre_save(model_instance, add)
        if file and not file._committed:
            # Open image
            image = Image.open(file)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            # Resize if too large
            max_size = (1200, 1200)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as WebP
            output = BytesIO()
            image.save(output, format='WEBP', quality=85, optimize=True)
            output.seek(0)
            
            # Save the compressed image
            file.save(
                os.path.splitext(file.name)[0] + '.webp',
                ContentFile(output.read()),
                save=False
            )
        return file


class Product(models.Model):
    CONDITION_CHOICES = [
        ('A', 'Как новый'),
        ('B', 'Хорошее'),
        ('C', 'Удовлетворительное')
    ]

    BODY_CONDITION_CHOICES = [
        ('A', 'Идеальное'),
        ('B', 'Хорошее'),
        ('C', 'Удовлетворительное'),
        ('D', 'Плохое')
    ]

    SCREEN_CONDITION_CHOICES = [
        ('A', 'Идеальное'),
        ('B', 'Хорошее'),
        ('C', 'Удовлетворительное'),
        ('D', 'Плохое')
    ]

    COLOR_CHOICES = [
        ('black', 'Чёрный'),
        ('white', 'Белый'),
        ('gold', 'Золотой'),
        ('silver', 'Серебристый'),
        ('blue', 'Синий'),
        ('red', 'Красный'),
        ('green', 'Зелёный'),
        ('other', 'Другой')
    ]

    STORAGE_CHOICES = [
        ('64GB', '64GB'),
        ('128GB', '128GB'),
        ('256GB', '256GB'),
        ('512GB', '512GB'),
        ('1TB', '1TB')
    ]

    PACKAGE_CONTENTS_CHOICES = [
        ('phone', 'Телефон'),
        ('charger', 'Зарядное устройство'),
        ('cable', 'Кабель'),
        ('documents', 'Документы'),
        ('case', 'Чехол'),
        ('screen_protector', 'Защитное стекло'),
        ('box', 'Коробка'),
        ('earphones', 'Наушники'),
        ('sim_tool', 'Скрепка для SIM'),
    ]

    # Основная информация
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-_.,!?()]+$',
                message='Название может содержать только буквы, цифры и специальные символы',
                code='invalid_title'
            )
        ],
        db_index=True
    )
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(
        verbose_name='Описание',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()<>]+$',
                message='Описание может содержать только буквы, цифры и специальные символы',
                code='invalid_description'
            )
        ]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена',
        validators=[MinValueValidator(
            Decimal('0.01'), message='Цена должна быть больше нуля')],
        db_index=True
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name='Состояние',
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    phone_number = models.CharField(
        max_length=20,
        verbose_name='Номер телефона',
        validators=[
            RegexValidator(
                regex=r'^(\+7|8)?\s?\(?\d{3}\)?\s?\d{3}[-]?\d{2}[-]?\d{2}$',
                message='Введите номер телефона в формате +7 (999) 999-99-99 или 8 (999) 999-99-99',
                code='invalid_phone_number'
            )
        ],
        help_text='Формат: +7 (999) 999-99-99 или 8 (999) 999-99-99'
    )
    is_top = models.BooleanField(default=False, db_index=True, verbose_name='В топе')
    city = models.CharField(
        max_length=100,
        verbose_name='Город',
        blank=True,
        null=True,
        db_index=True
    )

    # Связи с другими моделями
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        verbose_name='Категория',
        related_name='products',
        null=True,
        blank=True,
        db_index=True
    )
    seller = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name='Продавец',
        related_name='products',
        null=True,
        blank=True,
        db_index=True
    )

    # Характеристики устройства
    phone_model = models.CharField(
        max_length=100,
        verbose_name='Модель телефона',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Модель телефона может содержать только буквы, цифры и специальные символы',
                code='invalid_phone_model'
            )
        ]
    )
    display = models.CharField(
        max_length=10,
        verbose_name='Размер дисплея',
        default='6.1"',
        help_text='Размер дисплея в дюймах'
    )
    color = models.CharField(
        max_length=50,
        choices=COLOR_CHOICES,
        verbose_name='Цвет'
    )
    storage = models.CharField(
        max_length=50,
        choices=STORAGE_CHOICES,
        verbose_name='Память'
    )
    screen_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name='Размер экрана (дюймы)',
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('10.0'))],
        null=True,
        blank=True
    )
    body_condition = models.CharField(
        max_length=20,
        choices=BODY_CONDITION_CHOICES,
        verbose_name='Состояние корпуса',
        default='B'
    )
    screen_condition = models.CharField(
        max_length=20,
        choices=SCREEN_CONDITION_CHOICES,
        verbose_name='Состояние экрана',
        default='B'
    )
    battery_health = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Здоровье аккумулятора (%)',
        default=80
    )
    turbo = models.BooleanField(
        default=False,
        verbose_name='Наличие турбо'
    )
    package_contents = models.JSONField(
        verbose_name='Комплектация',
        default=list,
        help_text='Список комплектующих'
    )
    imei = models.CharField(max_length=32, blank=True, null=True)
    sim = models.PositiveSmallIntegerField(default=1)
    face = models.BooleanField(default=False)
    market = models.CharField(max_length=100, blank=True, null=True)
    faults = models.JSONField(default=list, blank=True)

    # Даты
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Изображения
    main_image = models.ImageField(upload_to='products/main/', blank=True, null=True)
    product_images = models.ManyToManyField('MediaImage', blank=True, related_name='products')

    # Рейтинг
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        db_index=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_title = self.title if self.id else None

    def __str__(self):
        return self.title

    def format_phone_number(self, phone):
        if not phone:
            return phone
            
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # If number starts with 8, replace with 7
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        
        # If number doesn't start with 7, add it
        if not digits.startswith('7'):
            digits = '7' + digits
        
        # Format the number
        if len(digits) == 11:  # +7 + 10 digits
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
        return phone

    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError({'price': 'Цена не может быть отрицательной'})
        if self.battery_health is not None and (self.battery_health < 0 or self.battery_health > 100):
            raise ValidationError({'battery_health': 'Здоровье аккумулятора должно быть от 0 до 100%'})
        
        # Format phone number before validation
        if self.phone_number:
            formatted_number = self.format_phone_number(self.phone_number)
            if formatted_number != self.phone_number:
                self.phone_number = formatted_number

    def save(self, *args, **kwargs):
        # Format phone number before saving
        if self.phone_number:
            self.phone_number = self.format_phone_number(self.phone_number)
        
        # Ensure package_contents is a list
        if not isinstance(self.package_contents, list):
            self.package_contents = []
            
        # Generate slug if not exists
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.phone_model}-{self.storage}")
            self.slug = base_slug
            # If slug exists, append timestamp
            if Product.objects.filter(slug=self.slug).exists():
                from django.utils import timezone
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                self.slug = f"{base_slug}-{timestamp}"
            
        super().save(*args, **kwargs)
        self._original_title = self.title
        cache.delete_pattern('product_*')

    def delete(self, *args, **kwargs):
        # Delete main image
        if self.main_image:
            delete_image(self.main_image.path)
        
        # Delete additional images
        for image in self.product_images.all():
            delete_image(image.image.path)
        
        super().delete(*args, **kwargs)
        cache.delete_pattern('product_*')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            Index(fields=['-created_at'], name='product_recent_idx'),
            Index(fields=['price'], name='product_price_idx'),
            Index(fields=['created_at'], name='product_created_at_idx'),
            Index(fields=['condition'], name='product_condition_idx'),
            Index(fields=['storage'], name='product_storage_idx'),
            Index(fields=['phone_model'], name='product_phone_model_idx'),
            Index(fields=['rating'], name='product_rating_idx'),
            Index(fields=['title', 'price'], name='product_title_price_idx'),
            Index(fields=['created_at', 'price'], name='product_created_price_idx'),
            Index(fields=['title', 'description'], name='product_search_idx'),
            Index(fields=['battery_health'], name='product_battery_health_idx'),
            Index(fields=['title', 'price']),
            Index(fields=['category', 'condition']),
            Index(fields=['created_at', 'is_active']),
        ]
        ordering = ['-is_top', '-created_at']

    @cached_property
    def cached_rating(self):
        cache_key = f'product_rating_{self.id}'
        rating = cache.get(cache_key)
        if rating is None:
            rating = self.calculate_rating()
            cache.set(cache_key, rating, 60 * 60)  # Cache for 1 hour
        return rating

    def calculate_rating(self):
        avg_rating = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating else 0.0

    def add_image(self, image_file):
        """Add an additional image to the product"""
        if not hasattr(self, '_images_to_save'):
            self._images_to_save = []
        self._images_to_save.append(image_file)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        indexes = [
            Index(fields=['name', 'slug']),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        cache.delete_pattern('category:*')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cache.delete_pattern('category:*')
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'Review by {self.user.username} for {self.product.title}'

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'Rating must be between 1 and 5'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Update product rating
        self.product.calculate_rating()
        # Clear cache
        cache.delete_pattern('product_*')
