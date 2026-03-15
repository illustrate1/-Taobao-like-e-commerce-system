import base64
import random
import time

import jwt
import hashlib
import json

import requests
from django.http import JsonResponse
from user.models import UserProfile, Address
from django.conf import settings
from django.core.cache import caches
from .tasks import async_send_active_email, async_send_message
from django.views import View
from django.db import transaction
from user.models import WeiBoProfile
from carts.views import CartsView

from django.core.mail import send_mail

from utils.logging_dec import logging_check
from utils.baseview import BaseView
from utils.weiboapi import OAuthWeiBoAPI
from utils.sms import YunTonXunAPI

CODE_CACHE = caches["default"]
# 短信缓存配置项
SMS_CACHE = caches["sms"]




def users(request):
    """
    注册功能视图函数
    1.获取请求体数据[request.body]

    2.数据校验
    3.查看用户名是否已经存在
      3.1 已存在 。。。
    4.生成token
    5.返回数据体
    """
    data = json.loads(request.body.decode())
    uname = data.get("uname")
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone")
    # 获取短信验证码
    verify = data.get("verify")

    # 从redis中取出验证码校验
    expire_key = "sms_expire_{}".format(phone)
    redis_code = SMS_CACHE.get(expire_key)
    if not redis_code:
        return JsonResponse({"code": 10108, "error": {"message": "验证码已经过期了，请重新获取"}})

    if verify != str(redis_code):
        return JsonResponse({"code": 10109, "error": {"message": "验证码有误，请重新获取"}})

    old_users = UserProfile.objects.filter(username=uname)
    if old_users:
        return JsonResponse({"code": 10100, "error": "The username is existed"})

    # 存入数据库
    m = hashlib.md5()
    m.update(password.encode())
    pwd_md5 = m.hexdigest()

    # 考虑并发
    try:
        user = UserProfile.objects.create(username=uname, passworld=pwd_md5, phone=phone, email=email)
    except Exception as e:
        print('------->', e)
        return JsonResponse({"code": 10101, "error": "The username is existed"})
    # 签发token
    token = make_token(uname)

    # 二次开发， try一下
    try:
        # 发送激活邮件
        # 激活链接：http://xxxx/active.html?code=xxx
        verify_url = get_verify_url(uname)
        # 发送激活邮件
        # send_active_email(email, verify_url)
        # 异步发送激活邮件
        async_send_active_email.delay(email, verify_url)
    except Exception as e:
        print("send email error:", e)
    offline_data = data.get("carts")
    carts_count = CartsView().merge_carts(offline_data, user.id)
    # 组织数据返回
    result = {
        'code': 200,
        'username': uname,
        'data': {'token': token},
        'carts_count': carts_count
    }

    return JsonResponse(result)

def active_view(request):
    """
    邮件激活视图逻辑
    :param request:
    :return:
    """
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"code": 10102, "error": "Not code"})
    # 获取明文
    code_str = base64.urlsafe_b64decode(code.encode()).decode()
    number, username = code_str.split("_")
    key = "active_email_%s" % username
    redis_num = CODE_CACHE.get(key)
    if number != redis_num:
        return JsonResponse({"code": 10103, "error": "Code error"})
    # orm更新
    try:
        user = UserProfile.objects.get(username=username, is_active=False)
    except Exception as e:
        print("Active error:", e)
        return JsonResponse({"code": 10104, "error": "Username error"})
    # 一查二改三保存
    user.is_active = True
    user.save()

    # 清缓存
    CODE_CACHE.delete(key)
    return JsonResponse({"code": 200, "data": "激活成成功"})

