import requests
import json

def get_product_information(company_id, api_token):
    url = f"https://api.partner.market.yandex.ru/v2/businesses/{company_id}/offer-mappings"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Query parametrlarini sozlash
    body = {
         # Agar sahifalash kerak bo'lsa, keyingi sahifani yuklash uchun token
        "offerIds": ["boyS108i"]
    }
    params = {
        'limit': 10,  # Bir sahifada qancha mahsulot ko'rsatilishini belgilaydi
        'page_token': None
    }
    
    # POST so'rovini yuborish
    response = requests.post(url, headers=headers, json=body, params=params)
    
    if response.status_code == 200:
        return response.json()  # JSON formatidagi javobni qaytaradi
    else:
        return f"Xato: {response.status_code} - {response.text}"

# Foydalanish misoli
company_id = "865333"
api_token = "y0_AgAEA7qjt7KxAAwmdgAAAAELY-tgAACft8WA-URJh5WJkKCbUYyt3bxRug"
product_info = get_product_information(company_id, api_token)
print(product_info)
