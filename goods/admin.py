from django.contrib import admin
from .models import SKU
from django.core.cache import caches


GOODS_INDEX_CACHE = caches["goods_index"]
GOODS_DETAIL_CACHE = caches["goods_detail"]


@admin.register(SKU)  # 注册管理员可使用表
class SKUAdmin(admin.ModelAdmin):
    # 重写Model Admin中的save_model()方法
    def save_model(self, request, obj, form, change):
        # 执行父类方法，更新mysql数据库
        super().save_model(request, obj, form, change)
        # 清除redis缓存
        GOODS_INDEX_CACHE.clear()
        print("更新数据时首页缓存清除～～～")

        # 清除详情页缓存
        key = "db%s" % obj.id
        GOODS_DETAIL_CACHE.delete(key)
        print("更新数据时详情页缓存清除～～～")

    def delete_model(self, request, obj):
        # 执行父类方法，更新mysql数据库
        super().delete_model(request, obj)
        # 清除redis缓存
        GOODS_INDEX_CACHE.clear()
        print("更新数据时首页缓存清除～～～")

        # 清除详情页缓存
        key = "db%s" % obj.id
        GOODS_DETAIL_CACHE.delete(key)
        print("更新数据时详情页缓存清除～～～")
