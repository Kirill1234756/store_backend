# Generated by Django 4.2.7 on 2025-04-13 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_product_seller_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_5',
            field=models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Доп. изображение 4'),
        ),
    ]
