import requests
import time
import json

params = {
    'status':1,
    'time_temp': int(time.time()*1000)
}

url = 'http://127.0.0.1:5000/proxies'
response = requests.get(url=url, params=params).json()

print(response)




