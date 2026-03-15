from django.urls import path
from . import views


urlpatterns = [
    # 用户邮件激活
    path("activation", views.active_view),
    # 地址管理(新增和查询)
    path("<str:username>/address", views.AddressView.as_view()),
    # 地址管理(删除和修改)
    path("<str:username>/address/<int:id>", views.AddressView.as_view()),
    # 设置默认地址
    path("<str:uername>/address/default", views.DefaultAddressView.as_view()),
    # 短信验证 (v1/users/sms/code)
    path("sms/code", views.sms_view),
    # 微博登录[获取授权登录页]：
    path("weibo/authorization", views.OAuthWeiBoUrlView.as_view()),
    # 微博登录[获取access_token]:
    path("weibo/users", views.OAuthWeiBoView.as_view()),
]