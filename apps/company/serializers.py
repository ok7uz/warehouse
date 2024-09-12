import datetime

from django.db.models import Sum, Count, Max
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.accounts.models import CustomUser
from apps.company.models import Company
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket
from apps.product.models import ProductStock, ProductSale, ProductOrder, WarehouseForStock, Recommendations, \
        InProduction, SortingWarehouse, Shelf, WarhouseHistory
from django.core.paginator import Paginator

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
        
        page = int(self.context.get('request').query_params.get('page', 1))
        page_size = int(self.context.get('request').query_params.get('page_size', 10))
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', "")
        sort = self.context.get('request').query_params.get('sort', "")
        vendor_code = self.context.get('request').query_params.get('article', "")

        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.datetime.now().date() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.datetime.now().date()

        filters = {
            'company': obj,
            'date__date__gte': date_from,
            'date__date__lte': date_to,
            'product__vendor_code__icontains': vendor_code
        }
        if service:
            filters['marketplace_type__icontains'] = service
        if vendor_code:
            filters['product__vendor_code__icontains'] = vendor_code
        ordering_by_alpabit = "-" if sort =="Z-A" else ""
        queryset = ProductSale.objects.filter(**filters).order_by(f"{ordering_by_alpabit}product__vendor_code")

        date_range = [date_from + datetime.timedelta(days=x) for x in range((date_to - date_from).days + 1)]
        results = {}

        if (date_to - date_from).days == 0:
            date = date_from
            date_range = queryset.values("warehouse")
            for warehouse in date_range:
                day_sales = queryset.filter(date__date=date, warehouse=warehouse).values('product__vendor_code').annotate(total_sales=Count('id'))
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {warehouse.region_name if warehouse.region_name else warehouse.oblast_okrug_name: 0 for date in date_range}
                    results[product_code][warehouse.region_name if warehouse.region_name else warehouse.oblast_okrug_name] = sale['total_sales']
        
        else:
            for date in date_range:
                day_sales = queryset.filter(date__date=date).values('product__vendor_code').annotate(total_sales=Count('id'))
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
                    results[product_code][date.strftime('%Y-%m-%d')] = sale['total_sales']
        if sort.isnumeric():  
            sort = 0 if sort =="-1" else 1      
            results = dict(sorted(results.items(), key=lambda item: sum(item[1].values()), reverse=bool(int(sort))))
        paginator = Paginator(list(results.items()),page_size)
        page = paginator.get_page(page)
        return page

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
        
        page = int(self.context.get('request').query_params.get('page', 1))
        page_size = int(self.context.get('request').query_params.get('page_size', 10))
        date_from = self.context.get('request').query_params.get('date_from', None)
        date_to = self.context.get('request').query_params.get('date_to', None)
        service = self.context.get('request').query_params.get('service', "")
        sort = self.context.get('request').query_params.get('sort', "")
        vendor_code = self.context.get('request').query_params.get('article', "")

        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.datetime.now().date() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.datetime.now().date()

        filters = {
            'company': obj,
            'date__date__gte': date_from,
            'date__date__lte': date_to,
            'product__vendor_code__icontains': vendor_code
        }
        if service:
            filters['marketplace_type__icontains'] = service
        if vendor_code:
            filters['product__vendor_code__icontains'] = vendor_code
        ordering_by_alpabit = "-" if sort =="Z-A" else ""
        queryset = ProductOrder.objects.filter(**filters).order_by(f"{ordering_by_alpabit}product__vendor_code")

        date_range = [date_from + datetime.timedelta(days=x) for x in range((date_to - date_from).days + 1)]
        results = {}

        if (date_to - date_from).days == 0:
            date = date_from
            date_range = queryset.values("warehouse")
            for warehouse in date_range:
                day_sales = queryset.filter(date__date=date, warehouse=warehouse).values('product__vendor_code').annotate(total_sales=Count('id'))
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {warehouse.region_name if warehouse.region_name else warehouse.oblast_okrug_name: 0 for date in date_range}
                    results[product_code][warehouse.region_name if warehouse.region_name else warehouse.oblast_okrug_name] = sale['total_sales']
        
        else:
            for date in date_range:
                day_sales = queryset.filter(date__date=date).values('product__vendor_code').annotate(total_sales=Count('id'))
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
                    results[product_code][date.strftime('%Y-%m-%d')] = sale['total_sales']
        if sort.isnumeric():  
            sort = 0 if sort =="-1" else 1      
            results = dict(sorted(results.items(), key=lambda item: sum(item[1].values()), reverse=bool(int(sort))))
        paginator = Paginator(list(results.items()),page_size)
        page = paginator.get_page(page)
        return page


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
        request = self.context.get('request')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        service = request.query_params.get('service', "")
        vendor_code = request.query_params.get('article', "")
        sort = self.context.get('request').query_params.get('sort', "")

        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.datetime.now().date() - datetime.timedelta(days=6)
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.datetime.now().date()

        filters = {
            'company': obj,
            'date__gte': date_from,
            'date__lte': date_to
        }
        if service:
            filters['marketplace_type__icontains'] = service
        if vendor_code:
            filters['product__vendor_code__icontains'] = vendor_code
        ordering_by_alphabit = "-" if sort =="Z-A" else ""
        queryset = ProductStock.objects.filter(**filters).select_related('warehouse').order_by(f"{ordering_by_alphabit}product__vendor_code")
        
        date_range = [date_from + datetime.timedelta(days=x) for x in range((date_to - date_from).days + 1)]
        results = {}

        if (date_from - date_to).days == 0:
            date_range = queryset.values_list("warehouse", flat=True)
            date_range = WarehouseForStock.objects.filter(id__in=set(date_range))
            for warehouse in date_range:
                date=date_from
                day_sales = queryset.filter(date=date, warehouse=warehouse).values('product__vendor_code').annotate(total_sales=Sum('quantity'))
                if not day_sales:

                    last_available_date = queryset.filter(date__lt=date, warehouse=warehouse).aggregate(last_date=Max('date'))['last_date']
                    if last_available_date:
                        day_sales = queryset.filter(date=last_available_date, warehouse=warehouse).values('product__vendor_code').annotate(total_sales=Sum('quantity'))
                
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {warehouse.name: 0 for warehouse in date_range}
                    results[product_code][warehouse.name] = sale['total_sales']
        else:
            for date in date_range:
                day_sales = queryset.filter(date=date).values('product__vendor_code').annotate(total_sales=Sum('quantity'))
                if not day_sales:
                    # Get the most recent data before the specified date if no data exists for this day
                    last_available_date = queryset.filter(date__lt=date).aggregate(last_date=Max('date'))['last_date']
                    if last_available_date:
                        day_sales = queryset.filter(date=last_available_date).values('product__vendor_code').annotate(total_sales=Sum('quantity'))
                
                for sale in day_sales:
                    product_code = sale['product__vendor_code']
                    if product_code not in results:
                        results[product_code] = {day.strftime('%Y-%m-%d'): 0 for day in date_range}
                    results[product_code][date.strftime('%Y-%m-%d')] = sale['total_sales']
        if sort.isnumeric():  
            sort = 0 if sort =="-1" else 1      
            results = dict(sorted(results.items(), key=lambda item: sum(item[1].values()), reverse=bool(int(sort))))
        paginator = Paginator(list(results.items()), page_size)
        page_obj = paginator.get_page(page)
        return page_obj

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
    
