from django.contrib import admin

from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse, WarehouseForStock
from django.db.models import Count

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['vendor_code']

@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'marketplace_type')
    search_fields = ['product__vendor_code',"id"]
    list_filter = ["marketplace_type","date"]

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(ProductOrder)
class ProductOrderAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'stock')
    list_filter = ["marketplace_type","date"]

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(ProductStock)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'stock')
    search_fields = ['vendor_code']
    list_filter = ["marketplace_type"]

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(Warehouse)
class WareHouseAdminView(admin.ModelAdmin):
    search_fields=["name","oblast_okrug_name"]
    
    
@admin.register(WarehouseForStock)
class WareHouseForStockAdminView(admin.ModelAdmin):
    search_fields=["name"]
    list_filter = ["marketplace_type"]
    


