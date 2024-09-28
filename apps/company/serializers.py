import datetime

from django.db.models import Sum, Count, Max

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.db import transaction

from apps.accounts.models import CustomUser
from apps.company.models import Company, CompanySettings
from apps.marketplaceservice.models import Wildberries, Ozon, YandexMarket
from apps.product.models import ProductStock, ProductSale, ProductOrder, WarehouseForStock, Recommendations, \
        InProduction, SortingWarehouse, Shelf, WarehouseHistory, Product, RecomamandationSupplier, PriorityShipments, \
        Shipment, ShipmentHistory
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
        CompanySettings.objects.create(last_sale_days=30,next_sale_days=100,company=company)
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
    application_for_production = serializers.IntegerField()

    class Meta:
        model = Recommendations
        fields = ["id", "product","quantity", "days_left","succes_quantity"]

    def get_product(self, instance):
        return instance.product.vendor_code
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["application_for_production"] = 0
        return rep

class InProductionSerializer(serializers.Serializer):
    
    id = serializers.UUIDField(required=False)   
    product = serializers.SerializerMethodField(required=False)
    application_for_production = serializers.IntegerField()
    produced = serializers.IntegerField(required=False)
    recommendations_id = serializers.UUIDField()

    class Meta:
        model = InProduction
        fields = ["id", "product","manufacture", "produced"]

    def to_representation(self, instance:InProduction):
        dc = {
            "id": instance.pk,
            "product": instance.product.vendor_code,
            "manufacture": instance.manufacture,
            "produced": instance.produced
        }
        return dc

    
    def validate_recommendations_id(self, value):
        
        errors = []
        print(value)
        if not Recommendations.objects.filter(id=value).exists():
            errors.append(f" Not found is Recommendations with UUID : {value}")
        if errors:
            raise serializers.ValidationError(errors)
        return value
    
    def create(self, validated_data):
    
        recommendations = Recommendations.objects.get(id=validated_data["recommendations_id"])
        
        company = recommendations.company
        product = recommendations.product
        application_for_production = validated_data['application_for_production']
        
        production = InProduction.objects.create(company=company,product=product, manufacture=application_for_production,recommendations=recommendations)
        recommendations.application_for_production += application_for_production
        recommendations.save()
        return production

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
    shelf = serializers.SerializerMethodField()

    class Meta:
        model = SortingWarehouse
        fields = ['id', 'product', 'unsorted', 'shelf']
    
    def get_product(self, obj: SortingWarehouse):
        return obj.product.vendor_code
    
    def get_shelf(self, obj):
        shelfs = Shelf.objects.filter(product=obj.product)
        dc = []
        for shelf in shelfs:
            pk = shelf.pk
            name = shelf.shelf_name
            stock = shelf.stock
            dc.append({"id": pk,"shelf_name":name,"stock": stock})
        return dc
    
class WarehouseHistorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    class Meta:
        model = WarehouseHistory
        fields = ["product","data"]

    def get_product(self,obj):
        return obj.product.vendor_code
    
    def get_data(self, obj):
        
        dates = self.context.get("dates")
        date_from = dates.get("date_from")
        date_to = dates.get("date_to")
        date_range = [date_from + datetime.timedelta(days=x) for x in range((date_to - date_from).days + 1)]
        dc = {date.strftime("%Y-%m-%d"): 0 for date in date_range}
        results = {}
        shelfs = WarehouseHistory.objects.filter(product=obj.product)
        for shelf in shelfs:
            if shelf.shelf:
                name = shelf.shelf.shelf_name
            else:
                name = "-"
            results[name] = dc
        for shelf in shelfs:
            if shelf.shelf:
                name = shelf.shelf.shelf_name
            else:
                name = "-"
            for date in date_range:
                total = WarehouseHistory.objects.filter(product=obj.product, date=date, company=obj.company, shelf=shelf.shelf).aggregate(total=Sum("stock")).get("total",0)
                if total:
                    results[name][date.strftime("%Y-%m-%d")] = total
                else:
                    results[name][date.strftime("%Y-%m-%d")] = 0
        
        return results

