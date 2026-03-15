from django.db import models
from utils.basemodel import BaseModel


class UserProfile(BaseModel):
    """用户表"""
    # 用户名  密码 邮箱  手机号 是否激活 创建时间
    username = models.CharField(max_length=11, verbose_name="用户名", unique=True)
    passworld = models.CharField(max_length=32)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    is_active = models.BooleanField(default=False, verbose_name='是否激活')

    class Meta:
        db_table = "user_user_profile"


class Address(BaseModel):
    """
    用户地址表
    """
    # 外键[用户表：地址表  1：n]
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # 收件人
    receiver = models.CharField(verbose_name='收件人', max_length=10)
    address = models.CharField(verbose_name="收件地址", max_length=100)
    postcode = models.CharField(verbose_name='邮编', max_length=6)
    receiver_mobile = models.CharField(verbose_name="手机号", max_length=11)

    # 标签 [家 ，公司，学校 ]
    tag = models.CharField(verbose_name='标签', max_length=11)
    # 是否为默认地址
    is_default = models.BooleanField(verbose_name="是否为默认地址", default=False)
    # 伪删除
    is_active = models.BooleanField(verbose_name='是否删除', default=True)

    class Meta:
         db_table = "user_address"

class WeiBoProfile(BaseModel):
    # 微博表
    # 外键：用户和微博 1：1 关系
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, null=True)
    wuid = models.CharField(verbose_name="微博uid", max_length=10, db_index=True)
    access_toke = models.CharField(verbose_name="微博授权令牌", max_length=32)

    class Meta:
        db_table = "user_weibo_profile"

