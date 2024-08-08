from django.contrib import admin
from apps.products.models import Product, WildberriesProductSales, OzonProductSales, YandexMarketProductSales, InProduction


class ProductAdmin(admin.ModelAdmin):
    """
    Админская панель для управления продуктами.
    """
    list_display = ('id', 'place_in_warehouse', 'company')
    list_filter = ('company',)
    fieldsets = (
        (None, {'fields': ('place_in_warehouse', 'company')}),
    )
    ordering = ('id',)


class WildberriesProductSalesAdmin(admin.ModelAdmin):
    """
    Админская панель для управления продажами продуктов на Wildberries.
    """
    list_display = ('id', 'product', 'wildberries', 'quantity', 'remain_quantity', 'created_at', 'updated_at')
    list_filter = ('wildberries', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('product', 'wildberries', 'quantity', 'remain_quantity')}),
        ('Дата', {'fields': ('created_at', 'updated_at')}),
    )
    ordering = ('id',)


class OzonProductSalesAdmin(admin.ModelAdmin):
    """
    Админская панель для управления продажами продуктов на Ozon.
    """
    list_display = ('id', 'product', 'ozon', 'quantity', 'remain_quantity', 'created_at', 'updated_at')
    list_filter = ('ozon', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('product', 'ozon', 'quantity', 'remain_quantity')}),
        ('Дата', {'fields': ('created_at', 'updated_at')}),
    )
    ordering = ('id',)


class YandexMarketProductSalesAdmin(admin.ModelAdmin):
    """
    Админская панель для управления продажами продуктов на YandexMarket.
    """
    list_display = ('id', 'product', 'yandex_market', 'quantity', 'remain_quantity', 'created_at', 'updated_at')
    list_filter = ('yandex_market', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('product', 'yandex_market', 'quantity', 'remain_quantity')}),
        ('Дата', {'fields': ('created_at', 'updated_at')}),
    )
    ordering = ('id',)


class InProductionAdmin(admin.ModelAdmin):
    """
    Админская панель для управления продукцией в производстве.
    """
    list_display = ('id', 'product', 'need_to_produce_quantity', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('product__vendor_code',)
    fieldsets = (
        (None, {'fields': ('product', 'need_to_produce_quantity')}),
        ('Дата', {'fields': ('created_at', 'updated_at')}),
    )
    ordering = ('id',)


# Регистрация моделей и их админских панелей
admin.site.register(Product, ProductAdmin)
admin.site.register(WildberriesProductSales, WildberriesProductSalesAdmin)
admin.site.register(OzonProductSales, OzonProductSalesAdmin)
admin.site.register(YandexMarketProductSales, YandexMarketProductSalesAdmin)
