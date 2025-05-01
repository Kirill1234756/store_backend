from django.db import models
from django.utils.text import slugify
from .image_utils import save_image, delete_image
import os

class MediaImage(models.Model):
    """Model for storing media images"""
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='media/images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Image'
        verbose_name_plural = 'Media Images'
    
    def __str__(self):
        return self.title or os.path.basename(self.image.name)
    
    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            # Delete old image if exists
            if self.pk:
                old_instance = MediaImage.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    delete_image(old_instance.image.path)
            
            # Save new image
            self.image.name = save_image(self.image, path_prefix='media/images/')
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.image:
            delete_image(self.image.path)
        super().delete(*args, **kwargs) 