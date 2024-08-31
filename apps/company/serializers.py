import datetime

from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.accounts.models import CustomUser
from apps.company.models import Company
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket
from apps.product.models import Product, ProductStock, ProductSale, ProductOrder


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'



class CompanyCreateAndUpdateSerializers(serializers.ModelSerializer):
    wb_api_key = serializers.CharField(required=False)

    api_token = serializers.CharField(required=False)
    client_id = serializers.CharField(required=False)

    api_key_bearer = serializers.CharField(required=False)
    fby_campaign_id = serializers.CharField(required=False)
    fbs_campaign_id = serializers.CharField(required=False)
    business_id = serializers.CharField(required=False)

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'wb_api_key', 'api_token', 'client_id',
            'api_key_bearer', 'fby_campaign_id', 'fbs_campaign_id',
            'business_id', 'created_at'
        ]

        extra_kwargs = {
            'name': {'required': True},
        }

    def create(self, validated_data):
        wb_api_key = validated_data.pop('wb_api_key', None)
        api_token = validated_data.pop('api_token', None)
        client_id = validated_data.pop('client_id', None)
        api_key_bearer = validated_data.pop('api_key_bearer', None)
        fby_campaign_id = validated_data.pop('fby_campaign_id', None)
        fbs_campaign_id = validated_data.pop('fbs_campaign_id', None)
        business_id = validated_data.pop('business_id', None)
        company = Company.objects.create(**validated_data)
        
        if wb_api_key:
            willberries = Wildberries.objects.create(wb_api_key=wb_api_key, company=company)
        if api_token and client_id:
            ozon = Ozon.objects.create(api_token=api_token, client_id=client_id, company=company)
        if api_key_bearer and fby_campaign_id and fbs_campaign_id and business_id:
            yandex_market = YandexMarket.objects.create(
                api_key_bearer=api_key_bearer, fby_campaign_id=fby_campaign_id,
                fbs_campaign_id=fbs_campaign_id, business_id=business_id, company=company
            )

        user = self.context.get('request').user
        try:
            user = CustomUser.objects.get(id=user.id)
            user.company.add(company)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User doesn't exist")

        return company

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        if validated_data.get('wb_api_key', None):
            
            self.willberries_change(validated_data['wb_api_key'], instance)

        if validated_data.get('api_token', None) and validated_data.get('client_id', None):
            
            self.ozon_change(validated_data['api_token'], validated_data['client_id'], instance)

        if (validated_data.get('api_key_bearer', None) and validated_data.get('fby_campaign_id', None) and
                validated_data.get('fbs_campaign_id', None) and validated_data.get('business_id', None)):
            self.yandex_market_change(validated_data['api_key_bearer'], validated_data['fby_campaign_id'],
                    validated_data['fbs_campaign_id'], validated_data['business_id'], instance)
        instance.updated_at = datetime.datetime.now()
        instance.save()
        return instance
    
    def willberries_change(self, wb_api_key, company):
        if Wildberries.objects.filter(company=company).exists():
            data_updated = Wildberries.objects.filter(company=company).update(wb_api_key=wb_api_key)
        else:
            data_updated = Wildberries.objects.create(wb_api_key=wb_api_key, company=company)
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
    Serializer for listing company.

    This serializer serializes Company model fields for listing purposes.
    """
    willberries = serializers.SerializerMethodField()
    ozon = serializers.SerializerMethodField()
    yandex_market = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["id", "name", "willberries", "ozon", "yandex_market"]

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
        fields = ["id", "data", 'product_count']

    def get_data(self, obj):
        
        page = self.context.get('request').query_params.get('page', None)
        page_size = self.context.get('request').query_params.get('page_size', None)
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', None)
        vendor_code = self.context.get('request').query_params.get('article', "")
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 10
        date_from = datetime.datetime.strptime(date_from,
                                               '%Y-%m-%d').date() if date_from else datetime.date.today() - datetime.timedelta(
            days=6)

        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.date.today()

        if service == 'ozon':
            products = ProductSale.objects.filter(company=obj, marketplace_type="ozon",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')

        elif service == 'yandexmarket':
            products = ProductSale.objects.filter(company=obj, marketplace_type="yandexmarket",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')

        elif service == 'wildberries':
            products = ProductSale.objects.filter(company=obj, marketplace_type="wildberries",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        
        else:
            products = ProductSale.objects.filter(company=obj,date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
       
        products = products[(page - 1) * page_size: page * page_size]
        results = {}
        
        for product in products:
            
            p_order = product.product
            order = product
            vendor_code = product.product.vendor_code
            date = order.date.strftime("%Y-%m-%d")
            
            if (date_to - date_from).days == 0:
                regions = [warehouse.warehouse.region_name for warehouse in products]
                date_ = order.warehouse.region_name
                warehouse_obj= order.warehouse
                results[vendor_code] = {datee: 0 for datee in regions}
                
            else:
                date_= order.date.strftime("%Y-%m-%d")
                warehouse_obj = None
                date_range = [(date_from + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range((date_to - date_from).days + 1)]
                results[vendor_code] = {datee: 0 for datee in date_range}
            
            
            if service == 'ozon':
                results[vendor_code][date_] = ProductSale.objects.filter(date__date=date, company=obj, marketplace_type="ozon", product=p_order,product__vendor_code__contains=vendor_code, warehouse=warehouse_obj).count()
            elif service == 'yandexmarket':
                results[vendor_code][date_] = ProductSale.objects.filter(date__date=date, company=obj, marketplace_type="yandexmarket", product=p_order,product__vendor_code__contains=vendor_code, warehouse=warehouse_obj).count()
            elif service == 'wildberries':
                results[vendor_code][date_] = ProductSale.objects.filter(date__date=date, company=obj, marketplace_type="wildberries", product=p_order,product__vendor_code__contains=vendor_code, warehouse=warehouse_obj).count()
            else:
                results[vendor_code][date_] = ProductSale.objects.filter(date__date=date, company=obj, product=p_order,product__vendor_code__contains=vendor_code, warehouse=warehouse_obj).count()
        return results

    def get_product_count(self, obj):
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', None)
        vendor_code = self.context.get('request').query_params.get('article', "")
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.date.today() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.date.today()

        if service == 'ozon':
            count = ProductSale.objects.filter(company=obj, marketplace_type="ozon",date__date__gte=date_from, date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'yandexmarket':
            count = ProductSale.objects.filter(company=obj, marketplace_type="yandexmarket",date__date__gte=date_from, date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'wildberries':
            count = ProductSale.objects.filter(company=obj, marketplace_type="wildberries",date__date__gte=date_from, date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        else:
            count = ProductSale.objects.filter(company=obj,date__date__gte=date_from, date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        return count


class CompanyOrdersSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField(read_only=True)
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ["id", "data", 'product_count']

    def get_data(self, obj):
        page = self.context.get('request').query_params.get('page', None)
        page_size = self.context.get('request').query_params.get('page_size', None)
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', None)
        vendor_code = self.context.get('request').query_params.get('article', "")
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 10
        date_from = datetime.datetime.strptime(date_from,
                                               '%Y-%m-%d').date() if date_from else datetime.date.today() - datetime.timedelta(
            days=6)

        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.date.today()

        if service == 'ozon':
            products = ProductOrder.objects.filter(company=obj, marketplace_type="ozon",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        elif service == 'yandexmarket':
            products = ProductOrder.objects.filter(company=obj, marketplace_type="yandexmarket",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        elif service == 'wildberries':
            products = ProductOrder.objects.filter(company=obj, marketplace_type="wildberries",date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        else:
            products = ProductOrder.objects.filter(company=obj,date__date__gte=date_from,date__date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
       
        products = products[(page - 1) * page_size: page * page_size]
        results = {}
        
        for product in products:
            
            p_order = product.product
            order = product
            vendor_code = product.product.vendor_code
            date_range = [(date_from + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                          for i in range((date_to - date_from).days + 1)]
            
            date = order.date.strftime("%Y-%m-%d")

            if (date_to - date_from).days == 0:
                regions = [warehouse.warehouse.region_name for warehouse in products]
                date_ = order.warehouse.region_name
                warehouse_obj= order.warehouse
                results[vendor_code] = {datee: 0 for datee in regions}
                
            else:
                date_= order.date.strftime("%Y-%m-%d")
                warehouse_obj = None
                date_range = [(date_from + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range((date_to - date_from).days + 1)]
                results[vendor_code] = {datee: 0 for datee in date_range}

            if service == 'ozon':
                results[vendor_code][date_] = ProductOrder.objects.filter(date__date=date, company=obj, marketplace_type="ozon", product=p_order,product__vendor_code__contains=vendor_code,warehouse=warehouse_obj).count()
            elif service == 'yandex':
                results[vendor_code][date_] = ProductOrder.objects.filter(date__date=date, company=obj, marketplace_type="yandex", product=p_order,product__vendor_code__contains=vendor_code,warehouse=warehouse_obj).count()
            elif service == 'wildberries':
                results[vendor_code][date_] = ProductOrder.objects.filter(date__date=date, company=obj, marketplace_type="wildberries", product=p_order,product__vendor_code__contains=vendor_code,warehouse=warehouse_obj).count()
            else:
                results[vendor_code][date_] = ProductOrder.objects.filter(date__date=date, company=obj, product=p_order,product__vendor_code__contains=vendor_code,warehouse=warehouse_obj).count()
        return results

    def get_product_count(self, obj):
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', None)
        vendor_code = self.context.get('request').query_params.get('article', "")
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.date.today() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.date.today()

        if service == 'ozon':
            count = ProductOrder.objects.filter(company=obj, marketplace_type="ozon",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'yandex':
            count = ProductOrder.objects.filter(company=obj, marketplace_type="yandex",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'wildberries':
            count = ProductOrder.objects.filter(company=obj, marketplace_type="wildberries",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        else:
            count = ProductOrder.objects.filter(company=obj,date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        return count


class CompanyStocksSerializer(serializers.Serializer):
    data = serializers.SerializerMethodField(read_only=True)
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ["id", "data", 'product_count']

    def get_data(self, obj):
        page = self.context.get('request').query_params.get('page', None)
        page_size = self.context.get('request').query_params.get('page_size', None)
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', "")
        vendor_code = self.context.get('request').query_params.get('article', "")
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 10
        
        date_from = datetime.datetime.strptime(date_from,'%Y-%m-%d').date() if date_from else datetime.datetime.now() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.datetime.now() 

        if service == 'ozon':
            products = ProductStock.objects.filter(company=obj, marketplace_type="ozon",date__gte=date_from,date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
            
        elif service == 'yandex':
            products = ProductStock.objects.filter(company=obj, marketplace_type="yandex",date__gte=date_from,date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        elif service == 'wildberries':
            products = ProductStock.objects.filter(company=obj, marketplace_type="wildberries",date__gte=date_from,date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        else:
            products = ProductStock.objects.filter(company=obj,date__gte=date_from,date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id')
        products = products[(page - 1) * page_size: page * page_size]
        results = {}
        
        for product_stock in products:
            
            product = product_stock.product
            vendor_code = product_stock.product.vendor_code

            if (date_to - date_from).days == 0:
                regions = [(warehouse.warehouse.name,warehouse.quantity) for warehouse in products]
                results[vendor_code] = {datee: quantity for datee, quantity in regions}
                
            else:
                date_range = [(date_from + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range((date_to - date_from).days + 1)]
                dc = {}
                
                for datee in date_range:
                    date_1 = datetime.datetime.strptime(datee,"%Y-%m-%d")
                    product_stock = ProductStock.objects.filter(date=datee, company=obj, product=product, marketplace_type__contains=service)
                    # print(product_stock.query)
                    if product_stock.exists():
                        quentity = product_stock.aggregate(total=Sum('quantity')).get('total',0)
                        # print((product_stock), datee)
                    else:
                        product_stock = ProductStock.objects.filter(date__lte=date_1, company=obj, product=product, marketplace_type__contains=service)
                        if product_stock.exists():
                            # print((product_stock.latest("date").date), datee)
                            date_ = product_stock.latest("date").date
                            product_stock = ProductStock.objects.filter(date=date_, company=obj, product=product, marketplace_type__contains=service)
                            quentity = product_stock.aggregate(total=Sum('quantity')).get('total',0)
                    dc[datee] = quentity
                results[vendor_code] = dc
            
        return results

    def get_product_count(self, obj):
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', None)
        vendor_code = self.context.get('request').query_params.get('article', "")
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.date.today() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.date.today()

        if service == 'ozon':
            count = ProductStock.objects.filter(company=obj, marketplace_type="ozon",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'yandex':
            count = ProductStock.objects.filter(company=obj, marketplace_type="yandex",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        elif service == 'wildberries':
            count = ProductStock.objects.filter(company=obj, marketplace_type="wildberries",date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        else:
            count = ProductStock.objects.filter(company=obj,date__gte=date_from, date__lte=date_to,product__vendor_code__contains=vendor_code).order_by("product_id").distinct('product_id').count()
        return count