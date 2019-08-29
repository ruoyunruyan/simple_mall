import json
from random import randint
from celery_tasks.sms.tasks import ccp_send_sms_code
from django.db.models import F, Q
from apps.goods.models import SKU
from celery_tasks.email.tasks import send_verify_email
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
from apps.ausers.models import User, Address
from meiduo_mall.settings.dev import logger
from django.contrib.auth import login
from utils.response_code import RETCODE
from django_redis import get_redis_connection
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import generate_verify_email_url
from apps.carts.utils import merge_cart_cookie_to_redis
from apps.oauth.utils import SecretOauth


class ModifyPwdView(View):
    """修改密码"""
    def post(self, request, user_id):
        json_dict = json.loads(request.body.decode())
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        secret_access_token = json_dict.get('access_token')
        # 解密access_token
        access_token = SecretOauth().loads(secret_access_token)
        mobile = access_token.get('mobile')
        # 判断手机号是否存在
        if not mobile:
            return http.HttpResponseBadRequest('验证超时')
        try:
            user = User.objects.get(id=user_id, mobile=mobile)
        except Exception as e:
            return http.HttpResponseNotFound('用户不存在')
        if password != password2:
            return http.HttpResponseBadRequest('两次密码不一致')
        # 设置新密码
        user.set_password(password)
        user.save()
        return http.JsonResponse({'status': '修改密码成功'})


class FindPwdCheckMsgView(View):

    def get(self, request, username):
        # 接收短信验证码
        sms_code = request.GET.get('sms_code')
        # 判断用户是否存在
        try:
            if re.match(r'^1[345789]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except Exception as e:
            return http.HttpResponseNotFound('用户名或手机号不存在')

        mobile = user.mobile
        sms_redis_client = get_redis_connection('sms_code')
        sms_code_redis = sms_redis_client.get(mobile)
        # 判断手机验证码是否过期
        if not sms_code_redis:
            return http.HttpResponseBadRequest('验证码已过期')

        if sms_code != sms_code_redis.decode():
            return http.HttpResponseNotFound('验证码有误')
        # 构造返回前端数据
        # 构造加密的验证数据, 设置过期时间
        access_token = SecretOauth(600).dumps({'mobile': mobile})
        context = {
            'user_id': user.id,
            'access_token': access_token,
        }
        return http.JsonResponse(context)


class FindPasswordSendSmsView(View):
    """发送短信验证码"""
    def get(self, request):
        # 接收前端参数
        secret_access_token = request.GET.get('access_token')
        # 解密前端参数,获取传递的手机号码
        access_token = SecretOauth().loads(secret_access_token)
        mobile = access_token.get('mobile')
        # 判断手机号是否存在
        if not mobile:
            return http.HttpResponseBadRequest('链接超时')
        # 有就发送手机短信
        # 开始生成随机的六位数的验证码
        sms_code = randint(100000, 999999)
        # 连接保存短信验证码的redis数据库
        sms_redis_client = get_redis_connection('sms_code')
        # 判断是否已经发送过短信
        send_flag = sms_redis_client.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # redis 的管道操作　，　将多个要进行的操作装进管道中，一起进行操作
        p1 = sms_redis_client.pipeline()
        p1.setex(mobile, 300, sms_code)
        p1.setex('send_flag_%s' % mobile, 60, 1)
        p1.execute()

        # 调用celery　异步发送短信
        ccp_send_sms_code.delay(mobile, sms_code)
        return http.JsonResponse({'code': '0', 'errmsg': '发送短信成功'})


class FindPasswordView(View):
    """更改密码第二步，验证图片验证码，发送手机验证码"""
    def get(self, request, username):
        # 获取前段图片验证码及图片uuid
        image_code = request.GET.get('text')
        uuid = request.GET.get('image_code_id')
        redis_client = get_redis_connection('verify_image_code')
        # 根据　uuid　获取图片验证码, redis 取出来的为 bytes 类型
        image_code_redis = redis_client.get(uuid)
        # 如果验证码不存在，则返回验证码过期
        if not image_code_redis:
            return http.HttpResponseBadRequest('验证码已过期')
        # 判断验证码是否正确
        if image_code.lower() != image_code_redis.decode().lower():
            return http.HttpResponseBadRequest('验证码错误')
        # 判断用户名是否存在
        try:
            if re.match(r'^1[345789]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except Exception as e:
            return http.HttpResponseNotFound('用户名或手机号错误')

        # 如果验证码正确，用户存在，则返回
        mobile = user.mobile
        secret_mobile = mobile[:3] + '****' + mobile[7:]

        # 加密手机号生成access_token, 同时设置过期时间
        mobile_dict = {'mobile': mobile}
        access_token = SecretOauth(600).dumps(mobile_dict)
        return http.JsonResponse({'mobile': secret_mobile, 'access_token': access_token})


class ShowFindPasswordView(View):
    """更改密码第一步，页面显示"""
    def get(self, request):
        return render(request, 'find_password.html')


class MobileCountView(View):
    def get(self, request, mobile):
        if not re.match(r'1[3-9]\d{9}', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')
        try:
            count = User.objects.filter(mobile=mobile).count()

        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('手机号不存在')
        return http.JsonResponse({"code": RETCODE.OK, 'count': count, 'errmsg': '查询成功'})


class UsernameCountView(View):
    def get(self, request, username):
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.info(e)
            return http.HttpResponseForbidden('用户名不存在')
        return http.JsonResponse({"code": RETCODE.OK, 'count': count, 'errmsg': '查询成功'})


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        req = request.POST
        username = req.get('username')
        password = req.get('password')
        password2 = req.get('password2')
        mobile = req.get('mobile')
        sms_code = req.get('msg_code')
        allow = req.get('allow')
        # 判断 是否为空
        if not all([username, password, password2, mobile]):
            return http.HttpResponseForbidden('输入信息不能为空')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选协议')
        # 从 redis 数据库中取出手机验证码
        sms_redis_client = get_redis_connection('sms_code')
        redis_sms_code = sms_redis_client.get(mobile)
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden('手机验证码输入错误')

        # 全部验证通过后， 生成用户， 存入数据库
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            # 将异常写入日志
            logger.info(e)
            return render(request, 'register.html', {"register_message": "注册失败"})

        # 保持登陆状态
        login(request, user)

        # return redirect(reverse('contents:index'))

        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username)
        return response


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        req = request.POST
        username = req.get('username')
        password = req.get('password')
        remembered = req.get('remembered')
        next = request.GET.get('next')
        if not all([username, password]):
            return http.HttpResponseForbidden('参数不齐全')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
            # 2.2 密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        login(request, user)

        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))

        # 合并购物车
        response = merge_cart_cookie_to_redis(request, response)

        response.set_cookie('username', username)
        return response


