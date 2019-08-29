from django import http
from django.shortcuts import render
from django.views import View
from alipay import AliPay
from apps.orders.models import OrderInfo
from django.conf import settings
import os
from apps.payment.models import Payment
from utils.response_code import RETCODE


class PaymentView(View):
    def get(self, request, order_id):
        user = request.user

        # 校验商品是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.HttpResponseBadRequest('商品不存在')
        # 创建Alipay实例对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key/meiduo_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key/alipay_public_key.pem'),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 用实例化对象生成　URL　路径中的查询参数
        order_query_str = alipay.api_alipay_trade_page_pay(
            subject='美多商城%s' % order_id,
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            return_url=settings.ALIPAY_RETURN_URL,
        )

        alipay_url = settings.ALIPAY_URL + "?" + order_query_str
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentStatusView(View):

    def get(self, request):
        # 获取查询集 query_set
        query_set = request.GET
        # 将查询集转换成字典
        query_dict = query_set.dict()
        # 取出其中的 signature
        signature = query_dict.pop('sign')
        # 实例化Alipay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key/meiduo_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'key/alipay_public_key.pem'),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 再次　校验这个重定向是否是alipay重定向过来的
        success = alipay.verify(query_dict, signature)
        # 如果成功，则将订单信息存入数据库

        if success:
            order_id = query_dict.get('out_trade_no')
            trade_id = query_dict.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            # 修改订单状态为待评价
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])

            context = {
                'trade_id': trade_id
            }
            return render(request, 'pay_success.html', context)

        else:
            # 订单支付失败，重定向到我的订单
            return http.HttpResponseForbidden('非法请求')
