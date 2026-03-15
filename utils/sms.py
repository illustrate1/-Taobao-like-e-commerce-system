"""
    第三方短信接口
"""
import time
import base64
import hashlib
import random
import requests


class YunTonXunAPI:
    def __init__(self, account_sid, auth_token, app_id, template_id):
        """
        差异化的内容做成应用
        :param account_sid: 账户id,控制台中获取
        :param auth_token: 授权令牌
        :param app_id:      应用id
        :param template_id: 模板短信id, 测试模板为1
        """
        self.account_sid = account_sid
        self.aut_token = auth_token
        self.app_id = app_id
        self.template_id = template_id

    def get_url(self):
        """ 获取情求的url地址"""
        return "https://app.cloopen.com:8883/2013-12-26/Accounts/{}/SMS/TemplateSMS?sig={}".format(self.account_sid, self.get_sig())


    def get_headers(self):
        """ 获取请求头 """
        s = self.account_sid + ':' + time.strftime("%Y%m%d%H%M%S")
        auth = base64.b64encode(s.encode()).decode()
        return {
            "Accept": "application/json;",
            "Content-Type": "application/json;charset=utf-8;",
            # requests模块会自动处理
            # "Content-Length": "256",
            "Authorization": auth,
        }

    def get_body(self, phone, code):
        """ 获取请求体 """

        return {
            "to": phone,
            "appId": self.app_id,
            "templateId": self.template_id,
            "datas": [code, "3"]
        }

    def run(self, phone, code):
        url = self.get_url()
        headers = self.get_headers()
        data = self.get_body(phone, code)
        return requests.post(url=url, headers=headers, json=data).json()

    def get_sig(self):
        """
            功能函数：生成请求url地址中的查询字符串sig
            md5(账户id + 授权令牌 +时间戳）
        """
        s = self.account_sid + self.aut_token + time.strftime("%Y%m%d%H%M%S")
        m = hashlib.md5()
        m.update(s.encode())

        return m.hexdigest().upper()
        pass

if __name__ == '__main__':
    config ={
        "account_sid": "2c94811c8cd4da0a018de9c1e38e2846",
        "auth_token": "bda67c0e3e524c8181efd9de24fd1e74",
        "app_id": "2c94811c8cd4da0a018de9c1e51c284d",
        "template_id": "1",
    }
    ytx = YunTonXunAPI(**config)
    phone = "16603822506"
    code = random.randint(1000, 9999)
    print(ytx.run(phone, code))