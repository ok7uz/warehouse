import time
import aiohttp
import asyncio
import json
import datetime
import random
from concurrent.futures import ThreadPoolExecutor

# Constants
CLIENT_ID = '48762'
API_KEY = '5b3b0e68-3f96-4772-9550-9951cb3d1678'
HEADERS = {
    'Client-Id': CLIENT_ID,
    'Api-Key': API_KEY,
    'Content-Type': 'application/json'
}
TIMEOUT = aiohttp.ClientTimeout(total=60)
MAX_CONCURRENT_REQUESTS = 10  # Control the number of concurrent requests


# Fetch SKU info asynchronously
async def fetch_sku_info(session, sku, retries=5, backoff_factor=1):
    url = 'https://api-seller.ozon.ru/v2/product/info'
    payload = json.dumps({"sku": sku})

    for attempt in range(retries):
        try:
            async with session.post(url, headers=HEADERS, data=payload, timeout=TIMEOUT) as response:
                if response.status == 429:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info, history=response.history, code=429
                    )
                return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
            else:
                raise
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return {'error': 'Max retries exceeded due to timeout'}
            wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
    return {'error': 'Max retries exceeded'}


# Fetch analytics data asynchronously
async def fetch_analytics_data(session, date_from, date_to, retries=5, backoff_factor=1):
    url = 'https://api-seller.ozon.ru/v1/analytics/data'
    payload = json.dumps({
        "date_from": date_from.strftime('%Y-%m-%d'),
        "date_to": date_to.strftime('%Y-%m-%d'),
        "metrics": ["revenue", "ordered_units"],
        "dimension": ["sku", 'day'],
        "limit": 1000,
        "offset": 0
    })

    for attempt in range(retries):
        try:
            async with session.post(url, headers=HEADERS, data=payload, timeout=TIMEOUT) as response:
                if response.status == 429:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info, history=response.history, code=429
                    )
                return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
            else:
                raise
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return {'error': 'Max retries exceeded due to timeout'}
            wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
    return {'error': 'Max retries exceeded'}


# Process SKU info
def process_sku_info(sku_info, item):
    data_sku = [dim['id'] for dim in item.get('dimensions', [])]
    data_date = next((dim['id'] for dim in item.get('dimensions', []) if not dim['name']), None)

    metrics = item.get('metrics', [])

    sources = sku_info.get('result', {}).get('sources', [])
    ozon_fbo_sku_id = None
    ozon_fbs_sku_id = None

    for source in sources:
        if source['source'] == 'fbo':
            ozon_fbo_sku_id = source['sku']
        elif source['source'] == 'fbs':
            ozon_fbs_sku_id = source['sku']

    quantity = metrics[1] if len(metrics) > 1 else None

    result = sku_info.get('result', {})
    name = result.get('name')
    vendor = result.get('offer_id')
    barcodes = result.get('barcodes', [])

    return {
        "name": name,
        "vendor": vendor,
        "ozon_barcode": barcodes[0] if barcodes else [],
        "ozon_product_id": result.get('id'),
        "ozon_sku": data_sku[0],
        "ozon_fbo_sku_id": ozon_fbo_sku_id,
        "ozon_fbs_sku_id": ozon_fbs_sku_id,
        "quantity": quantity,
        'data_date': data_date
    }


# Process data
async def process_data(date_from, date_to):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)) as session:
        response = await fetch_analytics_data(session, date_from, date_to)

        if 'result' not in response:
            return {'error': 'Invalid response format', 'response': response}

        tasks = []
        for item in response['result'].get('data', []):
            data_sku = [dim['id'] for dim in item.get('dimensions', [])]

            if not data_sku:
                continue

            tasks.append((fetch_sku_info(session, data_sku[0]), item))

        # Process SKU info in batches
        batch_size = MAX_CONCURRENT_REQUESTS
        datas = []
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            sku_infos = await asyncio.gather(*[task[0] for task in batch])
            datas.extend([process_sku_info(sku_info, item) for sku_info, item in zip(sku_infos, [task[1] for task in batch])])
    return datas


async def fetch_analytics_stock_on_warehouses(session, retries=5, backoff_factor=1):
    url = 'https://api-seller.ozon.ru/v2/analytics/stock_on_warehouses'

    payload = json.dumps({
        "limit": 1000,
        "offset": 0,
        "warehouse_type": "ALL"
    })

    for attempt in range(retries):
        try:
            async with session.post(url, headers=HEADERS, data=payload, timeout=TIMEOUT) as response:
                if response.status == 429:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info, history=response.history, code=429
                    )
                return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
            else:
                raise
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return {'error': 'Max retries exceeded due to timeout'}
            wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
    return {'error': 'Max retries exceeded'}


async def process_data2(date_format):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)) as session:
        response = await fetch_analytics_stock_on_warehouses(session)

        if 'result' not in response:
            return {'error': 'Invalid response format', 'response': response}

        
    return []
    #     tasks = []
    #     for item in response['result'].get('data', []):
    #         data_sku = [dim['id'] for dim in item.get('dimensions', [])]
    #
    #         if not data_sku:
    #             continue
    #
    #         tasks.append((fetch_sku_info(session, data_sku[0]), item))
    #
    #     # Process SKU info in batches
    #     batch_size = MAX_CONCURRENT_REQUESTS
    #     datas = []
    #     for i in range(0, len(tasks), batch_size):
    #         batch = tasks[i:i + batch_size]
    #         sku_infos = await asyncio.gather(*[task[0] for task in batch])
    #         datas.extend(
    #             [process_sku_info(sku_info, item) for sku_info, item in zip(sku_infos, [task[1] for task in batch])])
    #
    # return datas