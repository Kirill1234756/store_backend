import re
import os
import logging
import base64
from rest_framework import serializers
from .models import Product, Review, Category
from .media_models import MediaImage
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class MediaImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = MediaImage
        fields = ['id', 'title', 'image', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image_file:
            return obj.image_file.url
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image_file:
            if request:
                return request.build_absolute_uri(obj.image_file.url)
            return obj.image_file.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    additional_images = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    package_contents = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    category = serializers.CharField(required=False)
    is_top = serializers.BooleanField(read_only=True)
    city = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    imei = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sim = serializers.IntegerField(required=False)
    face = serializers.BooleanField(required=False)
    market = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    faults = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'category', 'category_name',
            'main_image', 'main_image_url', 'additional_images', 'rating', 'reviews_count', 
            'created_at', 'updated_at', 'phone_model', 'color', 'storage', 'condition', 
            'body_condition', 'screen_condition', 'battery_health', 'turbo', 
            'package_contents', 'phone_number', 'display', 'seller', 'seller_name',
            'is_top', 'city', 'images', 'imei', 'sim', 'face', 'market', 'faults'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_rating(self, obj):
        return obj.calculate_rating()

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/products/{obj.id}/image/main/')
            return f'/api/products/{obj.id}/image/main/'
        return None

    def get_additional_images(self, obj):
        return MediaImageSerializer(obj.product_images.all(), many=True, context=self.context).data

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def validate_main_image(self, value):
        if value:
            # Check file size (5MB limit)
            if value.size > 5242880:  # 5MB
                raise serializers.ValidationError("Image size must be less than 5MB")
            
            # Check file extension
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise serializers.ValidationError("Only jpg, jpeg, png, gif and webp files are allowed")
        return value

    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value

    def validate_battery_health(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Battery health must be between 0 and 100")
        return value

    def validate_package_contents(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("package_contents must be a list")
        return value

    def validate(self, data):
        # Required fields for iPhone
        required_fields = ['title', 'price', 'phone_model', 'color', 'storage', 'condition', 
                         'body_condition', 'screen_condition', 'battery_health', 'phone_number']
        
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: f"{field} is required"})

        # Validate price
        price = data.get('price')
        if price is not None:
            try:
                price = float(price)
                if price <= 0:
                    raise serializers.ValidationError({'price': 'Цена должна быть больше нуля'})
            except (ValueError, TypeError):
                raise serializers.ValidationError({'price': 'Некорректная цена'})

        # Validate condition
        if data.get('condition') not in ['A', 'B', 'C']:
            raise serializers.ValidationError({'condition': 'Invalid condition value'})
        
        if data.get('body_condition') not in ['A', 'B', 'C', 'D']:
            raise serializers.ValidationError({'body_condition': 'Invalid body condition value'})
        
        if data.get('screen_condition') not in ['A', 'B', 'C', 'D']:
            raise serializers.ValidationError({'screen_condition': 'Invalid screen condition value'})

        # Validate battery health
        battery_health = data.get('battery_health')
        if battery_health is not None and not 0 <= battery_health <= 100:
            raise serializers.ValidationError({'battery_health': 'Battery health must be between 0 and 100'})

        # Validate package contents
        package_contents = data.get('package_contents', [])
        if not isinstance(package_contents, list):
            raise serializers.ValidationError({'package_contents': 'package_contents must be a list'})

        return data

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        # Создаем продукт без изображений
        product = super().create(validated_data)
        
        # Обрабатываем изображения
        if images:
            # Первое изображение как главное
            product.main_image = images[0]
            product.save()
            
            # Остальные как дополнительные
            for img in images[1:]:
                media = MediaImage.objects.create(
                    title=f"Additional image for {product.title}",
                    image_file=img
                )
                product.product_images.add(media)
        
        return product

    def update(self, instance, validated_data):
        images = validated_data.pop('images', [])
        # Обновляем основные данные
        instance = super().update(instance, validated_data)
        
        # Обрабатываем новые изображения
        if images:
            # Обновляем главное изображение
            instance.main_image = images[0]
            instance.save()
            
            # Добавляем новые дополнительные изображения
            for img in images[1:]:
                media = MediaImage.objects.create(
                    title=f"Additional image for {instance.title}",
                    image_file=img
                )
                instance.product_images.add(media)
        
        return instance

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters")
        return value

    def validate_image(self, value):
        validate_image(value)
        return value

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    product = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'product', 'created_at']
