import json
import aiohttp
import asyncio
from datetime import timedelta, datetime

async def fetch_product_info(session, api_token, client_id, sku):
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_token,
        'Content-Type': 'application/json'
    }

    url = "https://api-seller.ozon.ru/v2/product/info"
    payload = json.dumps({"sku": sku})

    async with session.post(url, headers=headers, data=payload) as response:
        return await response.json()

async def get_ozon_sales(api_token, client_id, date_from=None, date_to=None):
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

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.json()

        unique_data = {}
        for item in data['result']['data']:
            try:
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
                        for i in range((datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days + 1):
                            unique_data[sku][(datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')] = 0
                        unique_data[sku][date] = quantity
            except:
                pass

        tasks = [fetch_product_info(session, api_token, client_id, sku) for sku in unique_data.keys()]
        results = await asyncio.gather(*tasks)

        response_data = {}
        for result, sku in zip(results, unique_data.keys()):
            vendor = result['result']['offer_id']
            response_data[vendor] = unique_data[sku]

        return response_data


def get_wildberries_sales(wb_api_key, date_from=None, date_to=None):
    date_from = date_from or (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = date_to or datetime.now().strftime('%Y-%m-%d')


def get_yandex_market_sales(api_key_bearer, fby_campaign_id, fbs_campaign_id, business_id, date_from=None, date_to=None):
    date_from = date_from or (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = date_to or datetime.now().strftime('%Y-%m-%d')