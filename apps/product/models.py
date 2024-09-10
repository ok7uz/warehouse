from typing import Iterable
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

from apps.company.models import Company

class Warehouse(models.Model):

    name = models.CharField(max_length=50)
    country_name = models.CharField(max_length=200)
    oblast_okrug_name = models.CharField(max_length=200)
    region_name = models.CharField(max_length=200)

    class Meta:

        db_table = "warehouse"
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouse"
        ordering = ["name"]
        unique_together = ("name","country_name", "oblast_okrug_name", "region_name")

    def __str__(self) -> str:
        return self.name
    
class WarehouseForStock(models.Model):
    
    name = models.CharField(max_length=50)

    MARKETPLACE_CHOICES = [
    ('wildberries', 'Wildberries'),
    ('ozon', 'Ozon'),
    ('yandexmarket', 'YandexMarket'),
    ]
    
    marketplace_type = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES)

    def __str__(self) -> str:
        return self.name

class Product(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    vendor_code = models.CharField(max_length=1000)

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
        unique_together = ('product', 'company', 'date', 'warehouse', 'marketplace_type')

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
        unique_together = ('product', 'company', 'date', 'warehouse', 'marketplace_type')

class ProductStock(models.Model):
    
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_stocks')
    warehouse = models.ForeignKey(WarehouseForStock,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    
    MARKETPLACE_CHOICES = [
    ('wildberries', 'Wildberries'),
    ('ozon', 'Ozon'),
    ('yandexmarket', 'YandexMarket'),
    ]
    
    marketplace_type = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES)

    class Meta:

        db_table = "product_stocks"
        verbose_name = "Product stock"
        verbose_name_plural = "Product stocks"
        
        unique_together = ('product', 'company', 'date', 'warehouse', 'marketplace_type')

class Recommendations(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    succes_quantity = models.PositiveIntegerField(default=0)
    days_left = models.IntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def save(self, *args, **kwargs) -> None:
        
        if self.quantity == self.succes_quantity:
            self.delete()
            return
        super().save(*args, **kwargs)

    class Meta:
        db_table = "recommendations"
        verbose_name = "Рекомендации"
        ordering = ["quantity"]

class InProduction(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    manufacture = models.PositiveIntegerField()
    produced = models.PositiveIntegerField(default=0)
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    recommendations = models.OneToOneField(Recommendations,on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.product.vendor_code
    
