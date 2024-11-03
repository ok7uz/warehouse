# import os 
# import django

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
# django.setup()

# from apps.product.tasks import get_yandex_orders

# print(len(get_yandex_orders("y0_AgAEA7qjt7KxAAwmdgAAAAELY-tgAACft8WA-URJh5WJkKCbUYyt3bxRug","2023-10-10",23746359,"")))

import json
import requests

headers = {
    'Authorization': "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMxMjYxMzczLCJpYXQiOjE3MzA2NTY1NzMsImp0aSI6ImRiMDc2ODE0MGJhMTQ3YTk5NzJmMTE1ZGQzZDc2YTBkIiwidXNlcl9pZCI6MX0.af0HPZ-CVLFOnywMwOH12sJSuj_RlrWZzNm8XvE4A8E",
    'Content-Type': 'application/json'
}

company_id = "5e30f3e4-4b35-436c-a414-d300530b3b1d"

with open("claster.json", 'r') as f :
    data = json.loads(f.read())

for item in data:
    claster = item['Кластер']
    for region in item['Что в него входит']:
        
        data = {
        "claster_to": claster,
        "region_name": region
        }

        print(requests.post("http://51.250.22.154:8000/api/claster/v1/5e30f3e4-4b35-436c-a414-d300530b3b1d", json=data,headers=headers).status_code)
