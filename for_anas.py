
import json
import requests

# ========== Stocks from Analytic (with paginations)========== 
def stock_from_analytic(header, offset=0, limit=1000, attempt=1, data_list=None):
    """
    Остатки товаро из аналитики
    """
    if not data_list:
        data_list = []
    url = f'https://api-seller.ozon.ru/v2/analytics/stock_on_warehouses'
    payload = json.dumps({
          "limit": limit,
          "offset": offset,
          "warehouse_type": "ALL"
    })
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        main_data = json.loads(response.text)
        stock_data = main_data['result']['rows']
        for data in stock_data:
            data_list.append(data)
        # made recursion for pagination in ozon
        if len(stock_data) == limit:
            offset = limit * attempt
            attempt += 1
            return stock_from_analytic(header, offset, limit, attempt, data_list)
        else:
            return data_list
# ========== Finish Stocks from analytic ========== #

# ========== Orders ========== #

def orders_fbo(header, data_from, date_to, offset=0, limit=1000, attempt=1, data_list=None):
    """
    FBO Orders
    """
    # time.sleep(1)
    if not data_list:
        data_list = []
    url = f'https://api-seller.ozon.ru/v2/posting/fbo/list'
    payload = json.dumps(
        {
            "dir": "ASC",
            "filter": {
                "since": f'{data_from}T00:00:00.000Z',
                "status": "",
                "to": f"{date_to}T00:00:00.000Z"
            },
            "limit": limit,
            "offset": offset,
            "translit": True,
            
            "with": {
                "analytics_data": True,
                "financial_data": True
            }
        }
    )
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        main_data = json.loads(response.text)
        stock_data = main_data['result']
        for data in stock_data:
            data_list.append(data)
        # made recursion for pagination in ozon
        if len(stock_data) == limit:
            offset = limit * attempt
            attempt += 1
            return orders_fbo(header, data_from, date_to, offset, limit, attempt, data_list)
        else:
            return data_list
        
def orders_fbs(header, data_from, date_to, offset=0, limit=1000, attempt=1, data_list=None):
    """
    FBS Orders
    """
    # time.sleep(1)
    if not data_list:
        data_list = []
    url = f'https://api-seller.ozon.ru/v3/posting/fbs/list'
    payload = json.dumps(
        {
            "dir": "ASC",
            "filter": {
                "since": f'{data_from}T00:00:00.000Z',
                "to": f"{date_to}T00:00:00.000Z"
            },
            "limit": limit,
            "offset": offset,
            # if using this setting cluster name will be russian name
            "with": {
                "financial_data": True
            }
        }
    )
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        main_data = json.loads(response.text)
        stock_data = main_data['result']['postings']
        for data in stock_data:
            data_list.append(data)
        # made recursion for pagination in ozon
        if len(stock_data) == limit:
            offset = limit * attempt
            attempt += 1
            return orders_fbs(header, data_from, date_to, offset, limit, attempt, data_list)
        else:
            return data_list

# Lists with storages in cluster (its could be in database, i think)
MOSKVA_ZAPAD_CLUSTER = ['ГРИВНО_РФЦ', 'ДОМОДЕДОВО_РФЦ', 'ПЕТРОВСКОЕ_РФЦ', 'ХОРУГВИНО_РФЦ', 'СОФЬИНО_РФЦ']
MOSKVA_VOSTOK = ['ЖУКОВСКИЙ_РФЦ', 'НОГИНСК_РФЦ', 'ПУШКИНО_1_РФЦ', 'ПУШКИНО_2_РФЦ', 'ТВЕРЬ_РФЦ', 'ТВЕРЬ_ХАБ']
SANKT_PETERBURG = ['САНКТ_ПЕТЕРБУРГ_РФЦ', 'СПБ_БУГРЫ_РФЦ', 'СПБ_КОЛПИНО_РФЦ', 'СПБ_ШУШАРЫ_РФЦ']
DON = ['ВОРОНЕЖ_МРФЦ', 'ВОРОНЕЖ_2_РФЦ', 'ВОЛГОГРАД_МРФЦ', 'РОСТОВ_НА_ДОНУ_РФЦ']
UG = ['АДЫГЕЙСК_РФЦ', 'НЕВИННОМЫССК_РФЦ', 'НОВОРОССИЙСК_МРФЦ']
POVOLZHIE = ['КАЗАНЬ_РФЦ', 'НИЖНИЙ_НОВГОРОД_РФЦ', 'ОРЕНБУРГ_РФЦ', 'САМАРА_РФЦ']
URAL = ['ЕКАТЕРИНБУРГ_РФЦ']
SIBIR = ['КРАСНОЯРСК_МРФЦ', 'НОВОСИБИРСК_РФЦ', 'ОМСК_РФЦ']
KALININGRAD = ['КАЛИНИНГРАД_МРФЦ']
DALNIY_VASTOK = ['ХАБАРОВСК_2_РФЦ']
BELARUS = ['МИНСК_МПСЦ']
KAZAKHSTAN = ['АСТАНА_РФЦ', 'АЛМАТЫ_МРФЦ']

# Clusters name for check orders
CLUSTERS_NAME = ['Дальний Восток', 
                     'Москва-Восток и Дальние регионы', 
                     'Санкт-Петербург и СЗО', 
                     'Дон', 
                     'Юг',
                     'Поволжье',
                     'Урал',
                     'Сибирь',
                     'Калининград',
                     'Дальний Восток',
                     'Беларусь',
                     'Казахстан']
ozon_headers_ooo = {
    'Api-Key': "5b3b0e68-3f96-4772-9550-9951cb3d1678	", # Api-Key from ozon
    'Content-Type': 'application/json',
    'Client-Id': "48762" # Client-id from Ozon
}

def stock_amount_cluster(article, cluster_name):
    # Get all stock info from analytic with pagination
    data_list = stock_from_analytic(ozon_headers_ooo)

    print(len(data_list)) # check amount of entries from ozon
    stock_art = 0
    for data in data_list:
        # compare incoming cluster and article with data from ozon and count stock in cluster
        if data['warehouse_name'].upper() in cluster_name and data['item_code'] == article:
            stock_art += data["free_to_sell_amount"]
    print('stock', stock_art)
    return stock_art


def orders_amount_cluster(article, cluster_name, date_from, date_to):
    # Get all fbs\fbo orders for incoming article in incoming cluster
    data_list_fbo = orders_fbo(ozon_headers_ooo, date_from, date_to)
    
    orders_fbo_amount = 0
    for data in data_list_fbo:
        # compare incoming cluster and article with data from ozon and count order in cluster
        if data['financial_data']['cluster_to'] == cluster_name and data['products'][0]['offer_id'] == article:
            orders_fbo_amount += data['products'][0]['quantity']
    print('orders_fbo_amount', orders_fbo_amount)

    data_list_fbs = orders_fbs(ozon_headers_ooo, date_from, date_to)
    orders_fbs_amount = 0
    for data in data_list_fbs:
        # compare incoming cluster and article with data from ozon and count order in cluster
        if data['financial_data']['cluster_to'] == cluster_name and data['products'][0]['offer_id'] == article:
            orders_fbs_amount += data['products'][0]['quantity']
    print('orders_fbs_amount', orders_fbs_amount)

    common_amount = orders_fbo_amount + orders_fbs_amount
    print('common_amount', common_amount)
    return common_amount

print(orders_fbo(header=ozon_headers_ooo,date_to="2024-10-31", data_from="2024-09-31",))