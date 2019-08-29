from django.conf.urls import url
from . import views

urlpatterns = [

    # 请求图形验证码路由 image_codes/(?P<uuid>[\w-]+)/
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view(), name='image_code'),

    # 短信验证码路由/sms_codes/(?P<mobile>1[3-9]\d{9})/
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view(), name='sms_code'),

]
