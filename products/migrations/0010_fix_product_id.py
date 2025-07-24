from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_add_product_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mediaimage',
            name='product_id',
        ),
        migrations.AddField(
            model_name='mediaimage',
            name='product',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='media_images',
                to='products.product',
                db_column='product_id'
            ),
        ),
    ] 