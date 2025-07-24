from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_alter_mediaimage_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaimage',
            name='product_id',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='media_images',
                to='products.product'
            ),
        ),
    ] 