from django.conf.urls import url

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

from .views import statistical, users, spu_spec, spu_spec_name, sku, sku_image, spu, spec_options, brand, channel, \
    order, permission, group, admin

urlpatterns = [

    # JWT 认证
    url(r'^authorizations/$', obtain_jwt_token),

    # 用户总数统计
    url(r'^statistical/total_count/$', statistical.UserCountView.as_view()),

    # 日增用户
    url(r'^statistical/day_increment/$', statistical.UserIncrementDailyView.as_view()),

    # 日活跃用户统计
    url(r'^statistical/day_active/$', statistical.UserActiveDailyView.as_view()),

    # 日下单用户数量
    url(r'^statistical/day_orders/$', statistical.UserOrderDailyView.as_view()),

    # 月增用户统计
    url(r'^statistical/month_increment/$', statistical.UserIncrementMonthView.as_view()),

    # 日分类商品访问量
    url(r'^statistical/goods_day_views/$', statistical.GoodsCategoryVisitView.as_view()),

    # 获取用户信息
    url(r'^users/$', users.UserView.as_view()),

    # 获取所有的spu规格名称, 用户spu规格编辑时的下拉选项
    url(r'^goods/simple/$', spu_spec_name.SPUNameView.as_view()),

    # sku添加时获取第三级分类
    url(r'^skus/categories/$', sku.CategoryView.as_view()),

    # 获取SPU商品规格信息
    url(r'goods/(?P<pk>\d+)/specs/$', sku.SpuSpecsView.as_view()),

    # 获取sku表的 id, name 字段
    url(r'^skus/simple/$', sku_image.SKUSimpleView.as_view()),

    # 简单的规格信息, 用于下拉选项
    url(r'^goods/specs/simple/$', spec_options.SPUSpecsSimpleView.as_view()),

    # 获取类别
    url(r'^goods/categories/$', channel.CategoryView.as_view()),

    # 获取频道
    url(r'^goods/channel_types/$', channel.ChannelGroupView.as_view()),

    # 获取品牌
    url(r'^goods/brands/simple/$', spu.BrandView.as_view()),

    # 权限 content
    url(r'^permission/content_types/$', permission.ContentView.as_view()),

    # 简单用户权限, 用于选项框
    url(r'^permission/simple/$', group.PermissionSimpleView.as_view()),

    # 获取用户组
    url(r'^permission/groups/simple/$', admin.UserModelView.as_view({'get': 'simple'})),

]

router = DefaultRouter()
# 为spu规格生成路由规则
router.register('goods/specs', spu_spec.SPUModelViewSetView, base_name='specs')

# SKU图片
router.register('skus/images', sku_image.SKUImageView, base_name='sku_image')

# 为sku生成路由规则
router.register('skus', sku.SKUModelViewSet, base_name='skus')

# 品牌　brand
router.register('goods/brands', brand.BrandModelView, base_name='brand')

# 商品频道组
router.register('goods/channels', channel.ChannelModelView, base_name='channel')

# 为spu生成路由规则
router.register('goods', spu.SPUView, base_name='spu')

# 商品规格选项
router.register('specs/options', spec_options.SpecificationModelViewSet, base_name='specs_options')

# 商品频道三级分类
router.register('goods/channel/categories', spu.CategoryView, base_name='goods_channel')

# 订单
router.register('orders', order.OrderModelView, base_name='order')

# 权限
router.register('permission/perms', permission.PermissionView, base_name='permission')

# 用户组
router.register('permission/groups', group.GroupModelView, base_name='group')

# 管理员
router.register('permission/admins', admin.UserModelView, base_name='admin')

urlpatterns += router.urls
