from django.contrib import admin

from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse
from django.db.models import Count

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'ozon_sku')

@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'stock')
    search_fields = ['product__vendor_code',"id"]

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(ProductOrder)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'stock')

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(ProductStock)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'stock')
    search_fields = ['vendor_code']

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
admin.site.register(Warehouse)
    


