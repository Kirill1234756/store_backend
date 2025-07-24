from django.core.management.base import BaseCommand
from products.models import Product
from products.media_models import MediaImage

class Command(BaseCommand):
    help = 'Удаляет битые MediaImage без файлов и сбрасывает main_image у Product без файла.'

    def handle(self, *args, **options):
        broken_images = MediaImage.objects.filter(image_file='')
        broken_count = broken_images.count()
        broken_images.delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено битых MediaImage: {broken_count}'))

        broken_products = Product.objects.filter(main_image='')
        product_count = broken_products.count()
        broken_products.update(main_image=None)
        self.stdout.write(self.style.SUCCESS(f'Сброшено main_image у Product: {product_count}')) 