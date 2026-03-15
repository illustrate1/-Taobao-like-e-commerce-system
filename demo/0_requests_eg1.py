"""
    测试达达商城登录
"""


import requests

url = "http://127.0.0.1:8000/v1/tokens"
data = {
    "username": "zhaoliyin",
    "password": "123456",
    "carts": 0
}

resp = requests.post(url=url, json=data)
print(resp.text)
print(resp.json())