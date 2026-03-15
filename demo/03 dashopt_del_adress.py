import requests

url = "http://127.0.0.1:8000/v1/users/zhaoyilin/address/4"
headers ={
    "authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDkxMDg3MzMsInVzZXJuYW1lIjoiemhhb2xpeWluIn0.BqCQoUJSs7xcSlHRLznGhHBgGMtxaCx1J5R8mF-jDJo"
}
data ={"id": "4"}
html = requests.delete(url=url, json=data, headers= headers).json()
print(html)