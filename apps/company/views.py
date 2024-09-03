from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from apps.product.tasks import *
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.company.models import Company
from apps.company.serializers import CompanySerializer, CompanyCreateAndUpdateSerializers, CompaniesSerializers, \
    CompanySalesSerializer, CompanyOrdersSerializer, CompanyStocksSerializer

COMPANY_SALES_PARAMETRS = [
    OpenApiParameter('page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page number"),
    OpenApiParameter('page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Page size"),
    OpenApiParameter('date_from', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date from"),
    OpenApiParameter('date_to', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Date to"),
    OpenApiParameter('service', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of marketplace",enum=['wildberries', 'ozon', 'yandexmarket']),
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