class ValidateDict(serializers.Serializer):
    sorting_warehouse_id = serializers.IntegerField()
    stock = serializers.IntegerField()

    def validate(self, attrs):
        if not ("sorting_warehouse_id" in attrs.keys() and "stock" in attrs.keys()):
                raise serializers.ValidationError("must be sorting_warehouse_id and stock")
        return attrs

class SortingToWarehouseSeriallizer(serializers.ModelSerializer):

    class Meta:
        model = SortingWarehouse
        fields = ['sorting_warehouse_id', 'stock', 'shelf_name']
    
    sorting_warehouse_id = serializers.IntegerField()
    stock = serializers.IntegerField()
    shelf_name = serializers.CharField()
    
    def validate(self, data):

        sorting_warehouse_id = data.get('sorting_warehouse_id')
        stock = data.get('stock')

        if not SortingWarehouse.objects.filter(id=sorting_warehouse_id).exists():
            raise serializers.ValidationError(f"Not found SortingWarehouse with ID: {sorting_warehouse_id}")

        warehouse = SortingWarehouse.objects.get(id=sorting_warehouse_id)
        if warehouse.unsorted < stock:
            raise serializers.ValidationError("The unsorted stock quantity in the warehouse must be greater than or equal to the stock quantity you want to allocate.")

        return data

    
    def create(self, validated_data):
        
        data = validated_data
        sorting_warehouse_id = data['sorting_warehouse_id']
        stock = data['stock']
        shelf_name = validated_data['shelf_name']
        sorting_warehouse = SortingWarehouse.objects.get(id=sorting_warehouse_id)
        company = sorting_warehouse.company
        product = sorting_warehouse.product
        sorting_warehouse.unsorted -= stock
        sorting_warehouse.save()

        shelf, created = Shelf.objects.get_or_create(shelf_name=shelf_name,product=product,company=company)
        
        shelf.stock += stock
        shelf.save()
        history, created = WarehouseHistory.objects.get_or_create(shelf=shelf,product=product,company=company)
        history.stock += stock
        history.save()

        
        return sorting_warehouse

class ShelfUpdateSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    shelf_name = serializers.CharField()
    stock = serializers.IntegerField()

    class Meta:
        model = Shelf
        fields = ['product','shelf_name','stock']

    def update(self, instance: Shelf, validated_data):
        
        try:
            product = Product.objects.get(vendor_code=validated_data['product'])
        except:
            product = instance.product
        shelf_name = validated_data.get("shelf_name",instance.shelf_name)
        stock = validated_data.get("stock", instance.stock)
        
        instance.shelf_name = shelf_name
        instance.stock = stock
        instance.product = product
        instance.save()
        
        return instance
    
    def get_product(self,obj):
        return obj.product.vendor_code
    
class InventorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    shelfs = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    total_fact = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseHistory
        fields = ['product','shelfs','total','total_fact']

    def get_product(self,obj):
        return {"vendor_code":obj.product.vendor_code,"product_id": obj.product.pk}
    
    def get_shelfs(self,obj):
        shelfs = Shelf.objects.filter(product=obj.product,company=obj.company).values("id","shelf_name","stock")
        return shelfs
    
    def get_total(self,obj):
        total = Shelf.objects.filter(product=obj.product).aggregate(total=Sum("stock"))['total']
        if not total:
            total = 0
        return total
    
    def get_total_fact(self,obj):
        total = WarehouseHistory.objects.filter(product=obj.product).aggregate(total=Sum("stock"))['total']
        if not total:
            total = 0
        return total

class CreateInventorySerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    shelf_name = serializers.CharField()
    stock = serializers.IntegerField()
    
    def create(self, validated_data):
        with transaction.atomic():
            product_id = validated_data['product_id']
            company_id = self.context['company_id']
            shelf_name = validated_data['shelf_name']
            stock = validated_data['stock']
            
            product = Product.objects.get(id=product_id)
            company = Company.objects.get(id=company_id)

            shelf, created = Shelf.objects.get_or_create(shelf_name=shelf_name,product=product,company=company)      
            shelf.stock += stock
            shelf.save()

            warehouse_history, created = WarehouseHistory.objects.get_or_create(company=company,product=product,shelf=shelf)
            warehouse_history.stock += stock
            warehouse_history.save()

            return warehouse_history

