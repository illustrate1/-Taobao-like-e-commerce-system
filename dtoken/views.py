import hashlib
import json
import time
import jwt

from django.http import JsonResponse
from user.models import UserProfile
from django.conf import settings
from carts.views import CartsView


def tokens(request):
    """
    登录功能视图函数
    :param request:
    :return:
    """
    # 1 获取请求体的数据
    data = json.loads(request.body.decode())
    username = data.get("username")
    password = data.get("password")

    # 2 判断用户名是否存在
    try:
        user = UserProfile.objects.get(username=username)
    except Exception as e:
        print("---", e)
        return JsonResponse({"code": 10200, "error": "The username is wrong"})
    # 3 判断密码是否正确
    m = hashlib.md5()
    m.update(password.encode())
    if m.hexdigest() != user.passworld:
        return JsonResponse({"code": 10201, "error": "The password is wrong"})
    token = make_token(username)

    # 购物车数据合并 离线购物车和在线购物车
    offline_data = data.get("carts")
    carts_count = CartsView().merge_carts(offline_data, user.id)


    result = {
        'code': 200,
        'username': username,
        'data': {'token': token},
        'carts_count': carts_count
    }
    # 4 组织数据返回
    return JsonResponse(result)

def make_token(uname, expire=3600*24):
    """
    生成token
    :param uname: 用户名
    :return: token
    """
    payload = {
        "exp": int(time.time())+expire,
        "username": uname
    }
    key = settings.JWT_TOKEN_KEY
    return jwt.encode(payload, key, algorithm="HS256").decode()