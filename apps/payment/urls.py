from django.conf.urls import url
from . import views

urlpatterns = [
    # payment/(?P<order_id>\d+)/
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view(), name='pay_ment'),

    # 支付成功回调 payment/status/
    url(r'^payment/status/$', views.PaymentStatusView.as_view(), name='pay_status'),
]