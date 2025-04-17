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

    # Основная информация
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Название может содержать только буквы, цифры и специальные символы',
                code='invalid_title'
            )
        ],
        db_index=True
    )
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
        max_length=50,
        choices=CONDITION_CHOICES,
        verbose_name='Состояние'
    )

    # Характеристики устройства
    phone_model = models.CharField(
        max_length=100,
        verbose_name='Модель телефона',
        default='Не указана',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Модель телефона может содержать только буквы, цифры и специальные символы',
                code='invalid_phone_model'
            )
        ]
    )
    color = models.CharField(
        max_length=50,
        choices=COLOR_CHOICES,
        default='black',
        verbose_name='Цвет'
    )
    storage = models.CharField(
        max_length=50,
        verbose_name='Память',
        default='Не указана',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Память может содержать только буквы, цифры и специальные символы',
                code='invalid_storage'
            )
        ]
    )
    screen_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name='Диагональ экрана (дюймы)',
        default=Decimal('6.1'),
        validators=[
            MinValueValidator(
                Decimal('1.0'), message='Диагональ экрана должна быть больше 1 дюйма'),
            MaxValueValidator(
                Decimal('20.0'), message='Диагональ экрана должна быть меньше 20 дюймов')
        ]
    )
    screen_condition = models.CharField(
        max_length=50,
        verbose_name='Состояние экрана',
        blank=True,
        default='Хорошее',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Состояние экрана может содержать только буквы, цифры и специальные символы',
                code='invalid_screen_condition'
            )
        ]
    )
    body_condition = models.CharField(
        max_length=50,
        verbose_name='Состояние корпуса',
        blank=True,
        default='Хорошее',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Состояние корпуса может содержать только буквы, цифры и специальные символы',
                code='invalid_body_condition'
            )
        ]
    )
    battery_health = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Здоровье аккумулятора (%)',
        default=80
    )
    includes = models.TextField(
        verbose_name='Комплектация',
        blank=True,
        default='Телефон, зарядное устройство',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Комплектация может содержать только буквы, цифры и специальные символы',
                code='invalid_includes'
            )
        ]
    )

    # Контактная информация
    seller_id = models.IntegerField(
        verbose_name='ID продавца',
        default=1
    )
    seller_phone = models.CharField(
        max_length=20,
        verbose_name='Телефон продавца',
        default='',
        validators=[
            RegexValidator(
                regex=r'^[0-9+\s\-()]+$',
                message='Телефон может содержать только цифры, пробелы, дефисы и скобки',
                code='invalid_phone'
            )
        ]
    )
    seller_address = models.TextField(
        verbose_name='Адрес продавца',
        blank=True,
        default='Не указан',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()]+$',
                message='Адрес может содержать только буквы, цифры и специальные символы',
                code='invalid_address'
            )
        ]
    )

    # Даты
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Изображения
    main_image = CompressedImageField(
        upload_to='products/',
        verbose_name='Главное изображение',
        blank=True,
        null=True
    )
    image_2 = CompressedImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Доп. изображение 1'
    )
    image_3 = CompressedImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Доп. изображение 2'
    )
    image_4 = CompressedImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Доп. изображение 3'
    )
    image_5 = CompressedImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Доп. изображение 4'
    )

    # Рейтинг
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name='Рейтинг',
        default=Decimal('0.0'),
        validators=[
            MinValueValidator(
                Decimal('0.0'), message='Рейтинг не может быть отрицательным'),
            MaxValueValidator(
                Decimal('5.0'), message='Рейтинг не может быть больше 5')
        ]
    )

    def __str__(self):
        return f"{self.title}\t{self.price} ₽\t{self.storage}"

    def clean(self):
        """Custom validation for the model"""
        # Check for potential XSS in text fields
        text_fields = ['title', 'description', 'phone_model', 'storage', 'screen_condition',
                       'body_condition', 'includes', 'seller_address']

        for field in text_fields:
            value = getattr(self, field)
            if value and re.search(r'<script|javascript:|vbscript:|expression\(|onload=|onerror=', value, re.IGNORECASE):
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    {field: 'Поле содержит потенциально опасный код'})

        # Don't set default image if not provided
        # Let the field handle null values

    def save(self, *args, **kwargs):
        """Override save to run clean method"""
        self.clean()
        super().save(*args, **kwargs)
        # Clear cache on save
        cache.delete_pattern('product:*')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Clear cache on delete
        cache.delete_pattern('product:*')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            Index(fields=['-created_at'], name='recent_idx'),
            Index(fields=['price']),
            Index(fields=['created_at']),
            Index(fields=['condition']),
            Index(fields=['storage']),
            Index(fields=['phone_model']),
            Index(fields=['rating']),
            Index(fields=['title', 'price']),
            Index(fields=['created_at', 'price']),
        ]
        ordering = ['-created_at']


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)

    class Meta:
        indexes = [
            Index(fields=['name', 'slug']),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete_pattern('category:*')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete_pattern('category:*')
