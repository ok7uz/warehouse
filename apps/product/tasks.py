import calendar
import time
import asyncio

import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.db.models import F
from apps.marketplaceservice.models import Ozon, Wildberries, YandexMarket
from apps.product.models import Product, ProductSale, ProductOrder, ProductStock, Warehouse, WarehouseForStock, Claster, \
      WarehouseYandex, WarehouseOzon
from config.celery import app
from apps.company.location.get_warehouse_name_from_yandex import get_location_info
from celery_once import QueueOnce

date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

wildberries_orders_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={date_from}T00:00:00'
wildberries_stocks_url = f'https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={date_from}T00:00:00'
ozon_sales_url = 'https://api-seller.ozon.ru/v1/analytics/data'
ozon_product_info_url = 'https://api-seller.ozon.ru/v2/product/info'
yandex_market_sales_url = 'https://api.partner.market.yandex.ru/reports/shows-sales/generate?format=CSV'
yandex_report_url = 'https://api.partner.market.yandex.ru/reports/info/{report_id}'

async def get_warehouse_data( api_key):
    headers = {
        "Authorization": api_key
    }
    response = requests.get("https://supplies-api.wildberries.ru/api/v1/warehouses", headers=headers)
    return response.json()

def not_official_api_wildberries(nmId, api_key):
    
    response = requests.get(f"https://card.wb.ru/cards/detail?dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&nm={nmId}")
    result = []
    if response.status_code == 200:
        products = response.json()['data']['products']
        for item in products:
            for item2 in item["sizes"]:
                for item3 in item2['stocks']:
                    result.append(item3)
    return result

