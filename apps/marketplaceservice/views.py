from concurrent.futures import ThreadPoolExecutor

from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.products.api.ozon import *

from datetime import datetime, timedelta

import requests
import json
import aiohttp
import asyncio


class SalesView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Sales",
        tags=['Sales'],
        manual_parameters=[
            openapi.Parameter(
                'data_from', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)", type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'data_to', openapi.IN_QUERY, description="End date (YYYY-MM-DD)", type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        data_from = request.query_params.get('data_from')
        data_to = request.query_params.get('data_to')

        try:
            if data_from and data_to:
                date_from = datetime.strptime(data_from, '%Y-%m-%d')
                date_to = datetime.strptime(data_to, '%Y-%m-%d')
            else:
                today = datetime.today()
                date_from = today - timedelta(days=7)
                date_to = today
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        get_sales = loop.run_until_complete(process_data(date_from, date_to))
        return Response(get_sales)


class SalesOfCountriesView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Sales",
        tags=['Sales'],
        manual_parameters=[
            openapi.Parameter(
                'date_format', openapi.IN_QUERY, description="Enter date (YYYY-MM-DD)", type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
        ],
    )
    async def get(self, request, *args, **kwargs):
        date_format = request.query_params.get('date_format')

        try:
            date_format = datetime.datetime.strptime(date_format, '%Y-%m-%d')
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        get_sales = await sync_to_async(process_data)(date_format, date_format)
        analytics_stock_on_warehouses = await sync_to_async(process_data2)(get_sales)

        return Response({'sales_data': get_sales, 'stock_data': analytics_stock_on_warehouses})
