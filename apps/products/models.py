from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket


class Product(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    vendor_code = models.CharField(max_length=1000)
    ozon_sku = models.CharField(max_length=1000, null=True)

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ('vendor_code',)


class ProductSale(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_sales')
    date = models.DateField()
    ozon_quantity = models.IntegerField(default=0)
    wildberries_quantity = models.IntegerField(default=0)
    yandex_market_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "product_sales"
        verbose_name = "Product sale"
        verbose_name_plural = "Product sales"
        ordering = ('product__vendor_code',)
        unique_together = ('product', 'company', 'date')
