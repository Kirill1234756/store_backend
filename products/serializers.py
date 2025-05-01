import re
import os
import logging
from rest_framework import serializers
from .models import Product, Review, Category, MediaImage
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class MediaImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    additional_images = MediaImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'category', 'category_name',
            'main_image', 'additional_images', 'rating', 'reviews_count', 'created_at', 'updated_at',
            'phone_model', 'color', 'storage', 'condition', 'body_condition', 'screen_condition',
            'battery_health', 'turbo', 'комплектация'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_rating(self, obj):
        return obj.calculate_rating()

    def get_reviews_count(self, obj):
        return obj.reviews.count()

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

    def validate_комплектация(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("комплектация must be a list")
        return value

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
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
