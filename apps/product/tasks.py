from json import dumps
from time import sleep

import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.db.models import F
from apps.marketplaceservice.models import Ozon, Wildberries, YandexMarket
from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse
from config.celery import app

date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

wildberries_orders_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={date_from}T00:00:00'
wildberries_stocks_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={date_from}T00:00:00'
ozon_sales_url = 'https://api-seller.ozon.ru/v1/analytics/data'
ozon_product_info_url = 'https://api-seller.ozon.ru/v2/product/info'
yandex_market_sales_url = 'https://api.partner.market.yandex.ru/reports/shows-sales/generate?format=CSV'
yandex_report_url = 'https://api.partner.market.yandex.ru/reports/info/{report_id}'

@app.task
def update_wildberries_sales():

    for wildberries in Wildberries.objects.all():
        
        wb_api_key = wildberries.wb_api_key
        company = wildberries.company
        try:
            latest_product_sale = ProductSale.objects.filter(marketplace_type="wildberries").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            latest_product_sale = False
        if not latest_product_sale:
            latest_product_sale = (datetime.now()-timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%S')
        wildberries_sales_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={latest_product_sale}'
        response = requests.get(wildberries_sales_url, headers={'Authorization': f'{wb_api_key}'})
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                
                warehouse, created = Warehouse.objects.get_or_create(
                    name = item['warehouseName'],
                    country_name = item['countryName'],
                    oblast_okrug_name = item['oblastOkrugName'],
                    region_name = item['regionName']
                )

                wildberries = wildberries
                warehouse = warehouse
                try:
                    product, _ = Product.objects.get_or_create(vendor_code=item['supplierArticle'])
                    date = datetime.strptime(item['date'],"%Y-%m-%dT%H:%M:%S")
                    product_sale, created_sale= ProductSale.objects.get_or_create(
                        product=product,
                        company=company,
                        date=date,
                        marketplace_type="wildberries",
                        warehouse=warehouse
                    )
                except:
                    pass
                
        else:
            return response.text
        return "Success"


@app.task
def update_wildberries_orders():
    for wildberries in Wildberries.objects.all():
        
        wb_api_key = wildberries.wb_api_key
        company = wildberries.company
        try:
            latest_product_sale = ProductOrder.objects.filter(marketplace_type="wildberries").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            latest_product_sale = False
        if not latest_product_sale:
            latest_product_sale = date_from
        wildberries_sales_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={latest_product_sale}'
        response = requests.get(wildberries_sales_url, headers={'Authorization': f'{wb_api_key}'})
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                
                warehouse, created = Warehouse.objects.get_or_create(
                    name = item['warehouseName'],
                    country_name = item['countryName'],
                    oblast_okrug_name = item['oblastOkrugName'],
                    region_name = item['regionName']
                )

                wildberries = wildberries
                warehouse = warehouse
                try:
                    product, _ = Product.objects.get_or_create(vendor_code=item['supplierArticle'])
                    date = datetime.strptime(item['date'],"%Y-%m-%dT%H:%M:%S")
                    product_order, created_sale= ProductOrder.objects.get_or_create(
                        product=product,
                        company=company,
                        date=date,
                        marketplace_type="wildberries",
                        warehouse=warehouse
                    )
                except:
                    pass
                
        else:
            return response.text
        return "Success"


@app.task
def update_wildberries_stocks():
    for wildberries in Wildberries.objects.all():
        wb_api_key = wildberries.wb_api_key
        response = requests.get(wildberries_stocks_url, headers={'Authorization': f'Bearer {wb_api_key}'})

        for item in response.json():
            vendor_code = item['supplierArticle']
            warehouse = item['warehouseName']
            quantity = item['quantityFull']
            product, _ = Product.objects.get_or_create(vendor_code=vendor_code)
            product_stock, _ = ProductStock.objects.get_or_create(
                product=product,
                company=wildberries.company,
                warehouse=warehouse
            )
            product_stock.wildberries_quantity = quantity
            product_stock.save()


def get_paid_orders(url, headers, date_from, status="delivered"):
    data = {
        "dir": "asc",
        "filter": {
            "status": status,
            "financial_status": "paid",
            "since": date_from,
            "to": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "limit": 1000,  # Ko'proq natija olish uchun limitni oshiring
        "offset": 0,
        "with": {
            "analytics_data": True,
            "financial_data": True
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('result', [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []
    
@app.task
def update_ozon_sales():
    
    FBO_URL = "https://api-seller.ozon.ru/v2/posting/fbo/list"
    FBS_URL = "https://api-seller.ozon.ru/v2/posting/fbs/list"
    try:
        date_from = ProductSale.objects.filter(marketplace_type="ozon").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S')
    except:
        date_from = False
    if not date_from:
        date_from = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for ozon in Ozon.objects.all():
        company = ozon.company
        api_token = ozon.api_token
        client_id = ozon.client_id
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_token,
            'Content-Type': 'application/json'
        }

        fbo_orders = get_paid_orders(FBO_URL,headers,date_from)
        fbs_orders = get_paid_orders(FBS_URL,headers,date_from)
        results = fbo_orders + fbs_orders

        for item in results:
            
            date = item['in_process_at']
            sku = item['products'][0]['offer_id']
            
            if "warehouse_name" in item["analytics_data"].keys():
                warehouse_name = item["analytics_data"]['warehouse_name']
            
            warehouse_name = ""
            oblast_okrug_name = item["analytics_data"]['region']
            region_name = item["analytics_data"]['city']

            product, created_p = Product.objects.get_or_create(vendor_code=sku)
            warehouse, created_w = Warehouse.objects.get_or_create(
                name = warehouse_name,
                country_name = "Russia",
                oblast_okrug_name = oblast_okrug_name,
                region_name = region_name
            )
            try:
                product_sale = ProductSale.objects.get_or_create(
                    product=product,
                    company=company,
                    date=date,
                    warehouse=warehouse,
                    marketplace_type = "ozon"
                )
            except Exception:
                pass

@app.task
def update_ozon_orders():
    
    FBO_URL = "https://api-seller.ozon.ru/v2/posting/fbo/list"
    FBS_URL = "https://api-seller.ozon.ru/v2/posting/fbs/list"
    try:
        date_from = ProductOrder.objects.filter(marketplace_type="ozon").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S')
    except:
        date_from = False
    if not date_from:
        date_from = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for ozon in Ozon.objects.all():
        company = ozon.company
        api_token = ozon.api_token
        client_id = ozon.client_id
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_token,
            'Content-Type': 'application/json'
        }

        fbo_orders = get_paid_orders(FBO_URL,headers,date_from,"awaiting_packaging")
        fbs_orders = get_paid_orders(FBS_URL,headers,date_from, "awaiting_deliver")
        results = fbo_orders + fbs_orders

        for item in results:
            
            date = item['in_process_at']
            sku = item['products'][0]['offer_id']
            
            if "warehouse_name" in item["analytics_data"].keys():
                warehouse_name = item["analytics_data"]['warehouse_name']
            
            warehouse_name = ""
            oblast_okrug_name = item["analytics_data"]['region']
            region_name = item["analytics_data"]['city']

            product, created_p = Product.objects.get_or_create(vendor_code=sku)
            warehouse, created_w = Warehouse.objects.get_or_create(
                name = warehouse_name,
                country_name = "Russia",
                oblast_okrug_name = oblast_okrug_name,
                region_name = region_name
            )
            try:
                product_sale = ProductOrder.objects.get_or_create(
                    product=product,
                    company=company,
                    date=date,
                    warehouse=warehouse,
                    marketplace_type = "ozon"
                )
            except Exception:
                pass

def get_yandex_orders(api_key, date_from, client_id, status="DELIVERED"):
    date_to = datetime.now().strftime("%d-%m-%Y")
    url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&supplierShipmentDateFrom=&supplierShipmentDateTo=&updatedAtFrom=&updatedAtTo=&dispatchType=&fake=&hasCis=&onlyWaitingForCancellationApprove=&onlyEstimatedDelivery=&buyerType=&page=&pageSize="
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
                }
    
    difrence = (datetime.now() - datetime.strptime(date_from,"%d-%m-%Y")).days
    if difrence == 365:
        orders = []
        months = [
    ("2024-01-01", "2024-01-31"),  
    ("2024-02-01", "2024-02-29"),  
    ("2024-03-01", "2024-03-31"),  
    ("2024-04-01", "2024-04-30"),  
    ("2024-05-01", "2024-05-31"),  
    ("2024-06-01", "2024-06-30"),  
    ("2024-07-01", "2024-07-31"),  
    ("2024-08-01", "2024-08-31"),  
    ("2024-09-01", "2024-09-30"),  
    ("2024-10-01", "2024-10-31"),  
    ("2024-11-01", "2024-11-30"),  
    ("2024-12-01", "2024-12-31")   
    ]
        
        for date_from, date_to in months:
            
            url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&supplierShipmentDateFrom=&supplierShipmentDateTo=&updatedAtFrom=&updatedAtTo=&dispatchType=&fake=&hasCis=&onlyWaitingForCancellationApprove=&onlyEstimatedDelivery=&buyerType=&page=&pageSize="
            response = requests.get(url, headers=headers).json()["orders"]
            with open("orders.json", "w") as f:
                import json
                f.write(json.dumps(response,indent=4))
            orders += response
    
    else:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            orders = response.json()['orders']
            return orders
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    return orders

@app.task
def update_yandex_market_sales():
    
    for yandex_market in YandexMarket.objects.all():
        api_key_bearer = yandex_market.api_key_bearer
        fby_campaign_id = yandex_market.fby_campaign_id
        fbs_campaign_id = yandex_market.fbs_campaign_id
        company = yandex_market.company
        date_from = ProductSale.objects.filter(marketplace_type="yandexmarket")

        if not (date_from or date_from.exists()):
            date_from = (datetime.now()-timedelta(days=365)).strftime("%d-%m-%Y")
        else:
            date_from =date_from.latest("date").date.strftime("%d-%m-%Y")

        results1 = get_yandex_orders(api_key_bearer, date_from,client_id=fby_campaign_id)
        results2 = get_yandex_orders(api_key_bearer, date_from,client_id=fbs_campaign_id)

        results = results1 + results2

        for item in results:
            buyer_total = item.get("buyerTotal",0)
            item_total = item.get("itemsTotal",0)

            if buyer_total == item_total:
                if "serviceName" in item["delivery"].keys():
                    warehouse_name = item["delivery"]['serviceName']
            
                warehouse_name = ""
                oblast_okrug_name = item["delivery"]['region']['parent']['name']
                region_name = item["delivery"]['region']['name']
                try:
                    country_name = item.get('delivery', {}).get('address', {}).get('country', "")
                except:
                    country_name = "Russia"

                warehouse, created_w = Warehouse.objects.get_or_create(
                    name = warehouse_name,
                    country_name = country_name,
                    oblast_okrug_name = oblast_okrug_name,
                    region_name = region_name
                )
                
                products = item["items"]
                date = datetime.strptime(item['updatedAt'],"%d-%m-%Y %H:%M:%S")
                
                for product in products:
                    vendor_code = product["offerId"]
                    product_obj, created_p = Product.objects.get_or_create(vendor_code=vendor_code)
                    product_s = ProductSale.objects.get_or_create(
                        product=product_obj,
                        company=company,
                        date=date,
                        warehouse=warehouse,
                        marketplace_type="yandexmarket"
                    )

                    date = date + timedelta(seconds=1)
    return "succes"
                    
@app.task
def update_yandex_market_orders():
    
    for yandex_market in YandexMarket.objects.all():
        api_key_bearer = yandex_market.api_key_bearer
        fby_campaign_id = yandex_market.fby_campaign_id
        fbs_campaign_id = yandex_market.fbs_campaign_id
        company = yandex_market.company
        date_from = ProductOrder.objects.filter(marketplace_type="yandexmarket")

        if not (date_from or date_from.exists()):
            date_from = (datetime.now()-timedelta(days=365)).strftime("%d-%m-%Y")
        else:
            date_from =date_from.latest("date").date.strftime("%d-%m-%Y")

        results1 = get_yandex_orders(api_key_bearer, date_from,client_id=fby_campaign_id,status="PROCESSING")
        results2 = get_yandex_orders(api_key_bearer, date_from,client_id=fbs_campaign_id,status="PROCESSING")

        results = results1 + results2

        for item in results:
            buyer_total = item.get("buyerTotal",0)
            item_total = item.get("itemsTotal",0)

            if buyer_total == item_total:
                if "serviceName" in item["delivery"].keys():
                    warehouse_name = item["delivery"]['serviceName']
            
                warehouse_name = ""
                oblast_okrug_name = item["delivery"]['region']['parent']['name']
                region_name = item["delivery"]['region']['name']
                try:
                    country_name = item.get('delivery', {}).get('address', {}).get('country', "")
                except:
                    country_name = "Russia"

                warehouse, created_w = Warehouse.objects.get_or_create(
                    name = warehouse_name,
                    country_name = country_name,
                    oblast_okrug_name = oblast_okrug_name,
                    region_name = region_name
                )
                
                products = item["items"]
                date = datetime.strptime(item['updatedAt'],"%d-%m-%Y %H:%M:%S")
                
                for product in products:
                    vendor_code = product["offerId"]
                    product_obj, created_p = Product.objects.get_or_create(vendor_code=vendor_code)
                    product_s = ProductOrder.objects.get_or_create(
                        product=product_obj,
                        company=company,
                        date=date,
                        warehouse=warehouse,
                        marketplace_type="yandexmarket"
                    )

                    date = date + timedelta(seconds=1)
    return "succes"
                    
                
                    