class CreateInventoryWithBarcodeSerializer(serializers.Serializer):
    barcode = serializers.CharField()
    shelf_name = serializers.CharField()
    stock = serializers.IntegerField()

    def validate_barcode(self, value):
        product = Product.objects.filter(barcode=value)
        if not product.exists():
            raise serializers.ValidationError("Not product with barcode")
        return value
    
    def create(self, validated_data):
        with transaction.atomic():
            barcode = validated_data['barcode']
            company_id = self.context['company_id']
            shelf_name = validated_data['shelf_name']
            stock = validated_data['stock']
            
            product = Product.objects.filter(id=barcode)
            if product.filter(marketplace_type="wildberries"):
                product = product.filter(marketplace_type="wildberries").first()
            else:
                product = product.first()
            company = Company.objects.get(id=company_id)

            shelf, created = Shelf.objects.get_or_create(shelf_name=shelf_name,product=product,company=company)      
            shelf.stock += stock
            shelf.save()

            warehouse_history, created = WarehouseHistory.objects.get_or_create(company=company,product=product,shelf=shelf)
            warehouse_history.stock += stock
            warehouse_history.save()

            return warehouse_history

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=CompanySettings
        fields = ["last_sale_days","next_sale_days"]
        
class RecomamandationSupplierSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    is_red = serializers.SerializerMethodField()

    class Meta:
        model = RecomamandationSupplier
        fields = ["id",'product', 'data', "is_red"]

    def get_product(self, obj):
        return obj.product.vendor_code

    def get_data(self, obj):
        product = obj.product
        market = self.context.get("market")
        result = RecomamandationSupplier.objects.filter(product=product, marketplace_type__icontains=market).select_related('warehouse').values('warehouse__region_name','days_left','quantity','warehouse__oblast_okrug_name')
        return [{
            "region_name": item["warehouse__region_name"] or item["warehouse__oblast_okrug_name"],
            "quantity": item["quantity"],
            "days_left": item["quantity"]
        } for item in result]

    def get_is_red(self, obj):
        
        market = self.context.get("market")
        product = obj.product
        rec = RecomamandationSupplier.objects.filter(product=product, marketplace_type__icontains=market).aggregate(total=Sum("quantity"))
        rec = rec['total'] or 0
        warehouse_s = WarehouseHistory.objects.filter(product=product).aggregate(total=Sum("stock"))
        warehouse_s = warehouse_s["total"] or 0
        return rec > warehouse_s

class PriorityShipmentsSerializer(serializers.ModelSerializer):
    region_name = serializers.SerializerMethodField()
    class Meta:
        model = PriorityShipments
        fields = ["id", "region_name", "travel_days","arrive_days", "sales", "sales_share","shipments_share","shipping_priority"]

    def get_region_name(self, obj):
        return obj.warehouse.region_name or obj.warehouse.oblast_okrug_name
    
class ShipmentSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    in_warehouse = serializers.SerializerMethodField()
    in_shelf = serializers.SerializerMethodField()
    shipment = serializers.IntegerField()

    class Meta:
        model = Shipment
        fields = ['id',"product", "in_shelf", 'in_warehouse', 'shipment']

    def get_product(self,obj):
        return obj.product.vendor_code
    
    def get_in_warehouse(self,obj):
        product = obj.product
        company = obj.company
        in_warehouse = WarehouseHistory.objects.filter(product=product, company=company)
        
        if in_warehouse.exists():
            in_warehouse = in_warehouse.aggregate(total=Sum("stock"))['total']
            return in_warehouse
        return 0
    
    def get_in_shelf(self,obj):
        product = obj.product
        company = obj.company
        in_shelf = Shelf.objects.filter(product=product, company=company).values("id","shelf_name","stock")
        
        return in_shelf
    
