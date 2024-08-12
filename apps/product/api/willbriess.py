import requests, json


def wb_data_from_api():
    url = "https://suppliers-api.wildberries.ru/content/v2/get/cards/list"
    token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQwNzE1djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTczNzU4NTQzNywiaWQiOiIxZDVkZGM3OC04NTA2LTQ4YmEtODNhMi01YzlkMzNhNDM0MzAiLCJpaWQiOjIzMDc3OTc2LCJvaWQiOjM2NTU1LCJzIjoxMDczNzQ0OTQyLCJzaWQiOiIzOGViNDYzNy00MmZlLTU5ODYtOTIwMC1hMTJhZDc5NjU0NjUiLCJ0IjpmYWxzZSwidWlkIjoyMzA3Nzk3Nn0.RaWr6BmCMhsk6JTHrnAtdVXpQyZgE3DZrQ0z7W2MczuRmcvEVGe4eXKPbSissK2pACJ1yg6OcL9H87B2dVFWFg"
    headers = {
        'Authorization': f'{token}'
    }

    payload = {
          "settings": {
            "cursor": {
                # "limit": 100
                # "nmID": 246675599,
                # "total": 1
            },
            "filter": {
              "withPhoto": -1
            }
          }
        }

    responce = requests.post(url, headers=headers, data=json.dumps(payload))
    print(responce.json())
    return []


print(wb_data_from_api())