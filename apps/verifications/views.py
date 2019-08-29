from django.shortcuts import render
from django.views import View
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http
from libs.yuntongxun.sms import CCP
from meiduo_mall.settings.dev import logger
from random import randint
from celery_tasks.sms.tasks import ccp_send_sms_code
from utils.response_code import RETCODE


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1. 生成验证码  验证码文本 及 验证码图片二进制流
        text, image = captcha.generate_captcha()
        # 2. 连接数据库
        image_redis_clien = get_redis_connection('verify_image_code')
        # 3. 将验证码文本保存到 redis 数据库
        image_redis_clien.setex(uuid, 300, text)
        return http.HttpResponse(image, content_type='image/jpeg')


class SMSCodeView(View):
    def get(self, request, mobile):
        # '/sms_codes/' + this.mobile + '/  ?image_code=' + this.image_code + '&image_code_id=' + this.image_code_id;
        # 接受路径查询参数  用户输入的验证码  及  UUID
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 连接 验证码的redis 数据库
        image_redis_client = get_redis_connection('verify_image_code')
        redis_image_code = image_redis_client.get(uuid)
        # 判断 取出验证码是否为空， 如果为空则说明验证码过期
        if redis_image_code is None:
            return http.JsonResponse({'code': "4001", 'errmsg': '图形验证码失效了'})
        # 判断 取出验证码与输入验证码是否一直,  注意大小写的转换, 注意 从redis 数据库中取出的数据为 bytes 类型
        if image_code.lower() != redis_image_code.decode().lower():
            return http.JsonResponse({'code': "4001", 'errmsg': '输入图形验证码有误'})

        # 删除 redis 数据库中的验证码
        try:
            image_redis_client.delete(uuid)
        except Exception as e:
            logger.error(e)
        # 开始生成随机的六位数的验证码
        sms_code = randint(100000, 999999)
        # 连接保存短信验证码的redis数据库
        sms_redis_client = get_redis_connection('sms_code')

        # 判断是否已经发送过短信
        send_flag = sms_redis_client.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # 保存生成的短信验证码, 用手机号作为键
        # sms_redis_client.setex(mobile, 300, sms_code)
        # 在redis中保存已经发送过短信的记录
        # sms_redis_client.setex('send_flag_%s' % mobile, 60, 1)

        # redis 的管道操作　，　将多个要进行的操作装进管道中，一起进行操作
        p1 = sms_redis_client.pipeline()
        p1.setex(mobile, 300, sms_code)
        p1.setex('send_flag_%s' % mobile, 60, 1)
        p1.execute()

        # 1. 发送短信
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 2. 调用celery　异步发送短信
        ccp_send_sms_code.delay(mobile, sms_code)

        print('当前的验证码是：', sms_code)
        return http.JsonResponse({'code': '0', 'errmsg': '发送短信成功'})


