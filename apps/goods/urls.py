from django.conf.urls import url
from . import views

urlpatterns = [

    # 产品列表
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view(), name='list'),

    # 热销产品
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view(), name='hot'),

    # 商品详情
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view(), name='detail'),

    # 商品评价
    url(r'^comment/(?P<sku_id>\d+)/$', views.CommentView.as_view()),

    # 商品访问量　detail/visit/(?P<category_id>\d+)/
    url(r'^detail/visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view(), name='visit'),

]