from geopy.geocoders import Nominatim
import time

proxies_list = [
    {"http": "http://62.171.168.103:80", "https": "http://62.171.168.103:80"},
    {"http": "http://23.82.137.157:80", "https": "http://23.82.137.157:80"},
    {"http": "http://142.93.202.130:3128", "https": "http://142.93.202.130:3128"},
    # {"http": "http://206.189.158.210:80", "https": "http://206.189.158.210:80"},
    # {"http": "http://182.253.141.140:8080", "https": "http://182.253.141.140:8080"}
]

def get_location_info(latitude, longitude):
    time.sleep(5) 

    try:

        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse((latitude, longitude), exactly_one=True)

        if location:
            address = location.raw.get('address', {})
            region = address.get('state', '')
            country = address.get('country', 'Davlat ma\'lumotlari topilmadi')
            return region
        else:
            return ""
    except Exception as e:

        return ""




