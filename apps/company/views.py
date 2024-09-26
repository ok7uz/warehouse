from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from apps.product.tasks import *
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from django_celery_results.models import TaskResult

from apps.company.models import Company, CompanySettings
from apps.product.models import Recommendations, InProduction, SortingWarehouse, Shelf, WarehouseHistory, RecomamandationSupplier, PriorityShipments, \
Shipment, ShipmentHistory
from apps.company.serializers import CompanySerializer, CompanyCreateAndUpdateSerializers, CompaniesSerializers, \
    CompanySalesSerializer, CompanyOrdersSerializer, CompanyStocksSerializer, RecommendationsSerializer, \
    InProductionSerializer, InProductionUpdateSerializer, SortingWarehouseSerializer, WarehouseHistorySerializer, \
    SortingToWarehouseSeriallizer, ShelfUpdateSerializer, InventorySerializer, CreateInventorySerializer, \
    SettingsSerializer, RecomamandationSupplierSerializer, PriorityShipmentsSerializer, ShipmentSerializer,\
    ShipmentCreateSerializer, ShipmentHistorySerializer, CreateShipmentHistorySerializer, UpdatePrioritySerializer
from .tasks import update_recomendations, update_recomendation_supplier, update_priority

COMPANY_SALES_PARAMETRS = [
    OpenApiParameter('page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page number"),
    OpenApiParameter('page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page size"),
    OpenApiParameter('date_from', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date from"),
    OpenApiParameter('date_to', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date to"),
    OpenApiParameter('service', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of marketplace",enum=['wildberries', 'ozon', 'yandexmarket']),
    OpenApiParameter('sort', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Sorting",enum=['1', '-1',"A-Z","Z-A"]),
    OpenApiParameter('article', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search by article"),
]

COMPANY_WAREHOUSE_PARAMETRS = [
    OpenApiParameter('page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page number"),
    OpenApiParameter('page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page size"),
    OpenApiParameter('sort', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Sorting",enum=['1', '-1',"A-Z","Z-A"]),
    OpenApiParameter('article', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search by article"),
]

class CompanyListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CompanyCreateAndUpdateSerializers,
        description="Get all company",
        tags=['Company'],
        responses={201: CompanyCreateAndUpdateSerializers()}
    )
    def post(self, request, *args, **kwargs):
        serializer = CompanyCreateAndUpdateSerializers(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        update_wildberries_sales.delay()
        update_ozon_sales.delay()
        update_yandex_market_sales.delay()
        update_wildberries_orders.delay()
        update_ozon_orders.delay()
        update_yandex_market_orders.delay()
        update_wildberries_stocks.delay()
        update_ozon_stocks.delay()
        update_yandex_stocks.delay()


        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Get all company",
        tags=['Company'],
        responses={200: CompanySerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        companies = Company.objects.filter(owner=request.user)
        serializer = CompaniesSerializers(companies, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all company",
        tags=['Company'],
        responses={200: CompaniesSerializers}
    )
    def get(self, request, *args, **kwargs):
        company = get_object_or_404(Company, id=kwargs.get('uuid'))
        serializer = CompaniesSerializers(company, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=CompanyCreateAndUpdateSerializers,
        description="Update company",
        tags=['Company'],
        responses={200: CompanyCreateAndUpdateSerializers(many=True)}
    )
    def put(self, request, *args, **kwargs):
        company = get_object_or_404(Company, id=kwargs.get('uuid'))
        serializer = CompanyCreateAndUpdateSerializers(company, data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Delete company",
        tags=['Company'],
        responses={204: OpenApiResponse(description='No Content')}
    )
    def delete(self, request, *args, **kwargs):
        company = get_object_or_404(Company, id=kwargs.get('uuid'))
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CompanySalesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all company",
        tags=['Company'],
        responses={200: CompanySalesSerializer(many=True)},
        parameters=COMPANY_SALES_PARAMETRS
    )
    def get(self, request: Request, company_id):
        update_wildberries_sales.delay()
        update_ozon_sales.delay()
        update_yandex_market_sales.delay()
        company = get_object_or_404(Company,id=company_id)
        serializer = CompanySalesSerializer(company, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all company orders',
        tags=['Company'],
        responses={200: CompanyOrdersSerializer(many=True)},
        parameters=COMPANY_SALES_PARAMETRS
    )
    def get(self, request, company_id):
        
        update_wildberries_orders.delay()
        update_ozon_orders.delay()
        update_yandex_market_orders.delay()
        
        company = get_object_or_404(Company,id=company_id)
        serializer = CompanyOrdersSerializer(company, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyStocksView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all company stocks',
        tags=['Company'],
        responses={200: CompanyStocksSerializer(many=True)},
        parameters=COMPANY_SALES_PARAMETRS
    )
    def get(self, request, company_id):
        update_wildberries_stocks.delay()
        update_ozon_stocks.delay()
        update_yandex_stocks.delay()
        company = get_object_or_404(Company,id=company_id)
        serializer = CompanyStocksSerializer(company, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class RecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all company recommandations',
        tags=['Recomamandations'],
        responses={200: RecommendationsSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS
    )
    def get(self, request, company_id):
        
        company = get_object_or_404(Company,id=company_id)
        sort = request.query_params.get("sort","")
        article = request.query_params.get("article","")
        page_size = int(request.query_params.get("page_size",100))
        page = int(request.query_params.get("page",1))
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            recommendations = Recommendations.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_alphabit}product__vendor_code")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            recommendations = Recommendations.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_quantity}quantity")
        else:
            recommendations = Recommendations.objects.filter(company=company, product__vendor_code__contains=article)
        
        paginator = Paginator(recommendations, per_page=page_size)
        page = paginator.get_page(page)
        serializer = RecommendationsSerializer(page,many=True)
        return Response({"results": serializer.data, "product_count": len(serializer.data)}, status=status.HTTP_200_OK)

class InProductionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all company inproductions (В производстве)',
        tags=["In Productions (В производстве)"],
        responses={200: InProductionSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS
    )
    def get(self, request, company_id):
        
        company = get_object_or_404(Company,id=company_id)
        sort = request.query_params.get("sort","")
        article = request.query_params.get("article","")
        page_size = int(request.query_params.get("page_size",100))
        page = int(request.query_params.get("page",1))
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            in_production = InProduction.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_alphabit}product__vendor_code")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            in_production = InProduction.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_quantity}quantity")
        else:
            in_production = InProduction.objects.filter(company=company, product__vendor_code__contains=article)
        
        
        paginator = Paginator(in_production, per_page=page_size)
        page = paginator.get_page(page)
        serializer = InProductionSerializer(page,many=True)
        return Response({"results": serializer.data, "product_count": len(serializer.data)}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Create company inproductions (В производстве) via recomendations ids',
        tags=["In Productions (В производстве)"],
        responses={201: InProductionSerializer(),
                   200: InProductionSerializer()},
        request=InProductionSerializer,
        examples=[
        OpenApiExample(
            'Example 1',
            summary='Simple example',
            description='This is a simple example of input.',
            value={
                "recommendations_id": "uuid",
                "application_for_production": 0
            },
            request_only=True,  # Only applicable for request bodies
        ),
    ])
    def post(self,request: Request, company_id):
        data = request.data
        
        in_productions = InProduction.objects.filter(recommendations=data['recommendations_id'])
        if in_productions.exists():
            
            in_productions = in_productions.first()
            in_productions.manufacture += data['application_for_production']
            in_productions.save()
            rec = get_object_or_404(Recommendations, id=data['recommendations_id'])
            rec.quantity -= data['application_for_production']
            rec.save()
            serializer = InProductionSerializer(in_productions)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = InProductionSerializer(data=data)
        if serializer.is_valid():
            in_productions = serializer.save()
            serializer = InProductionSerializer(in_productions)
            rec = get_object_or_404(Recommendations, id=data['recommendations_id'])
            rec.quantity -= data['application_for_production']
            rec.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateInProductionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description='Update InProduction by id',
        tags=["In Productions (В производстве)"],
        responses={200: InProductionSerializer()},
        request=InProductionUpdateSerializer,
        examples=[
        OpenApiExample(
            'Example 1',
            summary='Simple example',
            description='This is a simple example of input.',
            value={
                "produced": 1
            },
            request_only=True,  # Only applicable for request bodies
        ),
    ]
    )
    def put(self, request, inproduction_id):
        
        in_production = get_object_or_404(InProduction,id=inproduction_id)
        produced = request.data.get("produced",in_production.produced)
        in_production.produced = produced
        in_production.save()
        serializer = InProductionUpdateSerializer(in_production)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    @extend_schema(
        description='Add produced from InProduction',
        tags=["In Productions (В производстве)"],
        responses={200: InProductionSerializer()},
        request=InProductionUpdateSerializer,
        examples=[
        OpenApiExample(
            'Example 1',
            summary='Simple example',
            description='This is a simple example of input.',
            value={
                "produced": 1
            },
            request_only=True,  # Only applicable for request bodies
        ),
    ]
    )

    def patch(self, request, inproduction_id):
        
        in_production = get_object_or_404(InProduction,id=inproduction_id)
        produced = request.data.get("produced",0)
        in_production.manufacture -= produced
        in_production.save()
        serializer = InProductionUpdateSerializer(in_production)
        sorting, created_s = SortingWarehouse.objects.get_or_create(company=in_production.company,product=in_production.product)
        sorting.unsorted += produced
        sorting.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
             
class SortingWarehouseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all Sorting warehouse (В производстве)',
        tags=["Sorting Warehouse (Склад сортировки)"],
        responses={200: InProductionSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS
    )
    def get(self, request, company_id):
        
        company = get_object_or_404(Company,id=company_id)
        sort = request.query_params.get("sort","")
        article = request.query_params.get("article","")
        page_size = int(request.query_params.get("page_size",100))
        page = int(request.query_params.get("page",1))
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            sorting_warehouse = SortingWarehouse.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_alphabit}product__vendor_code")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            sorting_warehouse = SortingWarehouse.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_quantity}unsorted")
        else:
            sorting_warehouse = SortingWarehouse.objects.filter(company=company, product__vendor_code__contains=article)
        
        
        paginator = Paginator(sorting_warehouse, per_page=page_size)
        page = paginator.get_page(page)
        serializer = SortingWarehouseSerializer(page,many=True)
        return Response({"results": serializer.data, "product_count": len(serializer.data)}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Sorting warehouse to Warehouse History',
        tags=["Sorting Warehouse (Склад сортировки)"],
        responses={201: SortingWarehouseSerializer()},
        request=SortingToWarehouseSeriallizer,
        )
    def post(self,request: Request, company_id):
        data = request.data
        serializer = SortingToWarehouseSeriallizer(data=data)
        if serializer.is_valid():
            in_productions = serializer.save()
            serializer = SortingWarehouseSerializer(in_productions)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WarehouseHistoryView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all company",
        tags=['Warehouse History (Склад ГП)'],
        responses={200: WarehouseHistorySerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS + [OpenApiParameter('date_from', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date from"), (OpenApiParameter('date_to', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date to"))]
    )
    def get(self, request: Request, company_id):
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        article = request.query_params.get("article","")
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        sort = request.query_params.get('sort', "")
        
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.now().date() - timedelta(days=6)
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else date_from + timedelta(days=6)

        company = get_object_or_404(Company,id=company_id)
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            sorting_warehouse = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).order_by(f"{ordering_by_alphabit}product__vendor_code").distinct("product")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            sorting_warehouse = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).order_by(f"{ordering_by_quantity}unsorted").distinct("product")
        else:
            sorting_warehouse = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).distinct("product")
        context = {"date_from": date_from, "date_to": date_to}
        
        
        paginator = Paginator(sorting_warehouse, per_page=page_size)
        page = paginator.get_page(page)
        count = paginator.count
        serializer = WarehouseHistorySerializer(page, context={'dates': context}, many=True)
        return Response({"results": serializer.data, "product_count": count}, status=status.HTTP_200_OK)
    
class UpdateShelfView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description='Update shelf (Место)',
        tags=["Shelf (Место)"],
        responses={200: ShelfUpdateSerializer()},
        request=ShelfUpdateSerializer,
    )
    def patch(self, request, shelf_id):
        data = request.data
        shelf = get_object_or_404(Shelf,id=shelf_id)
        serializer = ShelfUpdateSerializer(shelf,data=data)
        if serializer.is_valid():
            instance = serializer.save()
            history = WarehouseHistory.objects.get(shelf=instance)
            stock = instance.stock
            history.stock = stock
            history.date = datetime.now()
            history.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description='Get all company inventory (В производстве)',
        tags=["Inventory (Инвентаризация)"],
        responses={200: InProductionSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS
    )
    def get(self, request, company_id):
        
        company = get_object_or_404(Company,id=company_id)
        sort = request.query_params.get("sort","")
        article = request.query_params.get("article","")
        page_size = int(request.query_params.get("page_size",100))
        page = int(request.query_params.get("page",1))
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            in_production = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_alphabit}product__vendor_code")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            in_production = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article).order_by(f"{ordering_by_quantity}stock")
        else:
            in_production = WarehouseHistory.objects.filter(company=company, product__vendor_code__contains=article)
        paginator = Paginator(in_production, per_page=page_size)
        page = paginator.get_page(page)
        serializer = InventorySerializer(page,many=True)
        count = paginator.count
        return Response({"results": serializer.data, "product_count": count}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Add place',
        tags=["Inventory (Инвентаризация)"],
        responses={201: InventorySerializer()},
        request=CreateInventorySerializer,
        )
    
    def post(self,request: Request, company_id):
        data = request.data
        get_object_or_404(Company,id=company_id)
        get_object_or_404(Product,id=data['product_id'])
        serializer = CreateInventorySerializer(data=data, context={"company_id": company_id})
        if serializer.is_valid():
            in_productions = serializer.save()
            serializer = InventorySerializer(in_productions)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
     description='Get company settings',
    tags=["Settings"],
    responses={201: InventorySerializer()},
    request=CreateInventorySerializer,
        )
    def get(self, request: Request, company_id):
        company = get_object_or_404(Company, id=company_id)
        settings = CompanySettings.objects.get(company=company)
        serializer = SettingsSerializer(settings)
        return Response(serializer.data, status.HTTP_200_OK)
    
    @extend_schema(
    description='Update company settings last sale days and next sale days',
    tags=["Settings"],
    responses={201: SettingsSerializer()},
    request=SettingsSerializer,
        )
    def patch(self, request: Request, company_id):
        data = request.data
        company = get_object_or_404(Company, id=company_id)
        settings = CompanySettings.objects.get(company=company)
        serializer = SettingsSerializer(settings, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
class CalculationRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
    description='Calculation recommendation',
    tags=["Recomamandations"],
    responses={200: {"message": "Calculation started", "task_id": 465456}}
        )
    def get(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        task = update_recomendation_supplier.delay(company_id)
        update_recomendations.delay(company_id)
        update_priority.delay(company_id)
        return Response({"message": "Calculation started", "task_id": task.id},status.HTTP_200_OK)
    
class CheckTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
    description='Get the status of the recommendation calculation process',
    tags=["Recomamandations"],
    responses={200: {"message": "Calculation started", "task_id": 465456}}
        )
    
    def get(self, request, task_id):
        
        try:
            task_result = TaskResult.objects.get(task_id=task_id)
        except TaskResult.DoesNotExist:
            return Response({"message": "Not found task"},status.HTTP_400_BAD_REQUEST)
        return Response({"status": task_result.status, "result": task_result.result},status.HTTP_200_OK)
    
