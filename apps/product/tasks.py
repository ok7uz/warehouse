from json import dumps
import requests
from datetime import datetime, timedelta
from celery import shared_task

from apps.company.models import Company
from apps.marketplaceservice.models import Ozon, Wildberries
from apps.product.models import Product, ProductSale

date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
wildberries_sales_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={date_from}T00:00:00'
ozon_sales_url = 'https://api-seller.ozon.ru/v1/analytics/data'
ozon_product_info_url = 'https://api-seller.ozon.ru/v2/product/info'


@shared_task
def update_wildberries_sales():
    for wildberries in Wildberries.objects.all():
        wb_api_key = wildberries.wb_api_key
        response = requests.get(wildberries_sales_url, headers={'Authorization': f'Bearer {wb_api_key}'})
        data = {}

        for item in response.json():
            date = item['date'][:10]
            vendor_code = item['supplierArticle']
            if vendor_code not in data:
                data[vendor_code] = {}
                if date not in data[vendor_code]:
                    data[vendor_code][date] = 1
                else:
                    data[vendor_code][date] += 1
            else:
                if date not in data[vendor_code]:
                    data[vendor_code][date] = 1
                else:
                    data[vendor_code][date] += 1
        for vendor_code, p_data in data.items():
            product, _ = Product.objects.get_or_create(vendor_code=vendor_code)

            for date, quantity in p_data.items():
                product_sale, _ = ProductSale.objects.get_or_create(product=product, company=wildberries.company, date=date)
                product_sale.wildberries_quantity = quantity
                product_sale.save()    

def get_product_vendor_code(sku, api_token, client_id):
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_token,
        'Content-Type': 'application/json'
    }
    payload = dumps({"sku": sku})
    response = requests.post(ozon_product_info_url, headers=headers, data=payload)
    return response.json()['result']['offer_id']


@shared_task
def update_ozon_sales():
    date_to = datetime.now().strftime('%Y-%m-%d')
    for ozon in Ozon.objects.all():
        api_token = ozon.api_token
        client_id = ozon.client_id
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_token,
            'Content-Type': 'application/json'
        }
        payload = dumps({
            "date_from": date_from,
            "date_to": date_to,
            "metrics": [
                "revenue",
                "ordered_units",
            ],
            "dimension": [
                "sku",
                'day'
            ],
            "filters": [],
            "sort": [
                {
                    "key": "revenue",
                    "order": "DESC"
                }
            ],
            "limit": 1000,
            "offset": 0
        })

        response = requests.post(ozon_sales_url, headers=headers, data=payload)
        results = response.json()['result']['data']
        data = {}

        for item in results:
            date = item['dimensions'][1]['id']
            sku = item['dimensions'][0]['id']
            if sku not in data:
                data[sku] = {}
                if date not in data[sku]:
                    data[sku][date] = 1
                else:
                    data[sku][date] += 1
            else:
                if date not in data[sku]:
                    data[sku][date] = 1
                else:
                    data[sku][date] += 1

        for sku, p_data in data.items():
            product = Product.objects.filter(ozon_sku=sku).first()
            if not product:
                vendor_code = get_product_vendor_code(sku, api_token, client_id)
                product, _ = Product.objects.get_or_create(vendor_code=vendor_code)
                product.ozon_sku = sku
                product.save()

            for date, quantity in p_data.items():
                product_sale, _ = ProductSale.objects.get_or_create(product=product, company=ozon.company, date=date)
                product_sale.ozon_quantity = quantity
                product_sale.save() 
