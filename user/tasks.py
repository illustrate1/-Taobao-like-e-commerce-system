from dashopt.celery import app
from django.core.mail import send_mail
from django.conf import settings
from utils.sms import YunTonXunAPI
@app.task
def async_send_active_email(email, verify_url):
    """

    :return:
    """
    subject = "达达商城激活邮件"
    html_message = """
    尊敬的用户你好，请点击激活链接进行激活～～
    <a href="%s" target="_blank">点击此处</a>
    """ % verify_url
    send_mail(subject, "", "2108705337@qq.com", [email], html_message=html_message)

@app.task
def async_send_message(phone,  code):
    # 调用短信接口
    sms_api = YunTonXunAPI(**settings.SMS_CONFIG)
    sms_api.run(phone, code)