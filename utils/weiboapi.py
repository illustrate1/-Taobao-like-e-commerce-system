"""
    第三方
"""
from urllib.parse import urlencode

import requests


class OAuthWeiBoAPI:
    def __init__(self, app_key, app_secret, redirect_uri):
        self.app_key = app_key
        self.ap_secret = app_secret
        self.redirect_uri = redirect_uri

    def get_grant_url(self):
        """
        获取微博授权登录页的url地址[接口文档]
        :return:
        """
        params = {
            "client_id": self.app_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }

        return "https://api.weibo.com/oauth2/authorize?" + urlencode(params)

class OAuthWeiBoView:
    def get(self):
        """
        获取access_token视图逻辑
        URL:https://api.weibo.com/oauth2/access_token
        请求方式：POST
        请求体数据：client_id,client_secret
        :param request:
        :return:
        """

        post_url = "https://api.weibo.com/oauth2/access_token"
        post_data = {
            "client_id": "860863778",
            "client_secret": "85efa0eaeebfcf833d74cc97d055963b",
            "grant_type": "authorization_code",
            "code": "681b06baf439d8c68c6554df7a0eaa1e",
            "redirect_uri": "http://localhost:7000/dadashop/templates/callback.html",
        }
        temp = {
            'redirect_uri': 'http://localhost:7000/dadashop/templates/callback.html',
            'code': '681b06baf439d8c68c6554df7a0eaa1e',
            'client_secret': '85efa0eaeebfcf833d74cc97d055963b ',
            'grant_type': 'authorization_code',
            'client_id': '860863778'
                }

        access_html = requests.post(url=post_url, data=post_data,).json()
        print('------------------')
        print('------------------')

        print(access_html)
        print('------------------')
if __name__ == '__main__':
    config = {
        "app_key": "860863778",
        "app_secret": "85efa0eaeebfcf833d74cc97d055963b ",
        "redirect_uri": "http://localhost:7000/dadashop/templates/callback.html",
    }
    weibo_api = OAuthWeiBoAPI(**config)
    print(weibo_api.get_grant_url())
    api = OAuthWeiBoView()
    api.get()