class ShipmentCreateSerializer(serializers.Serializer):
    recomamandation_supplier_ids = serializers.ListField(child=serializers.UUIDField())

    def validate(self, data):

        recomamandation_supplier_ids = data.get('recomamandation_supplier_ids')
        ls = []
        for item in recomamandation_supplier_ids:
            if not RecomamandationSupplier.objects.filter(id=item).exists():
                ls.append(f"Not found Recomamandation Supplier with UUID: {item}")
        if ls:
            raise serializers.ValidationError(ls)
        return data
    
    def create(self, validated_data):
        
        recomamandation_supplier_ids = validated_data['recomamandation_supplier_ids']
        recomamandation_supplier = RecomamandationSupplier.objects.filter(id__in=recomamandation_supplier_ids).values("id","product","company")
        shipment = []
        
        for item in recomamandation_supplier:
            product = item['product']
            rec_sup = item['id']
            company = item['company']
            total = RecomamandationSupplier.objects.filter(product=product,company=company).aggregate(total=Sum("quantity"))['total']
            
            shipment.append(Shipment(recomamand_supplier_id=rec_sup,product_id=product,shipment=total,company_id=company))

        return Shipment.objects.bulk_create(shipment,ignore_conflicts=True)

class ShipmentHistorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = ShipmentHistory
        fields = ['product','data']

    def get_product(self,obj):
        return obj.product.vendor_code
    
    def get_data(self, obj):
        
        dates = self.context.get("dates")
        date_from = dates.get("date_from")
        date_to = dates.get("date_to")
        date_range = [date_from + datetime.timedelta(days=x) for x in range((date_to - date_from).days + 1)][:-1]
        dc = {date.strftime("%Y-%m-%d"): 0 for date in date_range}

        for date in date_range:
            dc[date.strftime("%Y-%m-%d")] = ShipmentHistory.objects.filter(date__date=date, company=obj.company, product=obj.product).aggregate(total=Sum('quantity'))['total'] or 0
        
        return dc
    
class CreateShipmentHistorySerializer(serializers.Serializer):
    shelf_ids = serializers.ListField(child=serializers.UUIDField())
    shipment_id = serializers.IntegerField()

    def validate(self, attrs):
        
        shipment = Shipment.objects.filter(id=attrs['shipment_id'])
        if not shipment.exists():
            raise serializers.ValidationError(f"Not fount shipment with: {attrs['shipment_id']}")
        
        shelf_ids = attrs['shelf_ids']
        errors = []
        for item in shelf_ids:
            shelf = Shelf.objects.filter(id=item)
            if not shelf.exists():
                errors.append(f"Not fount shipment with: {item}")
        if errors:
            raise serializers.ValidationError(errors)
        product = shipment.first().product
        stock = WarehouseHistory.objects.filter(product=product).aggregate(total=Sum("stock"))['total'] or 0
        
        if stock < shipment.first().shipment:
            raise serializers.ValidationError("Insufficient stock available for the shipment")
        
        shelfs = Shelf.objects.filter(id__in=attrs['shelf_ids']).order_by("stock")
        ship_t = shipment.first().shipment
        if shelfs.aggregate(total=Sum("stock"))["total"] < ship_t:
            raise serializers.ValidationError("There is not enough product on the shelfs")
        
        return attrs
    
    def create(self, validated_data):
        
        shipment = Shipment.objects.get(id=validated_data['shipment_id'])
        company = shipment.company
        product = shipment.product
        shelfs = Shelf.objects.filter(id__in=validated_data['shelf_ids']).order_by("stock")
        ship_t = shipment.shipment
        
        for shelf_stock in shelfs:
            if shelf_stock.stock >= ship_t:
                shelf_stock.stock -= ship_t
                shelf_stock.save()
                shipment_history = ShipmentHistory.objects.create(company=company,product=product,quantity=ship_t)
                warehouse_history = WarehouseHistory.objects.create(product=product, company=company, date=datetime.datetime.now(),stock=-ship_t, shelf=shelf_stock)
                shipment.delete()
                break
            else:
                shipment.shipment -= shelf_stock.stock
                shipment.save()
                warehouse_history = WarehouseHistory.objects.create(product=product, company=company, date=datetime.datetime.now(),stock=-ship_t, shelf=shelf_stock)
                shelf_stock.delete()

        return shipment

class UpdatePrioritySerializer(serializers.Serializer):
    travel_days = serializers.IntegerField()
    arrive_days = serializers.IntegerField()

    def update(self, instance: PriorityShipments, validated_data):
        arrive_days = validated_data['arrive_days']
        travel_days = validated_data['travel_days']
        instance.travel_days = travel_days
        instance.arrive_days = arrive_days
        instance.save()
        return instance