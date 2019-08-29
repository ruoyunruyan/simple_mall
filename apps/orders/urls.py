from django.conf.urls import url
from . import views

urlpatterns = [
    # 订单处理
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='order'),

    # 提交订单　orders/commit/   OrderCommitView
    url(r'^orders/commit/$', views.OrderCommitView.as_view(), name='commit'),

    # 订单提交成功页面　orders/success/
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='success'),

    # 订单详情页  /orders/info/' + current + '/';
    url(r'^orders/info/(?P<page_num>\d+)/$', views.MyOrderView.as_view(), name='myorder'),

    # 显示商品评价
    url(r'^orders/judge/(?P<order_id>\d+)/$', views.GoodsJudgeView.as_view(), name='judge'),

    # 商品评价 orders/comment/
    url(r'^judge/comment/$',views.JudgeCommitView.as_view(), name='comment'),
]