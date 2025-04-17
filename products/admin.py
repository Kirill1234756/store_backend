from django.contrib import admin
from .models import Product
from django.utils.html import format_html


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'condition_badge',
                    'seller_info', 'created_at')
    list_filter = ('condition', 'created_at', 'phone_model')
    search_fields = ('title', 'phone_model', 'seller_phone')
    readonly_fields = ('created_at', 'updated_at', 'product_images')
    fieldsets = (
        ('Product Info', {
            'fields': ('title', 'description', 'price', 'condition')
        }),
        ('Technical Specs', {
            'fields': ('phone_model', 'storage', 'battery_health')
        }),
        ('Seller Info', {
            'fields': ('seller_phone', 'seller_address')
        }),
        ('Media', {
            'fields': ('product_images',)
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

    def seller_info(self, obj):
        return f"{obj.seller_phone} | {obj.seller_address}"
    seller_info.short_description = 'Seller Contact'

    def product_images(self, obj):
        return format_html(
            "".join(
                f'<img src="{img.url}" style="max-height: 100px; margin: 5px;" />'
                for img in [obj.main_image, obj.image_2, obj.image_3, obj.image_4]
                if img
            )
        )
    product_images.short_description = 'Images'
