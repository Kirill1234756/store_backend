from rest_framework import serializers
from .media_models import MediaImage
import os

class MediaImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaImage
        fields = ['id', 'title', 'image', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
    
    def validate_image(self, value):
        if value:
            # Check file size (5MB limit)
            if value.size > 5242880:  # 5MB
                raise serializers.ValidationError("Image size must be less than 5MB")
            
            # Check file extension
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise serializers.ValidationError("Only jpg, jpeg, png, gif and webp files are allowed")
        return value 