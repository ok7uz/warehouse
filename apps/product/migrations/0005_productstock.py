# Generated by Django 5.0.8 on 2024-08-18 12:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
        ('product', '0004_productorder'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductStock',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('warehouse', models.CharField(max_length=256)),
                ('ozon_quantity', models.IntegerField(default=0)),
                ('wildberries_quantity', models.IntegerField(default=0)),
                ('yandex_market_quantity', models.IntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_stocks', to='company.company')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='product.product')),
            ],
            options={
                'verbose_name': 'Product stock',
                'verbose_name_plural': 'Product stocks',
                'db_table': 'product_stocks',
                'ordering': ('product__vendor_code',),
                'unique_together': {('product', 'company', 'warehouse')},
            },
        ),
    ]
