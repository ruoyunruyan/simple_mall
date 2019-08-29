from django.contrib.auth.backends import ModelBackend
from meiduo_mall.settings.dev import logger
from .models import User
import re
from apps.oauth.utils import SecretOauth
from django.conf import settings


def get_user_by_account(request, username):

    """
    :param request: 通过判断request是否为空,判断是否为管理员登陆
    :param username:
    :return: 返回用户对象
    """
    if request is None:
        try:
            user = User.objects.get(username=username, is_staff=True)
        except Exception as e:
            return None
    else:
        try:

            if re.match(r'^1[345789]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except Exception as e:
            logger.error(e)
            return None
    return user


class UsernameMobileAuthBackend(ModelBackend):
    """重写用户认证的类"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(request, username)
        if user and user.check_password(password):
            return user


def generate_verify_email_url(user):
    data_dict = {'user_id': user.id, "email": user.email}
    secret_data = SecretOauth().dumps(data_dict)
    active_url = settings.EMAIL_ACTIVE_URL + '?token=' + secret_data
    return active_url
