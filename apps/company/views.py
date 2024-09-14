from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from apps.product.tasks import *
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.company.models import Company
from apps.product.models import Recommendations, InProduction, SortingWarehouse, Shelf, WarehouseHistory
from apps.company.serializers import CompanySerializer, CompanyCreateAndUpdateSerializers, CompaniesSerializers, \
    CompanySalesSerializer, CompanyOrdersSerializer, CompanyStocksSerializer, RecommendationsSerializer, \
    InProductionSerializer, InProductionUpdateSerializer, SortingWarehouseSerializer, WarehouseHistorySerializer, \
    SortingToWarehouseSeriallizer, ShelfUpdateSerializer, InventorySerializer, CreateInventorySerializer
    

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
        
        serializer = RecommendationsSerializer(recommendations,many=True)
        paginator = Paginator(serializer.data, per_page=page_size)
        page = paginator.get_page(page)
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
        
        serializer = InProductionSerializer(in_production,many=True)
        paginator = Paginator(serializer.data, per_page=page_size)
        page = paginator.get_page(page)
        return Response({"results": serializer.data, "product_count": len(serializer.data)}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Create company inproductions (В производстве) via recomendations ids',
        tags=["In Productions (В производстве)"],
        responses={201: InProductionSerializer(many=True)},
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
        serializer = InProductionSerializer(data=data)
        if serializer.is_valid():
            in_productions = serializer.save()
            serializer = InProductionSerializer(in_productions)
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
        in_production.produced += produced
        in_production.save()
        serializer = InProductionUpdateSerializer(in_production)
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
        
        serializer = SortingWarehouseSerializer(sorting_warehouse,many=True)
        paginator = Paginator(serializer.data, per_page=page_size)
        page = paginator.get_page(page)
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
        serializer = WarehouseHistorySerializer(sorting_warehouse, context={'dates': context}, many=True)
        
        paginator = Paginator(serializer.data, per_page=page_size)
        page = paginator.get_page(page)
        count = paginator.count
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
            serializer.save()
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
        
        serializer = InventorySerializer(in_production,many=True)
        paginator = Paginator(serializer.data, per_page=page_size)
        page = paginator.get_page(page)
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
        get_object_or_404(Product,vendor_code=data['vendor_code'])
        serializer = CreateInventorySerializer(data=data, context={"company_id": company_id})
        if serializer.is_valid():
            in_productions = serializer.save()
            serializer = InventorySerializer(in_productions)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)