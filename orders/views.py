import time

from django.db import transaction
from django.http import JsonResponse

from orders.models import OrderInfo, OrderGoods
from utils.baseview import BaseView
from user.models import Address
from django.conf import settings
from carts.views import CartsView
from goods.models import SKU


class AdvanceView(BaseView):
    def get(self, request, username):
        """ 确认订单页视图逻辑 """
        # 1 第一个列表：address[{},{}]
        user = request.myuser
        address = self.get_addresses(user.id)
        # 2 第二个列表
        # 区分链条：购物车-0 还是立即购买 -1
        typ = request.GET.get("settlement_type")
        if typ == "0":
            # 从购物车来的
            sku_list = self.get_order_sku_list(user.id)
        else:
            # 详情页立即购买
            sku_id = request.GET.get("sku_id")
            buy_num = request.GET.get("buy_num")
            if not all([sku_id, buy_num]):
                return JsonResponse({"code": 10500, "error": "参数有误"})
            sku_list = self.get_sku_list(sku_id, buy_num)
        result = {
            "code": 200,
            "data": {
                "addresses": address,
                "sku_list": sku_list
            },
            "base_url": settings.PIC_URL

        }
        return JsonResponse(result)
    def get_addresses(self, uid):
        """
        获取用户所有地址
        :param user:
        :return: [{},{},...]   默认地址作为第一个元素
        """
        all_address = Address.objects.filter(user_profile_id=uid, is_active=True)
        addresses = []
        for add in all_address:
            add_dict = {
                "id": add.id,
                "name": add.receiver,
                "mobile": add.receiver_mobile,
                "title": add.tag,
                "address": add.address
            }
            if add.is_default:
                addresses.insert(0, add_dict)
            else:
                addresses.append(add_dict)
        return addresses

    def get_order_sku_list(self, id):
        """
        功能函数：获取订单确认页商品数据
        :param id:
        :return:
        """
        sku_list = CartsView().get_carts_list(id)
        # 筛选出选中状态为1的商品  [{}, {},...]
        sku_list = [sku for sku in sku_list if sku["selected"]==1]


        return sku_list

    def get_sku_list(self, sku_id, buy_num):
        """
        功能函数：立即购买链条订单商品显示
        :param sku_id:
        :param buy_num:
        :return: sku_list [8个键值对]
        """
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except Exception as e:
            return JsonResponse({"code": 10501, "error": "改商品已下架"})
        value_query = sku.sale_attr_value.all()
        sku_list = [
            {
                "id": sku.id,
                "name": sku.name,
                "count": int(buy_num),
                "selected": 1,
                "default_image_url": str(sku.default_image_url),
                "price": sku.price,
                "sku_sale_attr_name": [i.spu_sale_attr.name for i in value_query],
                "sku_sale_attr_val": [i.name for i in value_query],
            }
        ]
        return sku_list

class OrderInfoView(BaseView):
    def post(self, request, username):
        """
        生成订单视图逻辑
        1 获取请求体数据
        2 订单表中插入数据
        3 跟新库存和销量
        4 订单商品表中插入数据库
        :param request:
        :param username:
        :return:
        """

        data = request.data
        address_id = data.get("address_id")

        user = request.myuser
        # 时间+用户id
        order_id = time.strftime("%Y%m%d%H%M%S") + str(user.id)
        total_amount = 0
        total_count = 0

        # 地址
        try:
            add = Address.objects.get(id=address_id, user_profile=user, is_active=True)
        except Exception as e:
            print("----->address error",e)
            return JsonResponse({"code": 10504, "error": "地址异常"})

        # 开启事务
        with transaction.atomic():
            sid = transaction.savepoint()
            # 1 订单表中插入数据
            print("-------------------777---------------------")
            order = OrderInfo.objects.create(
                user_profile=user,
                order_id=order_id,
                total_amount=total_amount,  # 总金额
                total_count=total_count,    # 总数量
                pay_method=1,
                freight=1,
                status=1,
                receiver=add.receiver,
                address=add.address,
                receiver_mobile=add.receiver_mobile,
                tag=add.tag
            )
            print("-------------------666---------------------")
            # 2 更新sku库存和销量
            carts_dict = self.get_carts_dict(user.id)
            skus = SKU.objects.filter(id__in=carts_dict.keys())
            print("-------------------555---------------------")
            for sku in skus:
                while True:
                    # 插入订单商品表
                    count = int(carts_dict[str(sku.id)][0])
                    if count > sku.stock:
                        # 回滚
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({"code": 10505, "error": "库存量不足"})
                    order_version = sku.version
                    result = SKU.objects.filter(id=sku.id, version=order_version).update(
                        stock=sku.stock - count,
                        sales=sku.sales + count,
                        version=order_version + 1
                    )
                    if result == 0:
                        continue
                    else:
                        break
                # 商品表插入数据
                OrderGoods.objects.create(
                    order_info_id=order_id,
                    sku_id=sku.id,
                    price=sku.price,
                    count=count,
                )
                total_amount += sku.price * count  # 总价
                total_count += count
            # 更新订单表的总价和总数量
            order.total_amount = total_amount
            order.total_count = total_count
            order.save()

            # 提交事务
            transaction.savepoint_commit(sid)
        # 清除购物车中已转化为有效订单商品数据
        carts_count = CartsView().del_carts_dict(user.id)
        # 组织数据返回
        result = {
            "code": 200,
            "data": {
                'saller': '达达商城',
                'total_amount': total_amount,
                'order_id': order_id,
                'carts_count': carts_count,
                'pay_url': ''
            }
        }

        return JsonResponse(result)

    def get_carts_dict(self, id):
        """
        功能函数：筛选购物车中 选中状态的商品的字典
        :param id:
        :return:
        """

        return CartsView().get_carts_dict(id)
