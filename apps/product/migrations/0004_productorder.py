# Generated by Django 5.0.8 on 2024-08-18 10:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
        ('product', '0003_alter_productsale_company_alter_productsale_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductOrder',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('date', models.DateField()),
                ('ozon_quantity', models.IntegerField(default=0)),
                ('wildberries_quantity', models.IntegerField(default=0)),
                ('yandex_market_quantity', models.IntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_orders', to='company.company')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='product.product')),
            ],
            options={
                'verbose_name': 'Product order',
                'verbose_name_plural': 'Product orders',
                'db_table': 'product_orders',
                'ordering': ('product__vendor_code',),
                'unique_together': {('product', 'company', 'date')},
            },
        ),
    ]
