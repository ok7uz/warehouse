# Generated by Django 5.0.8 on 2024-09-12 19:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0021_warhousehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='sortingwarehouse',
            name='shelf',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.shelf'),
        ),
    ]
