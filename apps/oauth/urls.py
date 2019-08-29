from django.conf.urls import url
from . import views

urlpatterns = [

    # 请求qq登陆url
    url(r'^qq/login/$', views.QQAuthURLView.as_view(), name='qqlogin'),

    # 根据回调的url参数获取 access_token 在 根据 access_token　获取 openid
    url(r'^oauth_callback/$', views.QQAuthUserView.as_view()),

    # 邮箱验证
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),

    # 请求sina登陆的url
    url(r'^sina/login/$', views.SinaAuthURLView.as_view(), name='sinalogin'),

    # sina用户验证
    url(r'^sina_callback/$', views.SinaAuthUserView.as_view()),
]
