from django.contrib import admin
from .models import Product, MediaImage
from django.utils.html import format_html


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'condition_badge', 'is_active', 'created_at')
    list_display_links = ('id', 'title')
    list_filter = ('condition', 'created_at', 'phone_model', 'is_active')
    search_fields = ('title', 'phone_model', 'description')
    readonly_fields = ('created_at', 'updated_at', 'product_images')
    fieldsets = (
        ('Product Info', {
            'fields': ('title', 'description', 'price', 'condition', 'is_active')
        }),
        ('Technical Specs', {
            'fields': ('phone_model', 'storage', 'battery_health', 'color', 'screen_size', 'screen_condition', 'body_condition')
        }),
        ('Media', {
            'fields': ('main_image', 'additional_images', 'product_images')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def condition_badge(self, obj):
        color = {
            'A': 'green',
            'B': 'orange',
            'C': 'red'
        }.get(obj.condition, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_condition_display()
        )
    condition_badge.short_description = 'Condition'

    def product_images(self, obj):
        if not obj.main_image and not obj.additional_images.exists():
            return "No images"
        
        images_html = []
        if obj.main_image:
            images_html.append(
                f'<div style="margin-bottom: 10px;">'
                f'<strong>Main Image:</strong><br>'
                f'<img src="{obj.main_image.url}" style="max-width: 200px; max-height: 200px;">'
                f'</div>'
            )
        
        if obj.additional_images.exists():
            images_html.append('<div><strong>Additional Images:</strong><br>')
            for img in obj.additional_images.all():
                images_html.append(
                    f'<img src="{img.image.url}" style="max-width: 200px; max-height: 200px; margin-right: 10px;">'
                )
            images_html.append('</div>')
        
        return format_html(''.join(images_html))
    product_images.short_description = 'Current Images'


@admin.register(MediaImage)
class MediaImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
