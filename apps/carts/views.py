from django.shortcuts import render
from django.views import View
import json
from django import http
from apps.goods.models import SKU
from django_redis import get_redis_connection
from utils.response_code import RETCODE
from utils.cookiesecret import CookieSecret


class CartsSelectAllView(View):
    """全选选项"""

    def put(self, request):
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')
        user = request.user
        if user.is_authenticated:
            # 修改 redis
            redis_client = get_redis_connection('carts')
            carts_data = redis_client.hgetall(user.id)
            for cart in carts_data.items():
                sku_id = cart[0].decode()  # 转换为字符串
                carts_dict = json.loads(cart[1].decode())
                if selected:
                    carts_dict['selected'] = True
                else:
                    carts_dict['selected'] = False
                redis_client.hset(user.id, sku_id, json.dumps(carts_dict))
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
        else:
            # 修改cookie
            carts_str = request.COOKIES.get('carts')
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
            if carts_str is not None:
                carts_dict = CookieSecret.loads(carts_str)
                for sku in carts_dict:
                    carts_dict[sku]['selected'] = selected
                carts_secret = CookieSecret.dumps(carts_dict)
                response.set_cookie('carts', carts_secret, max_age=14 * 24 * 3600)
            return response


class CartsView(View):
    """购物车功能"""

    def get(self, request):
        """购物车展示"""
        user = request.user
        # 判断用户是否登陆
        if user.is_authenticated:
            # 登陆　则返回 redis中的数据
            # 链接数据库
            carts_redis_client = get_redis_connection('carts')
            # 根据用户　user.id　获取用户的购物车数据
            carts_data = carts_redis_client.hgetall(user.id)
            # 因为获取的数据都是bytes　类型，所以需要先转换类型
            carts_dict = {int(sku[0].decode()): json.loads(sku[1].decode()) for sku in carts_data.items()}
        else:
            # 未登录返回 cookie 中的数据
            cookie_data = request.COOKIES.get('carts')
            # 判断获取的值是否有数据
            if cookie_data:
                # 获取道德数据进行解密
                carts_dict = CookieSecret.loads(cookie_data)
            else:
                # 没有则赋值为空
                carts_dict = {}
        # 获取 carts_dict　中的商品数据
        sku_ids = carts_dict.keys()
        # 获取所有的 商品 sku　信息
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'selected': str(carts_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts_dict.get(sku.id).get('count')),
            })
        context = {
            'cart_skus': cart_skus,
        }
        # 渲染购物车页面
        return render(request, 'cart.html', context)

    def post(self, request):
        """添加购物车"""
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 校验参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品不存在')
        # 判断前段传递的count是否为数字
        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count有误')
        # 判断前段传递的 selected 是否为bool值
        if not isinstance(selected, bool):
            return http.HttpResponseForbidden('参数selected有误')
        # 判断用户是否登陆
        user = request.user
        if user.is_authenticated:
            # 已经登陆，添加数据到 redis
            # 链接数据库
            carts_redis_client = get_redis_connection('carts')
            # 根据 user_id 存数据库获取用户的购买记录
            client_data = carts_redis_client.hgetall(user.id)
            # 判断用户是否存在够吗记录
            if not client_data:
                # 不存在则新建一条记录, 用用户的 user.id 作为键
                carts_redis_client.hset(user.id, sku_id, json.dumps({'count': count, 'selected': selected}))
            else:
                # 存在则读取记录判断是否存在浏览商品的购买记录
                # 注意 从redis 数据库中取出的数据为 bytes　类型
                # 所以先将　sku_id 转换为字符串，然后在转码，在于去除的数据进行比较
                if str(sku_id).encode() in client_data:
                    # 在购买记录中存在该商品的购买记录
                    # 根据　sku_id 取出商品的购买信息, 然后转码成字典类型
                    sku_dict = json.loads(client_data[str(sku_id).encode()].decode())
                    # 更新商品的 count　信息
                    sku_dict['count'] += count
                    # 将更新后的信息, 编码之后重新写入数据库
                    carts_redis_client.hset(user.id, sku_id, json.dumps(sku_dict))
                else:
                    # 在购买记录中不存在该商品的购买记录
                    carts_redis_client.hset(user.id, sku_id, json.dumps({'count': count, 'selected': selected}))
            # 返回前段相应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

        else:
            # 未登录，添加数据到 浏览器 cookie
            # 从　cookie 中取出　carts
            cart_str = request.COOKIES.get('carts')
            # 判断取出的 carts 中是否有数据
            if cart_str:
                # 将取出的 cart_str 进行解密
                cart_dic = CookieSecret.loads(cart_str)
            else:
                # 不存在则新建一条数据
                cart_dic = {}

            # 判断浏览的商品是否存在
            if sku_id in cart_dic:
                # 存在则取出其中的 count　进行添加
                cart_dic[sku_id]['count'] += count
            else:
                # 不存在则直接赋值
                cart_dic[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            # 将去除的 cart_dic　进行加密
            cookie_cart_secret = CookieSecret.dumps(cart_dic)
            # 生成相应对象
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            # 添加 cookie 信息
            response.set_cookie('carts', cookie_cart_secret, max_age=24 * 30 * 3600)
            # 返回相应对象
            return response

    def put(self, request):
        """修改购物车"""
        # 接受前段数据
        carts_dict = json.loads(request.body.decode())
        sku_id = carts_dict.get('sku_id')
        count = carts_dict.get('count')
        selected = carts_dict.get('selected', True)
        # 参数校验
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品sku_id不存在')
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count有误')
        # 判断 selected 是否为bool类型
        # 1. 判断是否有值
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')
        user = request.user
        # 判断用户是否登陆
        if user.is_authenticated:
            # 用户登陆，修改redis数据
            # 链接数据库
            redis_client = get_redis_connection('carts')
            new_data = {'count': count, 'selected': selected}
            # 直接覆盖以前的数据
            redis_client.hset(user.id, sku_id, json.dumps(new_data))
        else:
            # 用户未登录，修改cookie数据
            # 取出cookie数据
            cookie_str = request.COOKIES.get('carts')
            # 判断是否有数据
            if cookie_str:
                cookie_dict = CookieSecret.loads(cookie_str)
            else:
                cookie_dict = {}
            # 覆盖以前的数据
            cookie_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将其加密
            cookie_secret = CookieSecret.dumps(cookie_dict)
        # 构建前端的数据
        cart_sku = {
            'id': sku_id,
            'count': count,
            'selected': selected,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': sku.price,
            'amount': sku.price * count,
        }
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        if not user.is_authenticated:
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cookie_secret, max_age=24 * 30 * 3600)
        return response

    def delete(self, request):
        """删除购物车"""
        # 接收参数
        sku_id = json.loads(request.body.decode()).get('sku_id')
        # 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('该商品不存在')
        user = request.user
        # 判断用户是否登陆
        if user.is_authenticated:
            # 操作 redis
            redis_client = get_redis_connection('carts')
            # 删除对应的字段
            redis_client.hdel(user.id, sku_id)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
        else:
            # 操作　cookie
            cookie_str = request.COOKIES.get('carts')
            # 判断是否有数据
            if cookie_str:
                cookie_dict = CookieSecret.loads(cookie_str)
            else:
                cookie_dict = {}
            # 创建相应对象
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
            # 如果sku_id 存在则删除
            if sku_id in cookie_dict:
                del cookie_dict[sku_id]
                cookie_secret = CookieSecret.dumps(cookie_dict)
                response.set_cookie('carts', cookie_secret, max_age=14 * 24 * 3600)
            return response


class CartsSimpleView(View):
    """简单展示购物车"""

    def get(self, request):
        user = request.user
        # 判断用户是否登陆，以确定展示的购物车数据
        if user.is_authenticated:
            carts_redis_client = get_redis_connection('carts')
            carts_data = carts_redis_client.hgetall(user.id)
            # 转换格式
            cart_dict = {int(data[0].decode()): json.loads(data[1].decode()) for data in carts_data.items()}
        else:
            # 用户未登录，查询cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = CookieSecret.loads(cart_str)
            else:
                cart_dict = {}
        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })

        # 响应json列表数据
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})
