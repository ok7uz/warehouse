from django.contrib import admin

from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse, WarehouseForStock, \
      Recommendations, InProduction, Shelf, SortingWarehouse, WarehouseHistory, RecomamandationSupplier, PriorityShipments, \
      ShipmentHistory, Shipment
from django.db.models import Count
from django_celery_results.models import TaskResult

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['vendor_code',"id"]
    search_fields = ['vendor_code', "id"]

@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'marketplace_type')
    search_fields = ['product__vendor_code',"id", "warehouse__id"]
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
    search_fields=["id","name","oblast_okrug_name"]
    list_display = ["id","name", "oblast_okrug_name", "region_name"]    
    
@admin.register(WarehouseForStock)
class WareHouseForStockAdminView(admin.ModelAdmin):
    search_fields=["id","name"]
    list_display = ["id","name"]
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

@admin.register(RecomamandationSupplier)
class RecomamandationSupplierAdminView(admin.ModelAdmin):
    list_display =["id", "vendor_code", "days_left","quantity", "marketplace_type"]
    search_fields = ["product__vendor_code","warehouse__id"]
    list_filter = ["marketplace_type"]

    def vendor_code(self, recommandations: RecomamandationSupplier):
        return recommandations.product.vendor_code

@admin.register(PriorityShipments)
class PriorityShipmentsrAdminView(admin.ModelAdmin):
    
    list_display =["id", "vendor_code", "travel_days","arrive_days", "marketplace_type", "sales", "sales_share","shipments_share","shipping_priority"]
    search_fields = ["warehouse__id"]
    list_filter = ["marketplace_type"]

    def vendor_code(self, recommandations: PriorityShipments):
        return recommandations.warehouse.region_name or recommandations.warehouse.oblast_okrug_name

@admin.register(Shipment)
class PriorityShipmentsrAdminView(admin.ModelAdmin):
    
    list_display =["id", "vendor_code", "shipment"]
    search_fields = ["product__vendor_code"]
    list_filter = ["company"]

    def vendor_code(self, recommandations: Shipment):
        return recommandations.product.vendor_code

@admin.register(ShipmentHistory)
class ShipmentHistoryAdminView(admin.ModelAdmin):
    
    list_display =["id", "vendor_code", "quantity", "date"]
    search_fields = ["product__vendor_code"]
    list_filter = ["company"]

    def vendor_code(self, recommandations: ShipmentHistory):
        return recommandations.product.vendor_code

