from datetime import datetime

import requests
import json


url = 'https://api-seller.ozon.ru/v2/product/list'
url_info = 'https://api-seller.ozon.ru/v2/product/info'
url_warehouse = "https://api-seller.ozon.ru/v1/warehouse/list"
url_warehouse_info = "https://api-seller.ozon.ru/v3/product/info/stocks"

headers = {
     'Client-Id': '48762',
     'Api-Key': '5b3b0e68-3f96-4772-9550-9951cb3d1678',
     'Content-Type': 'application/json'
 }
params = {

 }

data = {
     "product_id": 575382951,
     # "name": "Ночник \"Руки с сердцем 3D\" - подарок любимой жене, супруге"
 }
data_json = json.dumps(data)

response = requests.post(url, headers=headers, params=params)
response_info = requests.post(url_info, headers=headers, data=data_json)
responce_warehouse = requests.post(url_warehouse, headers=headers)
response_warehouse_info = requests.post(url_warehouse_info, headers=headers)

# print(response.json())
print("---------------")
print(response_info.json())
# print("---------------")
# print(responce_warehouse.json())
# print("---------------")
# print(response_warehouse_info.json())


def get_analytics_data(date_from=datetime, date_to=datetime.now().strftime("%Y-%m-%d")):
    # Headers
    headers = {
        'Client-Id': '48762',
        'Api-Key': '5b3b0e68-3f96-4772-9550-9951cb3d1678',
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
            "spu",
            "day"
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

    response = requests.post(url, headers=headers, data=payload)

    # Return the response JSON data
    return response.json()


def save_response_as_json(date_from, date_to, file_name):
    data = get_analytics_data(date_from, date_to)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Fetch and save the analytics data
save_response_as_json("2024-07-16", "2024-07-23", "analytics_data.json")

print("Data saved to analytics_data.json")