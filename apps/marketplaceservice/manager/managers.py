from django.db.models import Manager, QuerySet
from django.core.exceptions import ObjectDoesNotExist


# Willberries manager
class WillberriesQueryset(QuerySet):

    def wildberries_info_query(self, uuid):
        try:
            data = self.filter(company=uuid).values('wb_api_key')
            return data
        except ObjectDoesNotExist:
            return None


class WillberriesManager(Manager):

    def get_queryset(self) -> QuerySet:
        return WillberriesQueryset(self.model, using=self._db)

    def wildberries_data_query(self, uuid):
        return self.get_queryset().wildberries_info_query(uuid)


# Ozon manager
class OzonQueryset(QuerySet):

    def ozon_info_query(self, uuid):
        try:
            data = self.filter(company=uuid).values('api_token', 'client_id')
            return data
        except ObjectDoesNotExist:
            return None


class OzonManager(Manager):

    def get_queryset(self) -> QuerySet:
        return OzonQueryset(self.model, using=self._db)

    def ozon_info_query(self, uuid):
        return self.get_queryset().ozon_info_query(uuid)


# Yandex Market manager
class YandexMarketQueryset(QuerySet):

    def yandex_market_info_query(self, uuid):
        try:
            data = self.filter(company=uuid).values('api_key_bearer', 'fby_campaign_id', 'fbs_campaign_id',
                                                    'business_id')
            return data
        except ObjectDoesNotExist:
            return None


class YandexMarketManager(Manager):

    def get_queryset(self) -> QuerySet:
        return YandexMarketQueryset(self.model, using=self._db)

    def yandex_market_info_query(self, uuid):
        return self.get_queryset().yandex_market_info_query(uuid)