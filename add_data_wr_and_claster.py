import requests
import json 

company_id = "5e30f3e4-4b35-436c-a414-d300530b3b1d"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwOTI5ODM5LCJpYXQiOjE3MzAzMjUwMzksImp0aSI6IjE1YWEwYzQ0YzUzZjRkMDE4MTVjNDI1MmI3YzhhZGQ2IiwidXNlcl9pZCI6MX0.m1oAEjl50cfmD8yFnd2uxUoEYzERX4X2vdz_w2RR2KE"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

with open("claster.json", 'r') as f :
    clasters = json.loads(f.read())

with open("warehouses.json", 'r') as f :
    wr = json.loads(f.read())

# for claster_item in clasters:
#     claster = claster_item["Кластер"]
#     for item in claster_item["Что в него входит"]:
#         region_name = item

#         data = {
#             "claster_to": claster,
#             "region_name": region_name
#         }

#         print(requests.post(f"http://51.250.22.154:8000/api/claster/v1/{company_id}",json=data, headers=headers).text)

for wr_item in wr:
    claster = wr_item['Кластер']
    for item in wr_item["Склады"]:
        warehouse_id = item["id"]

        data = {
            "claster_to": claster,
            "warehouse_id": warehouse_id
        }

        print(requests.post(f"http://51.250.22.154:8000/api/claster/v1/warehouse/{company_id}", json=data, headers=headers).text)



