from rest_framework import serializers
from .models import Product
import re
import os


class ProductSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(
        source='get_condition_display', read_only=True)
    color_display = serializers.CharField(
        source='get_color_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'condition', 'condition_display',
            'phone_model', 'color', 'color_display', 'storage', 'screen_size',
            'screen_condition', 'body_condition', 'battery_health', 'includes',
            'seller_phone', 'seller_address', 'created_at', 'updated_at',
            'main_image', 'image_2', 'image_3', 'image_4', 'image_5', 'seller_id'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'price': {'required': True},
            'condition': {'required': True},
            'phone_model': {'required': False},
            'color': {'required': False},
            'storage': {'required': False},
            'screen_size': {'required': False},
            'screen_condition': {'required': False},
            'body_condition': {'required': False},
            'battery_health': {'required': False},
            'includes': {'required': False},
            'seller_phone': {'required': False},
            'seller_address': {'required': False},
            'main_image': {'required': False, 'allow_null': True},
            'image_2': {'required': False, 'allow_null': True},
            'image_3': {'required': False, 'allow_null': True},
            'image_4': {'required': False, 'allow_null': True},
            'image_5': {'required': False, 'allow_null': True},
        }

    def validate_title(self, value):
        """Validate title field"""
        if len(value) < 3:
            raise serializers.ValidationError(
                "Название должно содержать не менее 3 символов")

        # Check for potential XSS
        if re.search(r'<script|javascript:|vbscript:|expression\(|onload=|onerror=', value, re.IGNORECASE):
            raise serializers.ValidationError(
                "Название содержит потенциально опасный код")

        return value

    def validate_description(self, value):
        """Validate description field"""
        if len(value) < 10:
            raise serializers.ValidationError(
                "Описание должно содержать не менее 10 символов")

        # Check for potential XSS
        if re.search(r'<script|javascript:|vbscript:|expression\(|onload=|onerror=', value, re.IGNORECASE):
            raise serializers.ValidationError(
                "Описание содержит потенциально опасный код")

        return value

    def validate_main_image(self, value):
        """Validate main image field"""
        if value:
            # If it's a string (URL), skip validation
            if isinstance(value, str):
                return value

            # Check file size (5MB limit)
            if value.size > 5242880:  # 5MB
                raise serializers.ValidationError(
                    "Размер изображения не должен превышать 5MB")

            # Check file extension
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                raise serializers.ValidationError(
                    "Файл должен быть изображением (jpg, jpeg, png, gif)")

        return value

    def validate_price(self, value):
        """Validate price field"""
        if value <= 0:
            raise serializers.ValidationError(
                "Цена должна быть положительным числом")

        # Check for reasonable price range
        if value > 1000000:  # 1 million
            raise serializers.ValidationError(
                "Цена слишком высокая")

        return value

    def validate_battery_health(self, value):
        """Validate battery health field"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError(
                "Здоровье батареи должно быть от 0 до 100")
        return value

    def validate_seller_phone(self, value):
        """Validate seller phone field"""
        if value and not re.match(r'^[0-9+\s\-()]+$', value):
            raise serializers.ValidationError(
                "Телефон может содержать только цифры, пробелы, дефисы и скобки")
        return value

    def validate_seller_address(self, value):
        """Validate seller address field"""
        if value and re.search(r'<script|javascript:|vbscript:|expression\(|onload=|onerror=', value, re.IGNORECASE):
            raise serializers.ValidationError(
                "Адрес содержит потенциально опасный код")
        return value

    def validate(self, data):
        """Validate the entire data object"""
        # Check for potential SQL injection in text fields
        text_fields = ['title', 'description', 'phone_model', 'storage',
                       'screen_condition', 'body_condition', 'includes', 'seller_address']

        for field in text_fields:
            if field in data and data[field]:
                if re.search(r'(?i)(union|select|insert|update|delete|drop|alter|exec|declare|xp_cmdshell)',
                             str(data[field])):
                    raise serializers.ValidationError(
                        {field: "Поле содержит потенциально опасный код"})

        return data

    def update(self, instance, validated_data):
        """Handle image updates"""
        # Handle main image
        main_image = validated_data.pop('main_image', None)
        if main_image is not None:
            if isinstance(main_image, str):
                # If it's a URL, keep the existing image
                validated_data['main_image'] = instance.main_image
            else:
                # If it's a file, update the image
                validated_data['main_image'] = main_image

        # Handle additional images
        for i in range(2, 6):
            image_key = f'image_{i}'
            image = validated_data.pop(image_key, None)
            if image is not None:
                if isinstance(image, str):
                    # If it's a URL, keep the existing image
                    validated_data[image_key] = getattr(instance, image_key)
                else:
                    # If it's a file, update the image
                    validated_data[image_key] = image

        return super().update(instance, validated_data)
