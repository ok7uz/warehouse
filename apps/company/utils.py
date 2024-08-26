import json
import requests
from datetime import timedelta, datetime


def fetch_product_info(api_token, client_id, sku):
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_token,
        'Content-Type': 'application/json'
    }

    url = "https://api-seller.ozon.ru/v2/product/info/list"
    payload = json.dumps({"sku": sku})

    with requests.post(url, headers=headers, data=payload) as response:
        data = {}
        for item in response.json()['result']['items']:
            data[str(item['sku'])] = item['offer_id']
        return data


def get_ozon_sales(api_token, client_id, date_from=None, date_to=None):
    date_from = date_from or (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = date_to or datetime.now().strftime('%Y-%m-%d')
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_token,
        'Content-Type': 'application/json'
    }

    url = "https://api-seller.ozon.ru/v1/analytics/data"
    payload = json.dumps({
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

    with requests.post(url, headers=headers, data=payload) as response:
        data = response.json()
        results = data['result']['data']

    date_range = [(datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
                  for i in range((datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days + 1)]

    unique_data = {}
    for item in results:
        sku = item['dimensions'][0]['id']
        date = item['dimensions'][1]['id']
        quantity = item['metrics'][1]
        if quantity > 0:
            if sku in unique_data:
                if date in unique_data[sku]:
                    unique_data[sku][date] += quantity
                else:
                    unique_data[sku][date] = quantity
            else:
                unique_data[sku] = {}
                for date in date_range:
                    unique_data[sku][date] = 0
                unique_data[sku][date] = quantity

    response_data = {}
    products_info = fetch_product_info(api_token, client_id, list(unique_data.keys()))
    for sku, data in unique_data.items():
        vendor = products_info[sku] if sku in products_info else sku
        response_data[vendor] = data

    return response_data


def get_wildberries_sales(wb_api_key, date_from=None, date_to=None):
    date_from = date_from or (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = date_to or datetime.now().strftime('%Y-%m-%d')
    date_range = [(datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
                  for i in range((datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days + 1)]


    url = f'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={date_from}T00:00:00'
    headers = {
        'Authorization': f'Bearer {wb_api_key}'
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    response_data = {}
    for item in data:
        date = item['date'][:10]
        if date in date_range:
            vendor = item['supplierArticle']
            if vendor in response_data:
                response_data[vendor][date] += 1
            else:
                response_data[vendor] = {}
                for d in date_range:
                    response_data[vendor][d] = 0
                response_data[vendor][date] += 1
    return dict(sorted(response_data.items()))
    
    
    


def get_yandex_market_sales(api_key_bearer, fby_campaign_id, fbs_campaign_id, business_id, date_from=None, date_to=None):
    date_from = date_from or (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = date_to or datetime.now().strftime('%Y-%m-%d')
