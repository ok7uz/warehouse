import requests

# Javobni olgan so'rov
url = "https://api.partner.market.yandex.ru/v2/campaigns/23746359/offers/stocks.json?page_token=eyJvcCI6Ij4iLCJrZXkiOiJsYnQxMiIsInNraXAiOjB9"

headers = {
    'Authorization': 'your_authorization_token',
    'Cookie': '_yasc=IlUOmtc9nVX11Kh6sYrQujJGxIsYNRpR6LVofzrIq+RDa+U0YN7rfH8Dpq8jcA/D9I0=; i=s9Ny4msrbrIZt1Df4V9UeGyG0DEon8ydFobxhalVZv5NG/VQd6KsQSt7nu1BmrlziA1g9g1+0PM/1Vs5B/HW6ZIzHR0=; yandexuid=4802114501724596423; yashr=8861220291724596423'
}

response = requests.post(url, headers=headers)

# Javobni JSON formatida olish
data = response.json()

# warehouseId ni olish (birinchi ombor uchun misol)
warehouse_id = data['result']['warehouses'][0]['id']  # Misol uchun, birinchi ombor

# Ombor haqida batafsil ma'lumot olish
warehouse_url = f"https://api.partner.market.yandex.ru/v2/campaigns/23746359/warehouses/{warehouse_id}.json"

warehouse_response = requests.get(warehouse_url, headers=headers)

# Ombor ma'lumotlarini chop etish
if warehouse_response.status_code == 200:
    warehouse_info = warehouse_response.json()
    print(warehouse_info)
else:
    print(f"Xatolik: {warehouse_response.status_code}, {warehouse_response.text}")
