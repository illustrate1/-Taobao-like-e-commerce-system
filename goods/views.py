from django.http import JsonResponse
from django.views import View
from django.conf import settings

from goods.models import Catalog, SKU, SPU, SKUImage, SPUSaleAttr, SaleAttrValue, SKUSpecValue

from utils.cache_dec import cache_check

class GoodsIndexView(View):
    def get(self, request):
        """ 首页展示视图逻辑 """
        print("----mysel-------")
        data = []
        all_catalog = Catalog.objects.all()
        for cata in all_catalog:
            cata_dict = {}
            cata_dict["catalog_id"] = cata.id
            cata_dict["catalog_name"] = cata.name
            # cata --> spu -->sku
            spu_ids = SPU.objects.filter(catalog=cata).values("id")
            sku_list = SKU.objects.filter(spu__in=spu_ids)[:3]
            sku = []
            for one_sku in sku_list:
                d = {
                    "skuid": one_sku.id,
                    "caption": one_sku.caption,
                    "name": one_sku.name,
                    "price": one_sku.price,
                    "image": str(one_sku.default_image_url)
                }
                sku.append(d)
            cata_dict["sku"] = sku
            data.append(cata_dict)
        result = {
            "code": 200,
            "data": data,
            "base_url": settings.PIC_URL,
        }


        return JsonResponse(result)

class GoodsDetailView(View):
    @cache_check(key_prefix='gd', key_param='sku_id', cache='goods_detail', expire=60)
    def get(self, request, sku_id):
        print("----数据来在于mysql数据库-----")
        try:
            sku_item = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 10300, "error": "没有此商品"})
        data = {}
        # 类1： 类别id 类别名name SKU-SPU-Catalog
        sku_catalog = sku_item.spu.catalog
        data["catalog_id"] = sku_catalog.id
        data["catalog_name"] = sku_catalog.name

        # 类2： sku相关的
        data["name"] = sku_item.name
        data["caption"] =sku_item.caption
        data["price"] = sku_item.price
        data["image"] = str(sku_item.default_image_url)
        data["spu"] = sku_item.spu.id
        # 类3： 详情图片
        img_query = SKUImage.objects.filter(sku=sku_item)
        if img_query:
            data["detail_image"] = img_query[0]
        else:
            data["detail_image"] = ""

        # 类4：销售属性值的id列表和name列表

        attr_value_query = sku_item.sale_attr_value.all()
        data["sku_sale_attr_val_id"] = [i.id for i in attr_value_query]
        data["sku_sale_attr_names"] = [i.name for i in attr_value_query]

        # 类5：销售属性名的id列表和name列表
        attr_name_query = SPUSaleAttr.objects.filter(spu=sku_item.spu)
        data["sku_sale_attr_id"] = [i.id for i in attr_name_query]
        data["sku_sale_attr_names"] = [i.name for i in attr_name_query]

        # 体现关系
        sku_all_sale_attr_vals_id = {}
        sku_all_sale_attr_vals_name = {}
        for id in data["sku_sale_attr_id"]:
            sku_all_sale_attr_vals_id[id] = []
            sku_all_sale_attr_vals_name[id] = []
            item_query = SaleAttrValue.objects.filter(spu_sale_attr=id)
            for item in item_query:
                sku_all_sale_attr_vals_id[id].append(item.id)
                sku_all_sale_attr_vals_name[id].append((item.name))
        data["sku_all_sale_attr_vals_id"] = sku_all_sale_attr_vals_id
        data["sku_all_sale_attr_vals_name"] = sku_all_sale_attr_vals_name

        # 类6和类7 规格属性相关
        spec = {}
        spec_query = SKUSpecValue.objects.filter(sku=sku_item)
        for spec_obj in spec_query:
            value = spec_obj.name
            key = spec_obj.spu_spec.name
            spec[key] = value
        data["spec"] = spec

        result = {
            "code": 200,
            "data": data,
            "base_url": settings.PIC_URL
        }
        return JsonResponse(result)




