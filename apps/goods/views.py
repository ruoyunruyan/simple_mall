from django import http
from django.shortcuts import render
from django.views import View
from apps.contents.utils import get_categories
from apps.orders.models import OrderGoods
from utils.response_code import RETCODE
from .models import GoodsCategory, SKU, GoodsVisitCount, SPU
from .utils import get_breadcrumb
from django.core.paginator import Paginator
from datetime import datetime


class CommentView(View):
    """商品评论"""
    def get(self, request, sku_id):

        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return render(request, '404.html')
        # 取同种类的所有商品
        skus = sku.spu.sku_set.all()

        # 获取商品评论
        comments = OrderGoods.objects.filter(sku__in=skus).exclude(comment='')
        # 商品评论总数
        # count = len(comments)
        comments_list = []
        for comment in comments:
            if comment.is_anonymous:
                username = '****'
            else:
                username = comment.order.user.username
            comments_list.append({
                'user': username,
                'comment': comment.comment,
                'score': comment.score
            })
        context = {
            'goods_comment_list': comments_list,
        }
        return http.JsonResponse(context)


class DetailView(View):
    """详情页"""
    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return render(request, '404.html')
        # 面包屑组件
        breadcrumb = get_breadcrumb(sku.category)
        # 商品分类三级菜单d
        categories = get_categories()

        # 获取当前商品的规格
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option_id)

        # 1. 获取当前商品的所有 sku
        # skus = sku.spu.sku_set.all()
        # 2. 获取当前商品的所有 sku
        skus = SKU.objects.filter(spu=sku.spu)

        # 构建不同参数的sku字典
        spec_sku_map = {}
        for s in skus:
            key = []
            s_specs = s.specs.order_by('spec_id')
            for spec in s_specs:
                key.append(spec.option_id)
            spec_sku_map[tuple(key)] = s.id

        # 获取当前商品的规格
        goods_specs = sku.spu.specs.order_by('id')

        for index, spec in enumerate(goods_specs):
            key = sku_key[:]
            spec_options = spec.options.all()
            for option in spec_options:
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 获取商品评论
        comments = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 商品评论总数
        count = len(comments)
        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
            'count': count
        }
        return render(request, 'detail.html', context)


class HotGoodsView(View):
    """热销商品排行"""
    def get(self, request, category_id):
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return http.JsonResponse({'code':RETCODE.OK, 'errmsg':'OK', 'hot_skus':hot_skus})


class ListView(View):
    """商品列表"""
    def get(self, request, category_id, page_num):

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseNotFound('GoodsCategory does not exist')

        breadcrumb = get_breadcrumb(category)

        categories = get_categories()

        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'
        else:
            sort_field = 'create_time'

        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)

        paginator = Paginator(skus, 5)
        # 总页数
        total_page = paginator.num_pages

        # 每一页的商品
        try:
            page_skus = paginator.page(page_num)
        except Exception as e:
            return http.HttpResponseNotFound('empty page')

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'category': category,
            'sort': sort,
            'page_num': page_num,
            'total_page': total_page,
            'page_skus': page_skus
        }
        return render(request, 'list.html', context)


class DetailVisitView(View):
    def post(self, request, category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseNotFound('缺少必传参数')
        # 1. 获取当天的日期
        date_str = datetime.now().strftime('%Y-%m-%d')  # 格式化日期字符串　
        date_today = datetime.strptime(date_str, '%Y-%m-%d')  # 将格式化日期字符串转换为日期格式

        # 2. 获取当天的日期
        # date_now = datetime.now()  # 获取当天的时间
        # date_today = datetime(date_now.year, date_now.month, date_now.day)  # 组合当天的时间

        try:
            count_date = category.goodsvisitcount_set.get(date=date_today)
        except Exception as e:
            count_date = GoodsVisitCount()
        try:
            count_date.count += 1
            count_date.category = category
            count_date.save()
        except Exception as e:
            return http.HttpResponseServerError('新增失败')
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
