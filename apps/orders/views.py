from datetime import datetime
from decimal import Decimal
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from apps.ausers.models import Address
from django_redis import get_redis_connection
import json
from apps.goods.models import SKU
from utils.response_code import RETCODE
from .models import OrderInfo, OrderGoods
from django.db import transaction
from datetime import datetime


class OrderSettlementView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # 收货地址
        addresses = Address.objects.filter(user=user, is_deleted=False)
        # 商品列表
        redis_client = get_redis_connection('carts')
        carts_data = redis_client.hgetall(user.id)
        carts_dict = {}
        for data in carts_data.items():
            sku_id = int(data[0].decode())
            sku_dict = json.loads(data[1].decode())
            if sku_dict['selected']:
                carts_dict[sku_id] = sku_dict
        # 获取所有商品
        # 计算商品的数量及价格
        total_count = 0
        total_amount = Decimal(0.00)
        skus = SKU.objects.filter(id__in=carts_dict)
        for sku in skus:
            # 商品的数量
            sku.count = carts_dict[sku.id].get('count')
            # 商品的总价
            sku.amount = sku.count * sku.price

            # 累加计算所有商品的数量及价格总和
            total_count += sku.count
            total_amount += sku.amount

        # 运费
        freight = Decimal('10.00')

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight,
            'default_address_id': user.default_address_id
        }
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredMixin, View):
    """订单提交处理"""
    def post(self, request):
        # 接收前段数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 校验参数是否完整
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('参数不完整')
        # 判断收货地址是否存在
        try:
            address = Address.objects.get(id=address_id, is_deleted=False)
        except Exception as e:
            return http.HttpResponseForbidden('收货地址不存在')
        # 判断支付方式是否支持
        if int(pay_method) not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('不支持该支付方式')

        user = request.user
        date_str = datetime.now().strftime('%Y%m%d%H%M%S')
        order_id = date_str + '%09d' % user.id

        # 事务起始位置
        with transaction.atomic():
            # 设置事务的保存点
            save_point = transaction.savepoint()
            try:
                # 创建订单
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    address=address,
                    user=user,
                    total_count=0,
                    total_amount=Decimal('0'),
                    pay_method=pay_method,
                    freight=Decimal('10.00'),
                    # 订单状态，如果是货到付款就是未发货，如果是alipay就是未付款
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT']
                    # status = OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                    # 'ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 获取订单的商品信息
                redis_client = get_redis_connection('carts')
                # 获取用户的所有订单
                client_data = redis_client.hgetall(user.id)
                # 获取订单中选中的商品
                goods_selected = {}
                for data in client_data.items():
                    sku_id = int(data[0].decode())
                    sku_data = json.loads(data[1].decode())
                    if sku_data['selected']:
                        goods_selected[sku_id] = sku_data

                # 循环遍历商品信息,判断商品的库存是否足够
                # 获取所有的商品 sku_ids
                sku_ids = goods_selected.keys()

                # 查询集的惰性机制及缓存机制会影响下边的查询，所以这里使用循环查询
                # skus = SKU.objects.filter(id__in=goods_selected.keys())
                for sku_id in sku_ids:

                    while True:

                        sku = SKU.objects.get(id=sku_id)
                        # 原始库存
                        origin_stock = sku.stock
                        # 原始销量
                        origin_sales = sku.sales

                        # 购买数量
                        sku_count = goods_selected[sku_id]['count']

                        # 如果库存不足则返回前段数据
                        if origin_stock < sku_count:
                            # 以为是判断语句，不会抛出错误，所以要在这里设置回滚操作
                            transaction.savepoint_rollback(save_point)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # 如果足够，则商品的库存减少，销量增加，同时商品的SPU表中的销量也要增加
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # import time
                        # time.sleep(5)
                        # 更新后库存,销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 修改数据的的时候使用乐观锁
                        result = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        # 更新失败　1. 商品库存不足　2.　修改商品数据的时候，商品的库存已经被其他订单修改
                        # 所以为防止第一种情况，需要循环尝试下单
                        if result == 0:
                            continue

                        sku.spu.sales += sku_count
                        sku.spu.save()

                        # 生成订单数据
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )
                        # 先订单中的商品数量及总价添加
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)
                        # 全部成功则退出循环
                        break

                # 循环遍历之后，给订单的总价添加运费, 然后保存
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_point)
                return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单失败'})
            # 执行成功则提交事务
            transaction.savepoint_commit(save_point)
        # 清楚购物城中已经提交订单的数据, 这里用的是拆包
        redis_client.hdel(user.id, *goods_selected)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


class OrderSuccessView(LoginRequiredMixin, View):
    """订单提交成功页面"""
    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_methos')
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)


class MyOrderView(LoginRequiredMixin, View):
    # 订单展示
    def get(self, request, page_num):
        # 获取用户
        user = request.user
        # 获取所有订单
        orders = OrderInfo.objects.filter(user=user).order_by('-order_id')
        # 将订单分页，每４个订单为１页
        paginator = Paginator(orders, 4)
        # 获取总页数
        total_page = paginator.num_pages
        # 请求页的订单
        try:
            page_orders = paginator.page(page_num)
        except Exception as e:
            return http.HttpResponseNotFound('empty page')

        orders_list = []
        for order in page_orders:

            # 获取支付方式
            pay_method = order.pay_method

            # 查询支付表中是否有订单的支付记录
            trades = order.payment_set.all()

            orders_list.append({
                # 订单创建时间
                'create_time': datetime.strptime(order.order_id[:14], '%Y%m%d%H%M%S'),
                # 订单号
                'order_id': order.order_id,
                # 订单状态
                'status': order.status,
                # 支付方式
                'pay_method': pay_method,
                # 商品总价格
                'total_amount': order.total_amount,
                # 运费
                'freight': order.freight,
                # 商品列表
                'skus': order.skus.all()
            })
        context = {
            'orders_list': orders_list,
            'page_num': page_num,
            'total_page': total_page
        }
        return render(request, 'user_center_order.html', context)


class GoodsJudgeView(LoginRequiredMixin, View):
    # 订单评价
    def get(self, request, order_id):
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.HttpResponseBadRequest('订单不存在')
        # 获取订单的所有商品
        skus = order.skus.all()
        sku_list = []
        for sku in skus:
            sku_list.append({
                'name': sku.sku.name,
                'price': str(sku.price),
                'default_image_url': sku.sku.default_image.url,
                'order_id': sku.order_id,
                'sku_id': sku.sku_id
            })

        context = {
            'skus': sku_list
        }
        return render(request, 'goods_judge.html', context)


class JudgeCommitView(LoginRequiredMixin, View):
    """保存评价"""
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        comment = json_dict.get('comment')
        score = json_dict.get('score')
        is_anonymous = json_dict.get('is_anonymous')
        # 参数校验
        try:
            order_good = OrderGoods.objects.get(sku_id=sku_id, order_id=order_id)
        except Exception as e:
            return http.HttpResponse('订单商品不存在')
        order_good.comment = comment
        order_good.score = score
        order_good.is_anonymous = is_anonymous
        order_good.save()
        # 增加商品sku的评论量
        order_good.sku.comments += 1
        order_good.sku.save()
        # 修改spu的评论量
        order_good.sku.spu.comments += 1
        order_good.sku.spu.save()
        # 修改订单的状态
        # 判断订单中的商品是否全部评论
        goods = OrderGoods.objects.filter(order_id=order_id)
        for good in goods:
            if good.comment == '':
               break
        else:
            order = OrderInfo.objects.get(order_id=order_id)
            order.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
            order.save()
        return http.JsonResponse({'code': 0})


