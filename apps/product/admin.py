from django.contrib import admin

from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse, WarehouseForStock, \
      Recommendations, InProduction, Shelf, SortingWarehouse, WarehouseHistory
from django.db.models import Count
from django_celery_results.models import TaskResult

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['vendor_code',"id"]
    search_fields = ['vendor_code', "id"]

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
    list_display = ('vendor_code', 'date')
    list_filter = ["marketplace_type","date"]
    search_fields = ['product__vendor_code',"id"]

    def vendor_code(self, productsale_obj):
        return productsale_obj.product.vendor_code
    
    def stock(self, productsale_obj):
        date = productsale_obj.date
        return ProductSale.objects.filter(date__date=date).values('product').annotate(sales_count=Count('id')).count()
    
@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', "quantity", 'date', "marketplace_type","company", "warehouse",)
    search_fields = ['product__vendor_code']
    list_filter = ["marketplace_type", "date"]

    def vendor_code(self, product_obj: ProductStock):
        return product_obj.product.vendor_code

    def company(self, productsale_obj: ProductStock):
        return productsale_obj.company.name
    
    def warehouse(self, productsale_obj: ProductStock):
        return productsale_obj.warehouse.name
    
@admin.register(Warehouse)
class WareHouseAdminView(admin.ModelAdmin):
    search_fields=["name","oblast_okrug_name"]
    
    
@admin.register(WarehouseForStock)
class WareHouseForStockAdminView(admin.ModelAdmin):
    search_fields=["name"]
    list_filter = ["marketplace_type"]
    
@admin.register(Recommendations)
class RecommendationsAdminView(admin.ModelAdmin):
    list_display =["vendor_code", "id", "quantity", "days_left", "application_for_production"]
    search_filter = ["product__vendor_code"]

    def vendor_code(self, recommandations: Recommendations):
        return recommandations.product.vendor_code
    
@admin.register(InProduction)
class InProductionAdminView(admin.ModelAdmin):
    list_display =["vendor_code", "id", "manufacture", "produced"]
    search_filter = ["product__vendor_code"]

    def vendor_code(self, recommandations: Recommendations):
        return recommandations.product.vendor_code
    
@admin.register(Shelf)
class ShelfAdminView(admin.ModelAdmin):
    list_display =["vendor_code", "id", "shelf_name", "stock"]
    search_filter = ["product__vendor_code"]

    def vendor_code(self, recommandations: Recommendations):
        return recommandations.product.vendor_code
    
@admin.register(SortingWarehouse)
class SortingWarehouseAdminView(admin.ModelAdmin):
    list_display =["vendor_code", "id", "unsorted"]
    search_filter = ["product__vendor_code"]

    def vendor_code(self, recommandations: Recommendations):
        return recommandations.product.vendor_code
    
@admin.register(WarehouseHistory)
class WarehouseHistoryAdminView(admin.ModelAdmin):
    list_display =["vendor_code", "id", "date","stock"]
    search_filter = ["product__vendor_code"]

    def vendor_code(self, recommandations: Recommendations):
        return recommandations.product.vendor_code
