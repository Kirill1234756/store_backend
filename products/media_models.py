from django.db import models
from django.utils.text import slugify
from .image_utils import save_image, delete_image
from .models import Product
import os

class MediaImage(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image_file = models.ImageField(upload_to='products/additional/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Image'
        verbose_name_plural = 'Media Images'
    
    def __str__(self):
        return self.title or f'Image {self.id}'
    
    @property
    def image(self):
        if self.image_file:
            return self.image_file.url
        return None

    @property
    def image_url(self):
        if self.image_file:
            return self.image_file.url
        return None
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"Additional image"
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.image_file:
            try:
                delete_image(self.image_file.path)
            except:
                pass
        super().delete(*args, **kwargs) 