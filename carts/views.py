from django.http import JsonResponse
from goods.models import SKU
from django.core.cache import caches
from django.conf import settings

from utils.baseview import BaseView


CARTS_CACHE = caches["carts"]

class CartsView(BaseView):
    def post(self, request, *args, **kwargs):
        """
        添加购物车视图逻辑
        1 获取请求体数据
        2 检查上下架状态

        :param request:
        :param username:
        :return:
        """
        data = request.data
        sku_id = data.get("sku_id")
        count = int(data.get("count"))
        # 校验上下架状态
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except Exception as e:
            return JsonResponse({"code": 10400, "error": "该商品已下架"})
        # 校验库存量
        if count > sku.stock:
            return JsonResponse({"code": 10401, "error": "库存量不足"})

        # 3 存入redis 数据库
        # 3.1 获取改用户现在购物车的所有数据
        user = request.myuser
        cache_key = self.get_cache_key(user.id)
        carts_data = self.get_carts_all_data(cache_key)
        # 3.2 考虑数据合并的
        if not carts_data:
            # 用户第一次添加购物车
            li = [count, 1]
        else:
            # 拿取该商品数据
            li = carts_data.get(sku_id)
            if not li:
                li = [count, 1]
            else:
                new_count = li[0] + count
                if new_count > sku.stock:
                    return JsonResponse({"code": 10402, "error": "库存量不足"})
                li = [new_count, 1]

        # 存入redis数据库
        carts_data[sku_id] = li
        CARTS_CACHE.set(cache_key, carts_data)

        result= {
            "code": 200,
            "data": {
                "carts_count": len(carts_data)
            },
            "base_url": settings.PIC_URL,
        }
        return JsonResponse(result)

    def get(self, request, *args, **kwargs):
        """
        查询购物车视图逻辑
        先从redis中获取数据
        根据sku_id获取mysql中数据
        :param request:
        :param username:
        :return:
        """
        user = request.myuser
        sku_list = self.get_carts_list(user.id)
        result = {
            "code": 200,
            "data": sku_list,
            "base_url": settings.PIC_URL
        }
        return JsonResponse(result)

    def get_cache_key(self, user_id):
        """
        功能函数：生成key

        :param user_id:
        :return:
        """

        return "carts_%s" % user_id

    def get_carts_all_data(self, cache_key):
        """
        功能函数：获取该用户所有数据
        :param cache_key:
        :return:
        """
        data = CARTS_CACHE.get(cache_key)

        if not data:
            return {}
        return data

    def merge_carts(self, offline_data, user_id):
        """
        合并购物车
        :param offline_data: 离线购物车数据
        :return: 合并购物车商品种类数量
        """
        cache_key = self.get_cache_key(user_id)
        carts_data = self.get_carts_all_data(cache_key)
        if not offline_data:
            return len(carts_data)

        for sku_dict in offline_data:
            sku_id = sku_dict.get("id")
            count = sku_dict.get("count")
            if sku_id in carts_data:
                last_count = carts_data[sku_id][0] + int(count)
                carts_data[sku_id][0] = last_count
            else:
                carts_data[sku_id] = [count, 1]
        # 合并完成后更新到redis
        CARTS_CACHE.set(cache_key, carts_data)
        # 返回合并后的商品总数量
        return len(carts_data)

    def get_carts_list(self, id):
        """
        确认订单页
        :param id:
        :return:
        """

        cache_key = self.get_cache_key(id)
        carts_data = self.get_carts_all_data(cache_key)
        sku_query = SKU.objects.filter(id__in=carts_data.keys())
        sku_list = []
        for sku in sku_query:
            value_query = sku.sale_attr_value.all()
            sku_dict = {
                "id": sku.id,
                "name": sku.name,
                "count": carts_data[str(sku.id)][0],
                "selected": carts_data[str(sku.id)][1],
                "default_image_url": str(sku.default_image_url),
                "price": sku.price,
                "sku_sale_attr_name": [i.spu_sale_attr.name for i in value_query],
                "sku_sale_attr_val": [i.name for i in value_query],
            }
            sku_list.append(sku_dict)
        return sku_list

    def get_carts_dict(self, id):
        """
        功能函数：筛选购物车中 选中状态的商品的字典
        :param id:
        :return:
        """
        cache_key = self.get_cache_key(id)
        carts_data = self.get_carts_all_data(cache_key)

        return {k: v for k, v in carts_data.items() if v[1] == 1}

    def del_carts_dict(self, id):
        """
        功能内函数：清除购物车数据[选中状态]
        :param id:
        :return:
        """
        cache_key = self.get_cache_key(id)
        carts_data = self.get_carts_all_data(cache_key)

        carts_dict = {}
        for k, v in carts_data.items():
            if v[1] == 0:
                carts_dict[k] = v

        # 更新到redis
        CARTS_CACHE.set(cache_key, carts_dict)

        return len(carts_dict)



