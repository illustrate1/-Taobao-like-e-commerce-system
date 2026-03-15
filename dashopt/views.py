import redis
from django.http import HttpResponse, JsonResponse
from goods.models import SKU


def test_cors(request):
    """测试跨域"""

    return HttpResponse("测试跨域")


pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(connection_pool=pool)


def stock_view(request):
    """ 测试Redis 分布式锁 """
    # Redis 分布式使用锁
    with r.lock("dashopt:stock", blocking_timeout=5) as lock:

        sku = SKU.objects.get(id=1)
        sku.stock -= 1
        sku.save()

    return JsonResponse({"code": 200})