class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }

        return render(request, 'user_center_info.html', context)


class EmailView(View):
    def put(self, request):
        # 接受发送的邮箱 =>  解码　=> json字符串
        json_str = request.body.decode('utf-8')
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        try:
            # 设置用户的邮箱
            request.user.email = email
            # 保存
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class AddressView(View):
    """收货地址页，地址展示"""
    def get(self, request):
        user = request.user
        addresses = Address.objects.filter(user=user, is_deleted=False)
        address_dict_list = []
        for address in addresses:
            address_dict_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        context = {
            'default_address_id': user.default_address_id,
            'addresses': address_dict_list,
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredMixin, View):
    """新增收件地址"""
    def post(self, request):
        """接收数据为Json对象"""
        json_dict = json.loads(request.body.decode('utf-8'))
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 判断 用户是否有 默认地址, 如果没有 设置一个
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 返回前端数据
        address_dict = {
            "id": address.id,
            "title": address.receiver,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class UpdateDestroyAddressView(View):
    """修改地址信息"""
    def put(self, request, address_id):
        """修改地址"""
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class DefaultAddressView(View):
    """修改默认地址"""
    def put(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
            # 响应设置默认地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class TitleAddressView(View):
    """修改title"""
    def put(self, request, address_id):
        json_dict = json.loads(request.body.decode('utf-8'))
        title = json_dict.get('title')
        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class ChangePwdView(View):
    """设置密码"""
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')

        # check_password
        try:
            request.user.check_password(old_password)
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        request.user.set_password(new_password)
        request.user.save()
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        return response


class UserBrowseHistory(View):
    """用户的浏览记录"""
    def get(self, request):
        # 链接数据库
        history_redis_client = get_redis_connection('history')
        # 根据键获取浏览记录　商品 sku_id　列表
        sku_ids = history_redis_client.lrange('history_%d' % request.user.id, 0, -1)
        skus = []
        for sku_id in sku_ids:
            # 获取商品
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})

    def post(self, request):
        # 获取商品的 sku_id
        sku_id = json.loads(request.body.decode()).get('sku_id')
        # 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品不存在!')
        # 链接 redis　数据库
        history_redis_client = get_redis_connection('history')
        # 生成key
        history_key = 'history_%s' % request.user.id
        # 对　redis　进行多次操作，所以使用管道操作，减少数据库交互
        p1 = history_redis_client.pipeline()
        # 1. 根据 sku_id ,先去除数据库中以往此条商品的记录
        p1.lrem(history_key, 0, sku_id)
        # 2. 将　sku_id 添加到数据库
        p1.lpush(history_key, sku_id)
        # 3. 截取数据库中的前５条数据, 只保留前５条数据
        p1.ltrim(history_key, 0, 4)
        # 4. 执行操作
        p1.execute()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

