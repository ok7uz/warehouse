# Generated by Django 5.0.7 on 2024-07-25 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_product_vendor_code_product_ozon_barcode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ozon_vendor_code',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='Озон Яндекс.Маркета'),
        ),
    ]
