from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from apps.oauth.models import OAuthQQUser, OAuthSinaUser
from apps.oauth.utils import SecretOauth
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE
import re
from django_redis import get_redis_connection
from apps.ausers.models import User
from weibo import APIClient


class SinaAuthUserView(View):
    def get(self, request):
        # 得到回传的　code
        code = request.GET.get('code')
        oauth_sina = APIClient(app_key=settings.SINA_APP_KEY,
                               app_secret=settings.SINA_APP_SECRET,
                               redirect_uri=settings.SINA_REDIRECT_URI
                               )
        try:
            # 根据 code 得到 tocken　=> {'access_token': '2.00IsO_OGJcPibD120f9a82d9R4xf1C', 'uid': '5708251100', 'expires_in': 1563044399, 'expires': 1563044399}
            tocken = oauth_sina.request_access_token(code=code)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('Oauth2.0认证失败!')
        # 获取 uid
        uid = tocken.get('uid')
        # 判断 uid 是否绑定用户
        try:
            sina_user = OAuthSinaUser.objects.get(uid=uid)
        except Exception as e:
            # 查询失败说明未绑定，跳转到绑定页面
            # 将　uid 加密
            secret_uid = SecretOauth().dumps({'uid': uid})
            context = {'uid': secret_uid}
            return render(request, 'sina_callback.html', context)
        else:
            # 用户已绑定，则记录用户登陆状态
            user = sina_user.user
            login(request, user)
            # 跳转到首页
            response = redirect(reverse('contents:index'))
            # 设置 cookie
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
            return response

    def post(self, request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code = request.POST.get('sms_code')
        # 获取加密的　uid
        secret_uid = request.POST.get('uid')
        uid = SecretOauth().loads(secret_uid).get('uid')
        # 参数校验
        if not all([mobile, password, sms_code, secret_uid]):
            return http.HttpResponseForbidden('信息输入不完整')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        sms_redis_client = get_redis_connection('sms_code')
        redis_sms_code = sms_redis_client.get(mobile)
        if sms_code is None:
            return http.HttpResponseForbidden('验证码已过有效期')
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden('手机验证码输入错误')
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            logger.error(e)
            # 用户不存在，则创建用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 用户存在，则检查用户输入密码是否正确
            if not user.check_password(password):
                return render(request, 'sina_callback.html', {'account_errmsg': '用户名或密码错误'})

        try:
            OAuthSinaUser.objects.create(uid=uid, user=user)
        except Exception as e:
            logger.error(e)
            return render(request, 'sina_callback.html', {'sina_login_errmsg': 'sina登录失败'})
        # 保持登陆状态
        login(request, user)
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=7 * 24 * 3600)
        return response


class SinaAuthURLView(View):
    """获取sina登陆url"""

    def get(self, request):
        # 实例化微博对象
        oauth_sina = APIClient(app_key=settings.SINA_APP_KEY,
                               app_secret=settings.SINA_APP_SECRET,
                               redirect_uri=settings.SINA_REDIRECT_URI
                               )
        login_url = oauth_sina.get_authorize_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQAuthURLView(View):
    def get(self, request):
        next_url = request.GET.get('next')
        oauth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state=next_url)
        login_url = oauth_qq.get_qq_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


def is_bind_openid(request, open_id, next_url):
    try:
        oauth_user = OAuthQQUser.objects.get(openid=open_id)
    except Exception as e:
        # 查询失败说明未绑定，重定向到绑定页
        logger.error(e)
        # openid 加密
        secret_openid = SecretOauth().dumps({'openid': open_id})
        context = {'openid': secret_openid}
        return render(request, 'oauth_callback.html', context)
    else:
        # 查询成功，套转到首页
        user = oauth_user.user
        login(request, user)
        if next_url:
            response = redirect(next_url)
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response


class QQAuthUserView(View):
    def get(self, request):
        next_url = request.GET.get('state')
        code = request.GET.get('code')
        oauth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            token = oauth_qq.get_access_token(code)
            open_id = oauth_qq.get_open_id(token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('Oauth2.0认证失败!')
        response = is_bind_openid(request, open_id, next_url)
        return response

    def post(self, request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code = request.POST.get('sms_code')

        secret_openid = request.POST.get('openid')
        # 解密
        openid = SecretOauth().loads(secret_openid).get('openid')

        if not all([mobile, password, sms_code, openid]):
            return http.HttpResponseForbidden('信息输入不完整')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        sms_redis_client = get_redis_connection('sms_code')
        redis_sms_code = sms_redis_client.get(mobile)
        if sms_code is None:
            return http.HttpResponseForbidden('验证码已过有效期')
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden('手机验证码输入错误')

        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            logger.error(e)
            # 用户不存在，则创建用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 用户存在，则检查用户输入密码是否正确
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 绑定用户
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            logger.error(e)
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})
        # 保持登陆状态
        login(request, user)
        next_url = request.GET.get('state')
        if next_url:
            response = redirect(next_url)
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=7 * 24 * 3600)
        return response


class VerifyEmailView(View):
    def get(self, request):

        secret_token = request.GET.get('token')
        token = SecretOauth().loads(secret_token)
        if not token:
            return http.HttpResponseBadRequest('缺少token')
        try:
            user = User.objects.get(id=token['user_id'], email=token['email'])
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('无效的token')
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')
        return redirect(reverse('users:info'))
