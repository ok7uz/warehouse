import datetime
import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.accounts.models import CustomUser
from apps.companies.models import Company
from apps.companies.utils import get_ozon_sales
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket


class CompanySerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    """
    Serializer for Company model.

    This serializer serializes Company model fields.
    """

    class Meta:
        model = Company
        fields = '__all__'

    def get_parent(self, obj):
        if obj.parent is not None:
            data = CompanySerializer(obj.parent, context={'request': self.context.get('request')}).data
            return data
        else:
            return None


class CompanyCreateAndUpdateSerializers(serializers.ModelSerializer):
    """
    Serializer for listing companies.

    This serializer serializes Company model fields for listing purposes.
    """
    # wilbreries body
    wb_api_key = serializers.CharField(required=False)

    # ozon body
    api_token = serializers.CharField(required=False)
    client_id = serializers.CharField(required=False)

    # yandex market body
    api_key_bearer = serializers.CharField(required=False)
    fby_campaign_id = serializers.CharField(required=False)
    fbs_campaign_id = serializers.CharField(required=False)
    business_id = serializers.CharField(required=False)

    class Meta:
        model = Company
        fields = [
            'uuid', 'name', 'wb_api_key', 'api_token', 'client_id',
            'api_key_bearer', 'fby_campaign_id', 'fbs_campaign_id',
            'business_id', 'created_at', 'parent'
        ]

        extra_kwargs = {
            'name': {'required': True},
        }

        def create(self, validated_data):
            company = Company.objects.create(**validated_data)

            if validated_data['parent']:
                try:
                    parent = Company.objects.get(uuid=validated_data['parent'])
                    company.parent = parent
                    company.save()
                except ObjectDoesNotExist:
                    raise serializers.ValidationError("Parent company doesn't exist")

            if validated_data['wb_api_key']:
                willberries = Wildberries.objects.create(**validated_data, company=company)
            elif validated_data['api_token'] and validated_data['client_id']:
                ozon = Ozon.objects.create(**validated_data, company=company)
            elif (validated_data['api_key_bearer'] and validated_data['fby_campaign_id'] and
                  validated_data['fbs_campaign_id'] and validated_data['business_id']):
                yandex_market = YandexMarket.objects.create(**validated_data, company=company)

            user = self.context.get('request')
            try:
                user = CustomUser.objects.get(username=user)
                user.company.add(company)
            except ObjectDoesNotExist:
                raise serializers.ValidationError("User doesn't exist")

            return company

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        if validated_data.get('wb_api_key', None):
            self.willberries_change(validated_data['wb_api_key'], instance)

        if validated_data.get('api_token', None) and validated_data.get('client_id', None):
            print("'bor'")
            self.ozon_change(validated_data['api_token'], validated_data['client_id'], instance)

        if (validated_data.get('api_key_bearer', None) and validated_data.get('fby_campaign_id') and
                validated_data.get('fbs_campaign_id') and validated_data.get('business_id')):
            self.yandex_market_change(validated_data['api_key_bearer'], validated_data['fby_campaign_id'],
                    validated_data['fbs_campaign_id'], validated_data['business_id'], instance)
        instance.updated_at = datetime.datetime.now()
        instance.save()
        return instance
    
    def willberries_change(self, wb_api_key, company):
        data_updated = Wildberries.objects.filter(company=company).update(wb_api_key=wb_api_key)
        return data_updated

    def ozon_change(self, api_token, client_id, company):
        if Ozon.objects.filter(company=company).exists():
            data_updated = Ozon.objects.filter(company=company).update(api_token=api_token, client_id=client_id)
        else:
            data_updated = Ozon.objects.create(api_token=api_token, client_id=client_id, company=company)
        return data_updated

    def yandex_market_change(self, api_key_bearer, fby_campaign_id, fbs_campaign_id, business_id, company):
        data_updated = YandexMarket.objects.filter(company=company).update(api_key_bearer=api_key_bearer,
                fby_campaign_id=fby_campaign_id, fbs_campaign_id=fbs_campaign_id, business_id=business_id)
        return data_updated


class CompaniesSerializers(serializers.ModelSerializer):
    """
    Serializer for listing companies.

    This serializer serializes Company model fields for listing purposes.
    """
    willberries = serializers.SerializerMethodField()
    ozon = serializers.SerializerMethodField()
    yandex_market = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["uuid", "parent", "name", "willberries", "ozon", "yandex_market"]

    def get_parent(self, obj):
        if obj.parent is not None:
            data = CompanySerializer(obj.parent, context={'request': self.context.get('request')}).data
            return data
        else:
            return None

    def get_willberries(self, obj):
        data_list = Wildberries.obj.wildberries_data_query(obj)
        return data_list

    def get_ozon(self, obj):
        data_list = Ozon.obj.ozon_info_query(obj)
        return data_list

    def get_yandex_market(self, obj):
        data_list = YandexMarket.obj.yandex_market_info_query(obj)
        return data_list


class CompanySalesSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField(read_only=True)
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ["uuid", "data", 'product_count']

    async def get_data(self, obj):
        ozon = Ozon.objects.filter(company=obj).first()
        ozon_data = await get_ozon_sales(client_id=ozon.client_id, api_token=ozon.api_token)
        self.product_count = len(ozon_data)
        return ozon_data

    def get_product_count(self, obj):
        return None