class RecommendationsSerializer(serializers.Serializer):
    id = serializers.UUIDField()   
    product = serializers.SerializerMethodField()
    quantity = serializers.IntegerField()
    days_left = serializers.IntegerField()
    succes_quantity = serializers.IntegerField()

    class Meta:
        model = Recommendations
        fields = ["id", "product","quantity", "days_left","succes_quantity"]

    def get_product(self, instance):
        return instance.product.vendor_code

class InProductionSerializer(serializers.Serializer):
    
    id = serializers.UUIDField(required=False)   
    product = serializers.SerializerMethodField(required=False)
    manufacture = serializers.IntegerField(required=False)
    produced = serializers.IntegerField(required=False)
    recommendations_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)

    class Meta:
        model = InProduction
        fields = ["id", "product","manufacture", "produced"]

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = super().to_representation(instance)  # Call the super method to get the default serialization
        ret.pop('recommendations_ids', None)  # Remove recommendations_ids from the response
        return ret

    def get_product(self, instance):
        return instance.product.vendor_code
    
    def validate_recommendations_ids(self, value):
        errors = []
        for uuid in value:
            if not Recommendations.objects.filter(id=uuid).exists():
                errors.append(f" Not found is Recommendations with UUID : {uuid}")
        if errors:
            raise serializers.ValidationError(errors)
        return value
    
    def create(self, validated_data):
        
        ls = []
        recommendations = Recommendations.objects.filter(id__in=validated_data["recommendations_ids"])
        for rec in recommendations:
            company = rec.company
            product = rec.product
            quantity = rec.quantity
            ls.append(InProduction(company=company,product=product,manufacture=quantity,recommendations=rec))
        try:
            in_production = InProduction.objects.bulk_create(ls,ignore_conflicts=True)
        except Exception as errors:
            raise serializers.ValidationError(errors)
        return in_production

class InProductionUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)   
    product = serializers.SerializerMethodField(required=False)
    manufacture = serializers.IntegerField(required=False)
    produced = serializers.IntegerField()

    class Meta:
        model = InProduction
        fields = ["id", "product","manufacture", "produced"]

    def get_product(self, instance):
        return instance.product.vendor_code
    
class SortingWarehouseSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    unsorted = serializers.IntegerField()

    class Meta:
        model = SortingWarehouse
        fields = ['id', 'product', 'unsorted']
    
    def get_product(self, obj):
        return obj.product.vendor_code