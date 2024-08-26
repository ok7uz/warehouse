from typing import Iterable
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.company.models import Company
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket


class Warehouse(models.Model):

    name = models.CharField(max_length=50)
    country_name = models.CharField(max_length=200)
    oblast_okrug_name = models.CharField(max_length=200)
    region_name = models.CharField(max_length=200)
    shelf = models.CharField(max_length=10)

    class Meta:

        db_table = "warehouse"
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouse"
        ordering = ["name"]
        unique_together = ("name","country_name", "oblast_okrug_name", "region_name", "shelf")

class Product(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    vendor_code = models.CharField(max_length=1000)
    ozon_sku = models.CharField(max_length=1000, null=True)

    class Meta:
        db_table = "product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ('vendor_code',)


class ProductSale(models.Model):
    
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_sales')
    date = models.DateTimeField()
    warehouse = models.ForeignKey(Warehouse,on_delete=models.CASCADE)

    MARKETPLACE_CHOICES = [
    ('wildberries', 'Wildberries'),
    ('ozon', 'Ozon'),
    ('yandexmarket', 'YandexMarket'),
]
    
    marketplace_type = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES)

    class Meta:
        db_table = "product_sales"
        verbose_name = "Product sale"
        verbose_name_plural = "Product sales"
        ordering = ('product__vendor_code',)
        unique_together = ('product', 'company', 'date')


class ProductOrder(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_orders')
    date = models.DateTimeField()
    warehouse = models.ForeignKey(Warehouse,on_delete=models.CASCADE)

    MARKETPLACE_CHOICES = [
    ('wildberries', 'Wildberries'),
    ('ozon', 'Ozon'),
    ('yandexmarket', 'YandexMarket'),
]
    
    marketplace_type = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES)
    

    class Meta:
        db_table = "product_orders"
        verbose_name = "Product order"
        verbose_name_plural = "Product orders"
        ordering = ('product__vendor_code',)
        unique_together = ('product', 'company', 'date')

class ProductStock(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_stocks')
    warehouse = models.ForeignKey(Warehouse,on_delete=models.CASCADE)
    ozon_quantity = models.IntegerField(default=0)
    wildberries_quantity = models.IntegerField(default=0)
    yandex_market_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "product_stocks"
        verbose_name = "Product stock"
        verbose_name_plural = "Product stocks"
        ordering = ('product__vendor_code',)
        unique_together = ('product', 'company', 'warehouse')