# FBV: Function Base Views   函数视图
# CBV: Class Base Views    类视图
# request.META.get("")   从请求头里面拿取数据(django会把请求头大写,并加上HTTP_)
class AddressView(BaseView):
    # @logging_check
    def get(self, request, username):
        """获取收件地址视图逻辑
            {"code": 200, "addresslist": [{}, {}]
        """
        # Address 查询
        user = request.myuser
        all_addres = Address.objects.filter(user_profile=user, is_active=True)

        addresslist = []
        for addresss in all_addres:
            address_dict = {

                    'id': addresss.id,
                    'address': addresss.address,
                    'receiver': addresss.receiver,
                    'receiver_mobile': addresss.receiver_mobile,
                    'tag': addresss.tag,
                    'postcode': addresss.postcode,
                    'is_default': addresss.is_default,
            }
            addresslist.append(address_dict)


        return JsonResponse({"code": 200, "addresslist": addresslist})
    # @logging_check
    def post(self, request, username):
        """
        新增地址视图逻辑
        :param request:
        :param username:
        :return:
        """
        # 1 获取请求体数据
        print("--------======")
        data = request.data
        receiver = data.get("receiver")
        receiver_phone = data.get("receiver_phone")
        address = data.get("address")
        postcode = data.get("postcode")
        tag = data.get("tag")



        # 存储
        user = request.myuser
        old_address = Address.objects.filter(user_profile=user, is_active=True)
        is_default = False
        if not old_address:
            is_default =True

        Address.objects.create(
            user_profile=user,
            receiver=receiver,
            address=address,
            postcode=postcode,
            receiver_mobile=receiver_phone,
            tag=tag,
            is_default=is_default
        )

        return JsonResponse({"code": 200, "data": "新增地址成功！"})


    # @logging_check
    def put(self, request, username):
        pass
    # @logging_check
    def delete(self, request, username, id):
        data = request.data
        add_id = data.get("id")
        user = request.myuser

        try:
            address = Address.objects.get(user_profile=user, id=add_id, is_active=True)
        except Exception as e:
            print("delete address error:", e)
            return JsonResponse({"code": 10104, "error": "Get address error"})

        # 删除地址
        if address.is_default:
            return JsonResponse({"code": 10105, "error": "Default address is not allowed delter"})
        address.is_active = False
        address.save()
        return JsonResponse({"code": 200, "data": "删除-地址成功！"})

class OAuthWeiBoUrlView(View):
    def get(self, request):
        """

        :param request:
        :return: {"code": 200, "oauth_url": ""}
        """
        weibo_api = OAuthWeiBoAPI(**settings.WEIBO_CONFIG)
        oauth_url = weibo_api.get_grant_url()

        return JsonResponse({"code": 200, "oauth_url": oauth_url})

class OAuthWeiBoView(View):
    def get(self, request):
        """
        获取access_token视图逻辑
        URL:https://api.weibo.com/oauth2/access_token
        请求方式：POST
        请求体数据：client_id,client_secret
        :param request:
        :return:
        """
        code = request.GET.get("code")
        if not code:
            return JsonResponse({"code": 10110, "error": "Not code"})
        post_url = "https://api.weibo.com/oauth2/access_token"
        post_data = {
            "client_id": settings.WEIBO_CONFIG.get("app_key"),
            "client_secret": settings.WEIBO_CONFIG.get("app_secret"),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.WEIBO_CONFIG.get("redirect_uri"),
        }

        access_html = requests.post(url=post_url, data=post_data,).json()
        print('---------------------')
        print(access_html)
        print('---------------------')

        # 绑定注册流程
        wuid = access_html.get("uid")
        access_token = access_html.get("access_token")

        # 到微博表中查询该wuid 是否存在
        # 情况1 不存在，用户第一次使用微博扫码[201]
        # 情况2 存在， 用户一定扫过码，但不一定绑定注册过
        #     2.1 已经和正式用户绑定过 [200]
        #     2.2 没有和正式用户绑定过 [201]
        try:
            weibo_user = WeiBoProfile.objects.get(wuid=wuid)
        except Exception as e:
            print("Get weibo user error:", e)
            # 一定是第一次扫码登录
            WeiBoProfile.objects.create(wuid=wuid, access_toke=access_token)
            return JsonResponse({"code": 201, "uid": "wuid"})
        user = weibo_user.user_profile
        if user:
            # 已经和正式用户绑定过
            return JsonResponse({"code": 200, "username": user.username, "token": make_token(user.username)})
        else:
            # 用户扫过码， 但没有和正式用户绑定过
            return JsonResponse({"code": 201, "uid": wuid})

    def post(self, request):
        """
        绑定注册用户视图逻辑
        获取请求体数据
        用户表插入数据
        微博表更新数据
        :param request:
        :return:
        """
        data = json.loads(request.body.decode())
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        phone = data.get("phone")
        wuid = data.get("uid")
        print("--------------------")
        print("uid --> ", wuid)
        print("--------------------")


        # 判断用户名是否可用
        try:
            user = UserProfile.objects.get(username=username)
            return JsonResponse({"code": 10111, "error": "用户名已存在"})
        except Exception as e:

            # 密码加密
            m = hashlib.md5()
            m.update(password.encode())
            pwd_md5 = m.hexdigest()

            # 执行插入和更新语句
            with transaction.atomic():
                sid = transaction.savepoint()
                try:
                    user = UserProfile.objects.create(username=username, passworld=pwd_md5, email=email, phone=phone)

                    # 更新微博表外键
                    weibo_user = WeiBoProfile.objects.get(wuid=wuid)
                    weibo_user.user_profile = user
                    weibo_user.save()
                except Exception as e:
                    print("Database error:", e)
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"code": 10112, "error": "请重新尝试"})

                # 提交事务
                transaction.savepoint_commit(sid)

            # 生成token
            token = make_token(username)

            # 发送激活邮件
            verify_url = get_verify_url(username)
            async_send_active_email(email, verify_url)

            return JsonResponse({"code": 200, "username": username, "token": token})



