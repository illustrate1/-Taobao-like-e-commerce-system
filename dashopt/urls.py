"""dashopt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from user import views as user_views
from dtoken import views as token_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # 测试跨域
    path('test_cors', views.test_cors),
    # 分布式锁
    path('v1/stock', views.stock_view),
    # 注册功能
    path('v1/users', user_views.users),
    # 登录功能
    path('v1/tokens', token_views.tokens),
    # 注册激活
    path('v1/users/', include('user.urls')),
    # 商品模块
    path("v1/goods/", include("goods.urls")),
    # 购物车模块
    path("v1/carts/", include("carts.urls")),
    # 订单模块
    path("v1/orders/", include("orders.urls")),
    #

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
