from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.negotiation import DefaultContentNegotiation
from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIHandler

from apps.ausers.models import User
from apps.meiduo_admin.serializers.users import UserModelSerializer, UserAddModelSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class UserView(ListCreateAPIView):
    """获取所有用户"""

    serializer_class = UserModelSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        """根据查询参数中是否有查询关键字, 返回不同的查询集"""
        queryset = User.objects.filter(is_staff=False).order_by('-id')
        # 获取搜索的关键字
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(username__contains=keyword)
        return queryset

    def get_serializer_class(self):
        """
        get 查询所有用户　　post 添加用户
        根据请求方式, 获取不同的序列化器
        """
        if self.request.method == 'GET':
            # 查询用户的序列化器
            return UserModelSerializer
        elif self.request.method == 'POST':
            # 添加用户的序列化器
            return UserAddModelSerializer