class DefaultAddressView(BaseView):
    # @logging_check
    def post(self, request, *args, **kwargs):
        """
        设置默认地址视图逻辑
        1 获取请求体数据[地址id]
        2 一查二改三保存
        3 返回响应
        :param request:
        :param username:
        :return:
        """
        user = request.myuser
        data = request.data
        uid = data.get("id")

        # 开启事务
        with transaction.atomic():
            # 创建存储点
            sid = transaction.savepoint()
            try:
                # 将原来的默认地址设置为非默认
                old_default = Address.objects.get(is_default=True, user_profile=user, is_active=True)
                old_default.is_default = False
                old_default.save()

                # 将现在地址设置为默认地址
                new_default = Address.objects.get(id=uid, user_profile=user, is_active=True)
                new_default.is_default = True
                new_default.save()
            except Exception as e:
                print("设置默认失败：", e)
                # 中间状态 回滚
                transaction.savepoint_rollback(sid)
                return JsonResponse({"code": 10106, "error": "设置默认地址失败了"})
            # 提交事物
            transaction.savepoint_commit(sid)
        return JsonResponse({"code": 200, "data": "设置默认地址成功"})

def sms_view(request):
    """
    短信验证视图逻辑
    1.获取请求体数据 （手机号）
    2 调用封装的短信发送接口
    :param request:
    :return:
    """
    # 获取数据
    data = json.loads(request.body.decode())
    phone = data.get("phone")
    code = random.randint(1000, 9999)

    # 判断如果三分钟内发过了，这直接返回，否则发送短信
    key = "sms_{}".format(phone)
    redis_code = SMS_CACHE.get(key)
    if redis_code:
        # 三分钟内已经发过，直接给用户返回
        return JsonResponse({"code": 10107, "error": {"message": "3分钟内只能发一次"}})
    # 存入redis中一份，有效期3分钟
    SMS_CACHE.set(key, code, 180)

    # 调用短信接口
    # sms_api = YunTonXunAPI(**settings.SMS_CONFIG)
    # sms_api.run(phone, code)
    # 异步任务
    async_send_message.delay(phone, code)

    # 存入验证码并设置过期时间
    expire_key = "sms_expire_{}".format(phone)
    SMS_CACHE.set(expire_key, code, 600)


    return JsonResponse({"code": 200, "data": "发送短信"})


def get_verify_url(uname):
    """ 功能函数： 生成邮件激活链接 """
    code_num = "%d" % random.randint(1000, 9999)
    code = "%s_%s" % (code_num, uname)
    code = base64.urlsafe_b64encode(code.encode()).decode()
    # 存储随机数
    key = "active_email_%s" % uname
    CODE_CACHE.set(key, code_num, 86400 * 3)
    # 激活链接
    verify_url = "http://127.0.0.1:7000/dadashop/templates/active.html?code=" + code
    return verify_url

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

# def send_active_email(email, verify_url):
#     """
#
#     :return:
#     """
#     subject = "达达商城激活邮件"
#     html_message = """
#     尊敬的用户你好，请点击激活链接进行激活～～
#     <a href="%s" target="_blank">点击此处</a>
#     """ % verify_url
#     send_mail(subject, "", "2108705337@qq.com", [email], html_message=html_message)


