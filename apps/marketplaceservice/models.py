from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.marketplaceservice.manager.managers import WillberriesManager, YandexMarketManager, OzonManager


class Wildberries(models.Model):
    """
    Модель Wildberries для хранения информации об API ключах.
    """
    uuid = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    wb_api_key = models.CharField(_("API ключ Wildberries"), max_length=1000, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="wildberries", verbose_name="Компания")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now=False, verbose_name="Дата обновления", null=True, blank=True)

    objects = models.Manager()
    obj = WillberriesManager()

    def __str__(self):
        return f"Wildberries : {self.company.name}"

    class Meta:
        db_table = "wildberries_table"
        verbose_name = "Wildberries"
        verbose_name_plural = "Wildberries"


class Ozon(models.Model):
    """
    Модель Ozon для хранения информации об API ключах.
    """
    uuid = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    api_token = models.CharField(_("API токен Ozon"), max_length=1000, null=True, blank=True)
    client_id = models.CharField(_("Клиентский ID Ozon"), max_length=1000, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="ozon", verbose_name="Компания")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now=False, verbose_name="Дата обновления", null=True, blank=True)

    objects = models.Manager()
    obj = OzonManager()

    def __str__(self):
        return f"Ozon : {self.company.name}"

    class Meta:
        db_table = "ozon_table"
        verbose_name = "Ozon"
        verbose_name_plural = "Ozon"


class YandexMarket(models.Model):
    """
    Модель YandexMarket для хранения информации об API ключах.
    """
    uuid = models.IntegerField(primary_key=True, editable=False, unique=True, verbose_name='Уникальный идентификатор')
    api_key_bearer = models.CharField(_("API ключ Bearer YandexMarket"), max_length=1000, null=True, blank=True)
    fby_campaign_id = models.CharField(_("FBS Кампания ID YandexMarket"), max_length=1000, null=True, blank=True)
    fbs_campaign_id = models.CharField(_("FBY Кампания ID YandexMarket"), max_length=1000, null=True, blank=True)
    business_id = models.CharField(_("Бизнес ID YandexMarket"), max_length=1000, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="YandexMarketCompany", verbose_name="Компания")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateField(auto_now=False, verbose_name="Дата обновления", null=True, blank=True)

    objects = models.Manager()
    obj = YandexMarketManager()

    def __str__(self):
        return f"YandexMarket : {self.company.name}"

    class Meta:
        db_table = "yandexMarket_table"
        verbose_name = "YandexMarket"
        verbose_name_plural = "YandexMarket"
