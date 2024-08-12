from django.contrib import admin

from apps.product.models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'ozon_sku')
