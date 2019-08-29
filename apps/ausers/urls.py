from django.conf.urls import url
from . import views


urlpatterns = [

    # 1. 注册
    url(r'^register/$', views.RegisterView.as_view(), name='register'),

    # 2. 判断用户名是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view(), name='usernamecount'),

    # 3. 判断手机号是否重复  /mobiles/(?P<mobile>1[3-9]\d{9})/count/
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view(), name='mobiles'),

    # 4. 登陆
    url(r'^login/$', views.LoginView.as_view(), name='login'),

    # 5. 退出登陆
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),

    # 6. 个人中心
    url(r'^info/$', views.UserInfoView.as_view(), name='info'),

    # 7. 添加邮箱
    url(r'^emails/$', views.EmailView.as_view(), name='email'),

    # 8. 展示收货地址
    url(r'^address/$', views.AddressView.as_view(), name='address'),

    # 9. 新增收货地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view(), name='creat_address'),

    # 11. 修改和删除  addresses/(?P<address_id>\d+)/
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view(), name="update_address"),

    # 12. 设置默认地址
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view(), name="default_address"),

    # 13. 设置标题
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.TitleAddressView.as_view(), name="title_address"),

    # 14. 修改密码
    url(r'^password/$', views.ChangePwdView.as_view(), name="password"),

    # 15. 用户的浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistory.as_view(), name='history'),

    # 找回密码
    url(r'^find_password/$', views.ShowFindPasswordView.as_view(), name='show_find_pwd'),

    # 找回密码　第一步
    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/sms/token/$', views.FindPasswordView.as_view(), name='find_pwd_1'),

    # 发送短信
    url(r'^sms_codes/$', views.FindPasswordSendSmsView.as_view()),

    # 第二步　'/accounts/' + this.username + '/password/token/?sms_code=' + this.sms_code
    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/password/token/$', views.FindPwdCheckMsgView.as_view()),

    # 第三步/users/'+ this.user_id +'/password/
    url(r'^users/(?P<user_id>\d+)/password/$', views.ModifyPwdView.as_view())


]