@app.task(base=QueueOnce, once={'graceful': True})
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
                    oblast_okrug_name = item['oblastOkrugName']
                )

                wildberries = wildberries
                warehouse = warehouse
                barcode = item["barcode"]

                product = Product.objects.filter(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries")
                if product.exists():
                    product = product.first()
                else:
                    product, _ = Product.objects.get_or_create(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries")
                date = datetime.strptime(item['date'],"%Y-%m-%dT%H:%M:%S")
                try:
                    product_sale, created_sale= ProductSale.objects.get_or_create(
                        product=product,
                        company=company,
                        date=date,
                        marketplace_type="wildberries",
                        warehouse=warehouse
                    )
                except:
                    continue
        else:
            return response.text
        return "Success"

@app.task(base=QueueOnce, once={'graceful': True})
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
                    oblast_okrug_name = item['oblastOkrugName']
                )

                wildberries = wildberries
                warehouse = warehouse
                barcode = item['barcode']
                product = Product.objects.filter(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries")
                if product.exists():
                    product = product.first()
                else:
                    product, _ = Product.objects.get_or_create(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries")
                date = datetime.strptime(item['date'],"%Y-%m-%dT%H:%M:%S")
                product_order, created_sale= ProductOrder.objects.get_or_create(
                    product=product,
                    company=company,
                    date=date,
                    marketplace_type="wildberries",
                    warehouse=warehouse
                )
                
        else:
            return response.text
        return "Success"

@app.task(base=QueueOnce, once={'graceful': True})
def update_wildberries_stocks():
    # Saqlash uchun kerakli ma'lumotlarni vaqtinchalik saqlash
    product_stocks_to_create = []
    
    for wildberries in Wildberries.objects.all():
        wb_api_key = wildberries.wb_api_key
        response = requests.get(wildberries_stocks_url, headers={'Authorization': f'Bearer {wb_api_key}'})
        
        warehouse_data = asyncio.run(get_warehouse_data(wb_api_key))
        
        for item in response.json():
            company = wildberries.company
            date = datetime.now()

            barcode = item.get('barcode')
            if not barcode:
                continue
            
            product = Product.objects.filter(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries").first()
            if not product:
                product, _ = Product.objects.get_or_create(vendor_code=item['supplierArticle'], barcode=barcode, marketplace_type="wildberries")

            result_w = not_official_api_wildberries(api_key=wb_api_key, nmId=item['nmId'])
            for item_not_official in result_w:
                quantity = item_not_official['qty']

                warehouse_name = next((wh['name'] for wh in warehouse_data if item_not_official['wh'] == wh['ID']), None)
                if not warehouse_name:
                    continue

                warehouse_obj, created_w = WarehouseForStock.objects.get_or_create(name=warehouse_name, marketplace_type="wildberries")
                
                product_stocks_to_create.append(ProductStock(
                    product=product,
                    warehouse=warehouse_obj,
                    marketplace_type="wildberries",
                    company=company,
                    date=date,
                    quantity=quantity
                ))
    
    ProductStock.objects.bulk_create(product_stocks_to_create, batch_size=100, ignore_conflicts=True)

    return "Success"

            
def get_paid_orders(url, headers, date_from, status="delivered",status_2="paid"):
    
    data = {
        "dir": "asc",
        "filter": {
            "status": status,
            "since": date_from,
            "to": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        },
        "limit": 1000,  
        "offset": 0,
        "with": {
            "analytics_data": True,
            "financial_data": True
        }
    }
    results = []
    response = requests.post(url, headers=headers, json=data)
    
    while response.json().get('result', False):
        results += response.json().get('result', [])
        data['offset'] += 1000
        response = requests.post(url, headers=headers, json=data)
    
    return results


def get_barcode(vendor_code, api_key, client_id):
    body = {"offer_id": vendor_code}
    headers = {
        "Api-Key":api_key,
        "Client-Id": client_id,
        'Content-Type': 'application/json'
    }
    # try:
    response = requests.post("https://api-seller.ozon.ru/v2/product/info",json=body, headers=headers)
    # except:
        # print(f"body: {body} headers: {headers}")
    
    if response.status_code == 200:
        return response.json()["result"]["barcode"]
    return 0 

@app.task(base=QueueOnce, once={'graceful': True})
def update_ozon_sales():
    
    FBO_URL = "https://api-seller.ozon.ru/v2/posting/fbo/list"
    FBS_URL = "https://api-seller.ozon.ru/v2/posting/fbs/list"
    
    for ozon in Ozon.objects.all():
        company = ozon.company
        api_token = ozon.api_token
        client_id = ozon.client_id
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_token,
            'Content-Type': 'application/json'
        }

        try:
            date_from = ProductSale.objects.filter(marketplace_type="ozon").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            date_from = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
        fbo_orders = get_paid_orders(FBO_URL,headers,date_from)
        fbs_orders = get_paid_orders(FBS_URL,headers,date_from)
        results = fbo_orders + fbs_orders

        for item in results:
           
            try:
                date = datetime.strptime(item['in_process_at'],"%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                date = datetime.strptime(item['in_process_at'],"%Y-%m-%dT%H:%M:%SZ")
            sku = item['products'][0]['offer_id']
            
            oblast_okrug_name = item["financial_data"]['cluster_to']
            warehouse_name = WarehouseOzon.objects.filter(claster_to=oblast_okrug_name).first()
            
            if warehouse_name:
                warehouse_name = warehouse_name.warehouse_name
            else:
                continue

            barcode = get_barcode(vendor_code=sku, api_key=ozon.api_token,client_id=ozon.client_id)
            if not barcode:
                continue
            
            product = Product.objects.filter(barcode=barcode)
            warehouse, created_w = Warehouse.objects.get_or_create(
                name = warehouse_name,
                oblast_okrug_name = oblast_okrug_name
            )

            if product.exists():
                
                wildberries_product = product.filter(marketplace_type="wildberries")
                if wildberries_product.exists():
                    W_product = wildberries_product.first()
                else:
                    W_product = False
                
                ozon_product = product.filter(marketplace_type='ozon')
                if ozon_product.exists():
                        ozon_product = ozon_product.first()
                else:
                    ozon_product = False
                
                if (not ozon_product) and (not W_product):
                    product = Product.objects.create(vendor_code=sku, marketplace_type="ozon", barcode=barcode)
                    product_sale_o = ProductSale.objects.create(product=product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    continue
                
                elif ozon_product and W_product:
                    product_sale_w = ProductSale.objects.filter(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    product_sale_o = ProductSale.objects.filter(product=ozon_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    
                    if product_sale_w.exists():
                        continue
                    
                    elif product_sale_o.exists():
                        product_sale_o = product_sale_o.first()
                        product_sale_o.product = W_product
                        product_sale_o.save()
                        continue
                    
                    else:
                        try:
                            product_sale_o = ProductSale.objects.create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                        except:
                            continue
                
                elif ozon_product and (not W_product):
                    product_sale_o = ProductSale.objects.get_or_create(product=ozon_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                
                elif W_product and (not ozon_product):
                    product_sale_o = ProductSale.objects.get_or_create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
            
            else:
                product, created_p = Product.objects.get_or_create(vendor_code=sku, marketplace_type="ozon", barcode=barcode)
            
                if not ProductSale.objects.filter(
                    product=product,
                    company=company,
                    date=date,
                    warehouse=warehouse,
                    marketplace_type = "ozon"
                ).exists():
                    try:
                        product_sale = ProductSale.objects.create(
                            product=product,
                            company=company,
                            date=date,
                            warehouse=warehouse,
                            marketplace_type = "ozon"
                        )
                    except:
                        continue
                 
@app.task(base=QueueOnce, once={'graceful': True})
def update_ozon_orders():
    
    FBO_URL = "https://api-seller.ozon.ru/v2/posting/fbo/list"
    FBS_URL = "https://api-seller.ozon.ru/v2/posting/fbs/list"
    
    try:
        date_from = ProductOrder.objects.filter(marketplace_type="ozon").latest('date').date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        date_from = False
    if not date_from:
        date_from = (datetime.now()-timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    for ozon in Ozon.objects.all():
        company = ozon.company
        api_token = ozon.api_token
        client_id = ozon.client_id
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_token,
            'Content-Type': 'application/json'
        }

        fbo_orders = get_paid_orders(FBO_URL,headers,date_from,"", "")
        fbs_orders = get_paid_orders(FBS_URL,headers,date_from, "","")
        
        results = fbo_orders + fbs_orders 
        for item in results:
            
            date = item['created_at']
            try:
                date = datetime.strptime(date,"%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                date = datetime.strptime(date,"%Y-%m-%dT%H:%M:%SZ")
            sku = item['products'][0]['offer_id']
            
            oblast_okrug_name = item["financial_data"]['cluster_to']

            warehouse_name = WarehouseOzon.objects.filter(claster_to=oblast_okrug_name).first()
            if warehouse_name:
                warehouse_name = warehouse_name.warehouse_name
            else:
                continue

            barcode = get_barcode(vendor_code=sku, api_key=ozon.api_token,client_id=ozon.client_id)
            if not barcode:
                continue
            
            product = Product.objects.filter(barcode=barcode)
            warehouse, created_w = Warehouse.objects.get_or_create(
                name = warehouse_name,
                oblast_okrug_name = oblast_okrug_name
            )
            
            if product.exists():
                
                wildberries_product = product.filter(marketplace_type="wildberries")
                if wildberries_product.exists():
                    W_product = wildberries_product.first()
                else:
                    W_product = False
                
                ozon_product = product.filter(marketplace_type='ozon')
                if ozon_product.exists():
                        ozon_product = ozon_product.first()
                else:
                    ozon_product = False
                
                if (not ozon_product) and (not W_product):
                    product = Product.objects.create(vendor_code=sku, marketplace_type="ozon", barcode=barcode)
                    try:
                        product_sale_o = ProductOrder.objects.create(product=product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    except:
                        continue
                    continue
                
                elif ozon_product and W_product:
                    product_sale_w = ProductOrder.objects.filter(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    product_sale_o = ProductOrder.objects.filter(product=ozon_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    
                    if product_sale_w.exists():
                        continue
                    
                    elif product_sale_o.exists():
                        product_sale_o = product_sale_o.first()
                        product_sale_o.product = W_product
                        product_sale_o.save()
                        continue
                    
                    else:
                        try:
                            product_sale_o = ProductOrder.objects.create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                        except:
                            continue
                
                elif ozon_product and (not W_product):
                    try:
                        product_sale_o = ProductOrder.objects.get_or_create(product=ozon_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
                    except:
                        continue

                elif W_product and (not ozon_product):
                    product_sale_o = ProductOrder.objects.get_or_create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="ozon")
            else:
                product, created_p = Product.objects.get_or_create(vendor_code=sku, marketplace_type="ozon", barcode=barcode)
            
                if not ProductOrder.objects.filter(
                    product=product,
                    company=company,
                    date=date,
                    warehouse=warehouse,
                    marketplace_type = "ozon"
                ).exists():
                    product_sale = ProductOrder.objects.create(
                        product=product,
                        company=company,
                        date=date,
                        warehouse=warehouse,
                        marketplace_type = "ozon"
                    )
            
@app.task(base=QueueOnce, once={'graceful': True})
def update_ozon_stocks():
    
    for ozon in Ozon.objects.all():
        api_key = ozon.api_token
        client_id = ozon.client_id
        
        headers = {
            'Client-Id': client_id,
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        company = ozon.company
        url = "https://api-seller.ozon.ru/v2/analytics/stock_on_warehouses"
        data = {
        "limit": 1000,
        "offset": 0,
        "warehouse_type": "ALL"
        }
        response = requests.post(url, headers=headers, json=data)
        
        results = []
        while response.status_code == 200 and response.json()['result']["rows"]:
            results += response.json()['result']["rows"]
            data['offset'] += 1000
            response = requests.post(url, headers=headers, json=data)
            
        for item in results:
            
            vendor_code = item['item_code']
            warehouse_name = item['warehouse_name']
            quantity = item['free_to_sell_amount']
            
            date = datetime.now()
            
            barcode = get_barcode(vendor_code=vendor_code, api_key=ozon.api_token,client_id=ozon.client_id)
            if not barcode:
                continue
            product = Product.objects.filter(barcode=barcode)
            warehouse = WarehouseForStock.objects.filter(name=warehouse_name, marketplace_type="ozon").first()
            if not warehouse:
                warehouse = WarehouseForStock.objects.create(name=warehouse_name, marketplace_type="ozon")
            
            if not product.exists():
                product, created_s = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type='ozon')
            
            elif product.filter(marketplace_type='ozon').exists():
                
                product_o = product.filter(marketplace_type='ozon').first()
                if product.filter(marketplace_type="wildberries").exists():
                    
                    vendor_code = product.filter(marketplace_type="wildberries").first().vendor_code
                    if product_o.vendor_code != vendor_code:
                        product_o.vendor_code = vendor_code
                        product_o.save()
                product = product_o
            
            else:
                product, created = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type='ozon')

            product_stock, created_s = ProductStock.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                date=date,
                company=company,
                marketplace_type='ozon'
            )
            
            product_stock.quantity = quantity
            product_stock.save()
    return "Succes"

def get_yandex_orders(api_key, date_from, client_id, status="DELIVERED", limit=1000):
    # print("working get_yandex_orders")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
                }
    
    difrence = (datetime.now() - datetime.strptime(date_from,"%Y-%m-%d")).days
    
    if difrence >= 200:
        orders = []
        months = []
        
        start_year = (datetime.now() - timedelta(days=365)).year
        start_month = (datetime.now() - timedelta(days=365)).month

        for month in range(start_month, 13):
            year = start_year
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            months.append((first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')))

        current_year = datetime.now().year
        for month in range(1, datetime.now().month + 1):
            year = current_year
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            months.append((first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')))

        # print(months)  
        
        for date_from, date_to in months:
            # print("working for cicle")
            url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&limit={limit}"
            # print(url)
            response = requests.get(url, headers=headers)
            # print(response.status_code)
            
            orders += response.json()["orders"]
            while 'paging' in response.json().keys() and 'nextPageToken' in response.json()['paging']:
                
                page_token = response.json()['paging']['nextPageToken']
                url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&limit={limit}&page_token={page_token}"
                response = requests.get(url, headers=headers)
                # print(response.status_code)
                if response.status_code == 200:
                    orders += response.json()["orders"]   
    else:
        
        date_to = datetime.now().strftime('%Y-%m-%d')
        url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&limit={limit}"
        orders = []
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
           
            orders += response.json()['orders']
            while 'paging' in response.json().keys() and 'nextPageToken' in response.json()['paging']:
                
                page_token = response.json()['paging']['nextPageToken']
                url = f"https://api.partner.market.yandex.ru/campaigns/{client_id}/orders?orderIds=&status={status}&substatus=&fromDate={date_from}&toDate={date_to}&limit={limit}&page_token={page_token}"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    orders += response.json()["orders"]
            # print(len(orders))
            return orders
        else:
            
            return []
    # print(len(orders))
    return orders

def find_republic_name(region):

    if  "REPUBLIC" == region.get("type", ""):
        return region.get("name")
    
    parent = region.get("parent")
    if parent:
        return find_republic_name(parent)
    
    return None

def find_barcode(vendor_code, company_id, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    body = {
         
        "offerIds": [vendor_code]
    }
    params = {
        'limit': 10,  #
        'page_token': None
    }
    response = requests.post(f"https://api.partner.market.yandex.ru/businesses/{company_id}/offer-mappings",headers=headers,json=body,params=params)
    if response.status_code == 200:
        try:
            return response.json()["result"]['offerMappings'][0]["offer"]["barcodes"][0]
        except:
            return 0
    else: 
        return 0
        
@app.task(base=QueueOnce, once={'graceful': True})
def update_yandex_market_sales():
    # print("working here")
    for yandex_market in YandexMarket.objects.all():
        # print("working here")
        api_key_bearer = yandex_market.api_key_bearer
        fby_campaign_id = yandex_market.fby_campaign_id
        fbs_campaign_id = yandex_market.fbs_campaign_id
        company = yandex_market.company
        
        date_from = ProductSale.objects.filter(marketplace_type="yandexmarket")
        # print(date_from)
        if not date_from.exists():
            date_from = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d")
        else:
            date_from =date_from.latest("date").date.strftime("%Y-%m-%d")
        # print(date_from)
        
        results1 = get_yandex_orders(api_key_bearer, date_from,client_id=fby_campaign_id)
        results2 = get_yandex_orders(api_key_bearer, date_from,client_id=fbs_campaign_id)
        
        results = results1 + results2
        # print(len(results))
        for item in results:
            # print(item['status'])
            if item['status'] != "DELIVERED":
                continue
            
            buyer_total = item.get("buyerTotal",0)
            item_total = item.get("itemsTotal",0)

            if buyer_total == item_total:
                
                oblast_okrug_name = find_republic_name(item["delivery"]['region'])
                if not oblast_okrug_name:
                    continue

                claster_to = Claster.objects.filter(region_name=oblast_okrug_name).first()
                if not claster_to:
                    oblast_okrug_name = find_republic_name(item["delivery"]['region'])
                else:
                    oblast_okrug_name = claster_to.claster_to
                warehouse, created_w = Warehouse.objects.get_or_create(
                    name = oblast_okrug_name,
                    oblast_okrug_name = oblast_okrug_name
                )
                
                products = item["items"]
                date = datetime.strptime(item['updatedAt'],"%d-%m-%Y %H:%M:%S")
                
                for product in products:
                    
                    vendor_code = product["offerId"]
                    barcode = find_barcode(vendor_code=vendor_code,company_id=yandex_market.business_id,api_key=yandex_market.api_key_bearer)
                    
                    if not barcode:
                        continue
                    
                    product = Product.objects.filter(barcode=barcode)
                    if product.exists():
                        
                        wildberries_product = product.filter(marketplace_type="wildberries")
                        if wildberries_product.exists():
                            W_product = wildberries_product.first()
                        else:
                            W_product = False
                        
                        yandexmarket_product = product.filter(marketplace_type='yandexmarket')
                        if yandexmarket_product.exists():
                                yandexmarket_product = yandexmarket_product.first()
                        else:
                            yandexmarket_product = False
                        
                        if (not yandexmarket_product) and (not W_product):
                            try:
                                product = Product.objects.create(vendor_code=vendor_code, marketplace_type="yandexmarket", barcode=barcode)
                            except:
                                continue
                            try:
                                product_sale_o = ProductSale.objects.create(product=product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                            continue
                        
                        elif yandexmarket_product and W_product:
                            product_sale_w = ProductSale.objects.filter(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            product_sale_y = ProductSale.objects.filter(product=yandexmarket_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            
                            if product_sale_w.exists():
                                continue
                            
                            elif product_sale_y.exists():
                                product_sale_y = product_sale_y.first()
                                product_sale_y.product = W_product
                                product_sale_y.save()
                                continue
                            
                            else:
                                try:
                                    product_sale_y = ProductSale.objects.create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                                except:
                                    continue
                        elif yandexmarket_product and (not W_product):
                            try:
                                product_sale_y = ProductSale.objects.get_or_create(product=yandexmarket_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                        elif W_product and (not yandexmarket_product):
                            try:
                                product_sale_y = ProductSale.objects.get_or_create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                    else:
                        product_obj, created_p = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type="yandexmarket")
                        if not ProductSale.objects.filter(
                            product=product_obj,
                            company=company,
                            date=date,
                            warehouse=warehouse,
                            marketplace_type="yandexmarket"
                        ):
                            product_s = ProductSale.objects.get_or_create(
                                product=product_obj,
                                company=company,
                                date=date,
                                warehouse=warehouse,
                                marketplace_type="yandexmarket"
                            )
                            # print(f"obj: {product_s}")
                    date = date + timedelta(seconds=1)
                    
    return "succes"
                    
@app.task(base=QueueOnce, once={'graceful': True})
def update_yandex_market_orders():
    
    for yandex_market in YandexMarket.objects.all():
        api_key_bearer = yandex_market.api_key_bearer
        fby_campaign_id = yandex_market.fby_campaign_id
        fbs_campaign_id = yandex_market.fbs_campaign_id
        company = yandex_market.company
        date_from = ProductOrder.objects.filter(marketplace_type="yandexmarket")

        if not (date_from or date_from.exists()):
            date_from = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d")
        else:
            date_from =date_from.latest("date").date.strftime("%Y-%m-%d")

        results1 = get_yandex_orders(api_key_bearer, date_from,client_id=fby_campaign_id,status="")
        results2 = get_yandex_orders(api_key_bearer, date_from,client_id=fbs_campaign_id,status="")

        results = results1 + results2

        for item in results:
            buyer_total = item.get("buyerTotal",0)
            item_total = item.get("itemsTotal",0)

            if buyer_total == item_total:

                oblast_okrug_name = find_republic_name(item["delivery"]['region'])
                if not oblast_okrug_name:
                    continue
                
                claster_to = Claster.objects.filter(region_name=oblast_okrug_name).first()
                if not claster_to:
                    oblast_okrug_name = oblast_okrug_name = find_republic_name(item["delivery"]['region'])
                else:
                    oblast_okrug_name = claster_to.claster_to
                
                warehouse, created_w = Warehouse.objects.get_or_create(
                    name = oblast_okrug_name,
                    oblast_okrug_name = oblast_okrug_name
                )
                
                products = item["items"]
                date = datetime.strptime(item['updatedAt'],"%d-%m-%Y %H:%M:%S")
                
                for product in products:
                    vendor_code = product["offerId"]
                    barcode = find_barcode(vendor_code=vendor_code,company_id=yandex_market.business_id,api_key=yandex_market.api_key_bearer)
                    if not barcode:
                        continue
                    product = Product.objects.filter(barcode=barcode)
                    
                    if product.exists():
                        
                        wildberries_product = product.filter(marketplace_type="wildberries")
                        if wildberries_product.exists():
                            W_product = wildberries_product.first()
                        else:
                            W_product = False
                        
                        yandexmarket_product = product.filter(marketplace_type='yandexmarket')
                        if yandexmarket_product.exists():
                                yandexmarket_product = yandexmarket_product.first()
                        else:
                            yandexmarket_product = False
                        
                        if (not yandexmarket_product) and (not W_product):
                            product = Product.objects.create(vendor_code=vendor_code, marketplace_type="yandexmarket", barcode=barcode)
                            try:
                                product_sale_o = ProductOrder.objects.create(product=product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                            continue
                        
                        elif yandexmarket_product and W_product:
                            product_sale_w = ProductOrder.objects.filter(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            product_sale_y = ProductOrder.objects.filter(product=yandexmarket_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            
                            if product_sale_w.exists():
                                continue
                            
                            elif product_sale_y.exists():
                                product_sale_y = product_sale_y.first()
                                product_sale_y.product = W_product
                                product_sale_y.save()
                                continue
                            
                            else:
                                try:
                                    product_sale_y = ProductOrder.objects.create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                                except:
                                    continue
                        elif yandexmarket_product and (not W_product):
                            try:
                                product_sale_y = ProductOrder.objects.get_or_create(product=yandexmarket_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                        elif W_product and (not yandexmarket_product):
                            try:
                                product_sale_y = ProductOrder.objects.get_or_create(product=W_product,company=company,date=date,warehouse=warehouse,marketplace_type="yandexmarket")
                            except:
                                continue
                    else:
                        product_obj, created_p = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type="yandexmarket")
                        if not ProductOrder.objects.filter(
                            product=product_obj,
                            company=company,
                            date=date,
                            warehouse=warehouse,
                            marketplace_type="yandexmarket").exists():
                            product_s = ProductOrder.objects.get_or_create(
                                product=product_obj,
                                company=company,
                                date=date,
                                warehouse=warehouse,
                                marketplace_type="yandexmarket"
                            )

                    date = date + timedelta(seconds=1)
    return "succes"    

def get_warehouse_name(business_id,headers, warehouse_id):
    warehouse_by_busness_id_url = f"https://api.partner.market.yandex.ru/businesses/{business_id}/warehouses"               
    warehouse_url = f"https://api.partner.market.yandex.ru/warehouses"    

    get_warehouse_name_l = requests.get(warehouse_by_busness_id_url,headers=headers)
    if get_warehouse_name_l.status_code == 200:
        get_warehouse_name_l = get_warehouse_name_l.json()["result"]["warehouses"]
    else:
        get_warehouse_name_l = []
    get_warehouse_name_l_2 = requests.get(warehouse_url,headers=headers)
    if get_warehouse_name_l_2.status_code == 200:
        get_warehouse_name_l_2 = get_warehouse_name_l_2.json()["result"]["warehouses"]
    else:
        get_warehouse_name_l = []
    results = get_warehouse_name_l + get_warehouse_name_l_2
    
    for item in results:
        if item["id"] == warehouse_id:
            return item['address']['gps']
        
@app.task(base=QueueOnce, once={'graceful': True})
def update_yandex_stocks():
    
    for yandex in YandexMarket.objects.all():
        api_key = yandex.api_key_bearer
        # fbs = yandex.fbs_campaign_id
        fby = yandex.fby_campaign_id
        business_id = yandex.business_id
        
        url = "https://api.partner.market.yandex.ru/campaigns/{campaignId}/offers/stocks"
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
                }
        # response1 = requests.post(url.format(campaignId=fbs), headers=headers)
        results = []
        response2 = requests.post(url.format(campaignId=fby), headers=headers)
        
        # while True:
        #     if response1.status_code == 200 and "paging" in response1.json()["result"].keys() and "nextPageToken" in response1.json()["result"]["paging"].keys():
        #         result1 += response1.json()["result"]["warehouses"]
        #         nextPageToken = response1.json()["result"]["paging"]["nextPageToken"]
        #         params = {"page_token": nextPageToken}
        #         response1 = requests.post(url.format(campaignId=fbs), headers=headers,params=params)
        #     else:
        #         break
        
        while True:
            if response2.status_code == 200 and "paging" in response2.json()["result"].keys() and "nextPageToken" in response2.json()["result"]["paging"].keys():
                results += response2.json()["result"]["warehouses"]
                nextPageToken = response2.json()["result"]["paging"]["nextPageToken"]
                params = {"page_token": nextPageToken}
                response2 = requests.post(url.format(campaignId=fby), headers=headers,params=params)
            else:
                break
        company = yandex.company
       
        for item in results:
            warehouse = WarehouseYandex.objects.filter(warehouse_id=item['warehouseId']).first()
            if not warehouse:
                warehouse = get_warehouse_name(business_id,headers,item['warehouseId'])
                if not warehouse:
                    continue
                latitude = warehouse['latitude']
                longitude = warehouse['longitude']
                warehouse = get_location_info(latitude=latitude, longitude=longitude)
            else:
                warehouse = warehouse.claster_to

            for offers in item['offers']:
                if "upatedAt" in offers.keys():
                    date = datetime.strptime(offers['updatedAt'],"%Y-%m-%dT%H:%M:%S.%f%z")
                else:
                    date = datetime.now()
                vendor_code = offers["offerId"]
                count = 0
                for stock in offers['stocks']:
                    if stock and stock["type"] == "AVAILABLE":
                        count += stock["count"]
                quantity = count
            
                barcode = find_barcode(vendor_code=vendor_code,company_id=yandex.business_id,api_key=yandex.api_key_bearer)
                
                if not barcode or not warehouse:
                    continue
                
                product = Product.objects.filter(barcode=barcode)
                warehouses, created_w = WarehouseForStock.objects.get_or_create(name=warehouse, marketplace_type="yandexmarket")
                
                if not product.exists():
                    product, created_s = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type='yandexmarket')
                
                elif product.filter(marketplace_type='yandexmarket').exists():
                    
                    product_o = product.filter(marketplace_type='yandexmarket').first()
                    if product.filter(marketplace_type="wildberries").exists():
                        
                        vendor_code = product.filter(marketplace_type="wildberries").first().vendor_code
                        if product_o.vendor_code != vendor_code:
                            product_o.vendor_code = vendor_code
                            product_o.save()
                    
                    product = product_o
                
                else:
                    product, created = Product.objects.get_or_create(vendor_code=vendor_code, barcode=barcode, marketplace_type='yandexmarket')
                    
                product_stock, created_s = ProductStock.objects.get_or_create(
                    product=product,
                    warehouse=warehouses,
                    marketplace_type = "yandexmarket",
                    company=company,
                    date=date
                )

                product_stock.quantity = quantity
                product_stock.save()

    return "Succes"

@app.task(base=QueueOnce, once={'graceful': True})
def synchronous_algorithm():
    
    update_wildberries_sales.delay()
    update_ozon_sales.delay()
    update_yandex_market_sales.delay()
    
    update_wildberries_orders.delay()
    update_ozon_orders.delay()
    update_yandex_market_orders.delay()
    
    update_wildberries_stocks.delay()
    
    update_ozon_stocks.delay()
    
    update_yandex_stocks.delay()

    return True

    