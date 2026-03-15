import json

import jwt
from django.http import JsonResponse
from django.conf import settings
from user.models import UserProfile


def logging_check(func):
    def wrapper(self, request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            return JsonResponse({"code": 403, "error": "Please login"})

        try:
            payload = jwt.decode(token, key=settings.JWT_TOKEN_KEY, algorithms="HS256")
        except Exception as e:
            return JsonResponse({"code": 403, "error": "Please login"})

        # 拿取用户名
        username = payload.get("username")
        # 查取对象
        user = UserProfile.objects.get(username=username)
        # 添加对象属性
        request.myuser = user

        data_loads = None
        if request.body:
            data_loads = json.loads(request.body.decode())
        request.data = data_loads
        return func(self, request, *args, **kwargs)
    return wrapper