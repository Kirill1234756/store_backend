from django.contrib import admin
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import Product
from .media_models import MediaImage
from .widgets import MultipleClearableFileInput

class ProductAdminForm(forms.ModelForm):
    package_contents = forms.MultipleChoiceField(
        choices=Product.PACKAGE_CONTENTS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Комплектация',
        help_text='Выберите все предметы, входящие в комплект'
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['package_contents'] = self.instance.package_contents or []

    def clean_package_contents(self):
        return self.cleaned_data['package_contents']

# --- Product admin registration (restore if missing) ---
class MediaImageInline(admin.TabularInline):
    model = Product.product_images.through
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [MediaImageInline]
    form = ProductAdminForm
    list_display = ('id', 'title', 'price', 'condition', 'is_active', 'is_top', 'created_at', 'phone_number', 'city')
    search_fields = ('title', 'phone_model', 'description', 'phone_number', 'city')
    list_filter = ('condition', 'is_active', 'is_top', 'created_at', 'city')
    ordering = ('-created_at',)
    list_per_page = 20

# --- MediaImage admin and upload form (as before) ---
class ImageUploadForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label='Товар',
        help_text='Выберите товар для загрузки изображений'
    )
    is_main = forms.BooleanField(
        required=False,
        initial=False,
        label='Сделать главным',
        help_text='Отметьте, если это главное изображение товара'
    )
    images = forms.FileField(
        widget=MultipleClearableFileInput(attrs={'accept': 'image/*', 'class': 'file-input'}),
        label='Изображения',
        help_text='Выберите одно или несколько изображений'
    )

@admin.register(MediaImage)
class MediaImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'image_file', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'product__title')
    readonly_fields = ('created_at', 'updated_at', 'get_image_preview_large')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.admin_site.admin_view(self.upload_view), name='mediaimage_upload'),
        ]
        return custom_urls + urls

    def upload_view(self, request):
        if request.method == 'POST':
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.cleaned_data['product']
                is_main = form.cleaned_data['is_main']
                files = request.FILES.getlist('images')
                
                for i, image in enumerate(files):
                    media_image = MediaImage.objects.create(
                        product=product,
                        title=f"{product.title} - Image {i+1}",
                        image_file=image
                    )
                    
                    # Если это первое изображение и is_main отмечено,
                    # или если это единственное изображение
                    if (i == 0 and is_main) or len(files) == 1:
                        product.main_image = media_image.image_file
                        product.save()
                
                messages.success(request, f'Успешно загружено {len(files)} изображений')
                return redirect('admin:products_mediaimage_changelist')
        else:
            form = ImageUploadForm()
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Загрузка изображений',
            'form': form,
            'opts': self.model._meta,
            'has_file_field': True
        }
        
        return TemplateResponse(request, 'admin/mediaimage/upload.html', context)

    def is_main_image(self, obj):
        if obj.product and obj.product.main_image:
            is_main = obj.image_file == obj.product.main_image
            return format_html(
                '<span style="color: {};">{}</span>',
                'green' if is_main else 'gray',
                'Главное' if is_main else 'Дополнительное'
            )
        return '-'
    is_main_image.short_description = 'Тип'

    def get_image_preview(self, obj):
        if obj.image_file:
            try:
                return format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                    obj.image_file.url
                )
            except Exception:
                return format_html('<span style="color: red;">Ошибка отображения</span>')
        return format_html('<span style="color: gray;">Нет изображения</span>')
    get_image_preview.short_description = 'Превью'
    
    def get_image_preview_large(self, obj):
        if obj.image_file:
            try:
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<img src="{}" style="max-width: 300px; max-height: 300px;" />'
                    '</div>',
                    obj.image_file.url
                )
            except Exception:
                return format_html('<span style="color: red;">Ошибка отображения</span>')
        return format_html('<span style="color: gray;">Нет изображения</span>')
    get_image_preview_large.short_description = 'Текущее изображение'

    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }
        js = ('admin/js/jquery.init.js',)
