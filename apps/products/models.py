from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket


class Product(models.Model):
    """
    Модель продукта для хранения информации о товарах.
    """
    id = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    place_in_warehouse = models.CharField(_("Местонахождение на складе"), max_length=500, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="ProductCompany", verbose_name="Компания")
    ozon_vendor_code = models.CharField(_("Озон Яндекс.Маркета"), max_length=1000, null=True, blank=True)
    ozon_barcode = models.CharField(_("Штрих-код Ozon"), max_length=1000, null=True, blank=True)
    ozon_product_id = models.CharField(_("ID продукта Ozon"), max_length=1000, null=True, blank=True)
    ozon_sku = models.CharField(_("SKU Ozon"), max_length=1000, null=True, blank=True)
    ozon_fbo_sku_id = models.CharField(_("ID SKU FBO Ozon"), max_length=1000, null=True, blank=True)
    ozon_fbs_sku_id = models.CharField(_("ID SKU FBS Ozon"), max_length=1000, null=True, blank=True)
    yandex_vendor_code = models.CharField(_("Артикул Яндекс.Маркета"), max_length=1000, null=True, blank=True)
    yandex_barcode = models.CharField(_("Штрих-код Яндекс.Маркета"), max_length=1000, null=True, blank=True)
    yandex_sku = models.CharField(_("SKU Яндекс.Маркета"), max_length=1000, null=True, blank=True)
    willberries_vendor_code = models.CharField(_("Артикул Willberries"), max_length=1000, null=True, blank=True)
    willberries_barcode = models.CharField(_("Штрих-код Willberries"), max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.vendor_code  # what is that brother??

    class Meta:
        db_table = "product_table"
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"


class WildberriesProductSales(models.Model):
    """
    Модель для хранения информации о продажах продуктов на Wildberries.
    """
    id = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Количество проданных товаров")
    remain_quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Остаток товаров")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="WildberriesProduct", verbose_name="Продукт")
    wildberries = models.ForeignKey(Wildberries, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="WildberriesProduct", verbose_name="Wildberries")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now_add=False, verbose_name="Дата обновления")

    def __str__(self):
        return self.product.vendor_code  # wtf??

    class Meta:
        db_table = "wildberries_product_table"
        verbose_name = "Продажи на Wildberries"
        verbose_name_plural = "Продажи на Wildberries"


class OzonProductSales(models.Model):
    """
    Модель для хранения информации о продажах продуктов на Ozon.
    """
    id = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Количество проданных товаров")
    remain_quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Остаток товаров")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="OzonProduct", verbose_name="Продукт")
    ozon = models.ForeignKey(Ozon, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="OzonProduct", verbose_name="Ozon")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now_add=False, verbose_name="Дата обновления")

    def __str__(self):
        return self.product.vendor_code

    class Meta:
        db_table = "ozon_product_table"
        verbose_name = "Продажи на Ozon"
        verbose_name_plural = "Продажи на Ozon"


class YandexMarketProductSales(models.Model):
    """
    Модель для хранения информации о продажах продуктов на YandexMarket.
    """
    id = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Количество проданных товаров")
    remain_quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Остаток товаров")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="YandexMarketProduct", verbose_name="Продукт")
    yandex_market = models.ForeignKey(YandexMarket, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name="YandexMarketProduct", verbose_name="YandexMarket")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now_add=False, verbose_name="Дата обновления")

    def __str__(self):
        return self.product.vendor_code

    class Meta:
        db_table = "yandex_market_product_table"
        verbose_name = "Продажи на YandexMarket"
        verbose_name_plural = "Продажи на YandexMarket"


class InProduction(models.Model):
    """
    Модель для хранения информации о продуктах в производстве.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Продукт",
                                related_name="InProductionProduct")
    need_to_produce_quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Необходимо произвести")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now_add=False, verbose_name="Дата обновления")

    def __str__(self):
        return self.product.vendor_code

    class Meta:
        db_table = "in_production_product_table"
        verbose_name = "В производстве"
        verbose_name_plural = "В производстве"