class RecomamandationSupplierView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all Recomendation Supplier",
        tags=['Recomendation Supplier (Рекомендации отгрузок)'],
        responses={200: RecomamandationSupplierSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS + [OpenApiParameter('service', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of marketplace",enum=['wildberries', 'ozon', 'yandexmarket'])]
    )
    def get(self, request: Request, company_id):
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        article = request.query_params.get("article","")
        sort = request.query_params.get('sort', "")
        service = request.query_params.get('service', "")

        company = get_object_or_404(Company,id=company_id)
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            supplier = RecomamandationSupplier.objects.filter(company=company, product__vendor_code__contains=article,marketplace_type__icontains=service).order_by(f"{ordering_by_alphabit}product__vendor_code").distinct("product")
        else:
            supplier = RecomamandationSupplier.objects.filter(company=company, product__vendor_code__contains=article,marketplace_type__icontains=service).distinct("product")
        context = {"market": service}
        
        paginator = Paginator(supplier, per_page=page_size)
        page = paginator.get_page(page)
        count = paginator.count
        serializer = RecomamandationSupplierSerializer(page, context=context, many=True)
        if sort and sort in ["-1", "1"]:
            ordering_by_quantity = False if sort =="-1" else True
            data = sorted(serializer.data,key=lambda item: sum(d['quantity'] for d in item['data']), reverse=ordering_by_quantity)
        else:
            data = serializer.data
        return Response({"results": data, "product_count": count}, status=status.HTTP_200_OK)

COMPANY_PRIORITY_PARAMETRS = [
    OpenApiParameter('page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page number"),
    OpenApiParameter('page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page size"),
    OpenApiParameter('sort', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Sorting",enum=['travel_days', '-travel_days',"A-Z","Z-A",'arrive_days', '-arrive_days','sales', '-sales','shipments', '-shipments','sales_share', '-sales_share','shipments_share', '-shipments_share','shipping_priority', '-shipping_priority']),
    OpenApiParameter('region_name', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search by article"),
]

class PriorityShipmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all Priority Shipments",
        tags=['Priority Shipments (Приоритет отгрузок)'],
        responses={200: PriorityShipmentsSerializer(many=True)},
        parameters=COMPANY_PRIORITY_PARAMETRS + [OpenApiParameter('service', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of marketplace",enum=['wildberries', 'ozon', 'yandexmarket'])]
    )
    def get(self, request: Request, company_id):
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        warehouse = request.query_params.get("region_name","")
        sort = request.query_params.get('sort', "")
        service = request.query_params.get('service', "")

        company = get_object_or_404(Company,id=company_id)
        
        if sort and sort in ["Z-A", "A-Z"]:
            
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{ordering_by_alphabit}warehouse__region_name")
            
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{ordering_by_alphabit}warehouse__oblast_okrug_name")

        elif sort and "travel_days" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "arrive_days" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}arrive_days")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "sales" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}sales")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "shipments" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}shipments")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "sales_share" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}sales_share")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "shipments_share" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}shipments_share")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        elif sort and "shipping_priority" in sort:
            reverse = "-" if "-" in sort  else ""
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}shipping_priority")
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse,marketplace_type__icontains=service).order_by(f"{reverse}travel_days")
        else:
            priority = PriorityShipments.objects.filter(company=company, warehouse__region_name__contains=warehouse,marketplace_type__icontains=service)
            if not priority.exists():
                priority = PriorityShipments.objects.filter(company=company, warehouse__oblast_okrug_name__contains=warehouse)
        
        paginator = Paginator(priority, per_page=page_size)
        page_obj = paginator.get_page(page)
        serializer = PriorityShipmentsSerializer(page_obj, many=True)
        count = paginator.count
        return Response({"results": serializer.data, "product_count": count}, status=status.HTTP_200_OK)
    
class ShipmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Get all Shipments",
        tags=['Shipments (Отгрузок)'],
        responses={200: PriorityShipmentsSerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS + [OpenApiParameter('service', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of marketplace",enum=['wildberries', 'ozon', 'yandexmarket'])]
    )
    def get(self, request, company_id):

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))
        article = request.query_params.get("article","")
        sort = request.query_params.get('sort', "")

        company = get_object_or_404(Company,id=company_id)
        if sort in ["A-Z", "Z-A"]:
            sort = "-" if sort=="Z-A" else ""
            shipments = Shipment.objects.filter(company=company,product__vendor_code__contains=article).order_by(f"{sort}product__vendor_code")
        elif sort in ["-1", "1"]:
            sort = "-" if sort=="-1" else ""
            shipments = Shipment.objects.filter(company=company,product__vendor_code__contains=article).order_by(f"{sort}shipment")
        else:
            shipments = Shipment.objects.filter(company=company,product__vendor_code__contains=article)
        
        
        paginator = Paginator(shipments, per_page=page_size)
        page = paginator.get_page(page)
        count = paginator.count
        serializer = ShipmentSerializer(page, many=True)
        return Response({"results": serializer.data, "product_count": count}, status=status.HTTP_200_OK)

    @extend_schema(
        description="Recomendation Supplier to Shipment",
        tags=['Shipments (Отгрузок)'],
        responses={200: PriorityShipmentsSerializer(many=True)},
        request=ShipmentCreateSerializer,
    )
    def post(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        data  = request.data
        serializer = ShipmentCreateSerializer(data=data)
        
        if serializer.is_valid():
            shipment = serializer.save()
            serializer = ShipmentSerializer(shipment, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShipmentHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get all Shipment History",
        tags=['Shipment History (История отгрузок)'],
        responses={200: ShipmentHistorySerializer(many=True)},
        parameters=COMPANY_WAREHOUSE_PARAMETRS + [OpenApiParameter('date_from', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date from"), (OpenApiParameter('date_to', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date to"))]
    )
    def get(self, request: Request, company_id):
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        article = request.query_params.get("article","")
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        sort = request.query_params.get('sort', "")
        
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else datetime.now().date() - timedelta(days=6)
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else date_from + timedelta(days=7)

        company = get_object_or_404(Company,id=company_id)
        
        if sort and sort in ["Z-A", "A-Z"]:
            ordering_by_alphabit = "-" if sort =="Z-A" else ""
            sorting_warehouse = ShipmentHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).order_by(f"{ordering_by_alphabit}product__vendor_code").distinct("product")
        elif sort and sort in ["-1", "1"]:
            ordering_by_quantity = "-" if sort =="-1" else ""
            sorting_warehouse = ShipmentHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).order_by(f"{ordering_by_quantity}quantity").distinct("product")
        else:
            sorting_warehouse = ShipmentHistory.objects.filter(company=company, product__vendor_code__contains=article,date__gte=date_from, date__lte=date_to).distinct("product")
            print(sorting_warehouse)
        context = {"date_from": date_from, "date_to": date_to}
        
        
        paginator = Paginator(sorting_warehouse, per_page=page_size)
        page = paginator.get_page(page)
        count = paginator.count
        serializer = ShipmentHistorySerializer(page, context={'dates': context}, many=True)
        return Response({"results": serializer.data, "product_count": count}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description="Shipment to Shipment History",
        tags=['Shipment History (История отгрузок)'],
        responses={201: ShipmentHistorySerializer(many=True)},
        request=CreateShipmentHistorySerializer,
    )
    def post(self, request, company_id):
        data = request.data
        serializer = CreateShipmentHistorySerializer(data=data)
        if serializer.is_valid():
            ship_his = serializer.save()
            return Response({"message": "success saved"}, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class ChangeRegionTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        description="Update Priority Shipment",
        tags=['Priority Shipments (Приоритет отгрузок)'],
        responses={200: PriorityShipmentsSerializer()},
        request=UpdatePrioritySerializer,
    )
    def patch(self, request, priority_id):
        priority = get_object_or_404(PriorityShipments, id=priority_id)
        data = request.data
        serializer = UpdatePrioritySerializer(instance=priority, data=data)
        if serializer.is_valid():
            priority = serializer.save()
            serializer = PriorityShipmentsSerializer(priority)
            return Response(serializer.data,status.HTTP_200_OK)
        return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)