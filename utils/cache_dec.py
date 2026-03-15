from django.core.cache import caches


def cache_check(**cache_kwargs):
    def _cache_check(func):
        def wrapper(self, request, *args, **kwargs):
            # 选择缓存配置项
            CACHES = caches["default"]
            if "cache" in cache_kwargs:
                CACHES = caches[cache_kwargs["cache"]]
            # 设置key   gb + id
            key = cache_kwargs["key_prefix"] + str(kwargs["sku_id"])
            # 查看redis中是否有缓存
            response = CACHES.get(key)
            if response:
                print("----数据来自于redis-----")
                return response
            # redis中没有缓存，从mysqlz中获取数据，并缓存到redis
            value = func(self, request, *args, **kwargs)
            exp = cache_kwargs.get("expire", 300)
            # 储存json数据
            CACHES.set(key, value, exp)
            return value
        return wrapper
    return _cache_check