from django.conf import settings

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import serializers

from fdfs_client.client import Fdfs_client

from apps.meiduo_admin.serializers.brand import BrandSerializer
from apps.meiduo_admin.utils.paginator import PagePagination
from apps.goods.models import Brand


class BrandModelView(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = PagePagination

    def create(self, request, *args, **kwargs):
        # 接收参数
        name = request.data.get('name')
        first_letter = request.data.get('first_letter')
        logo = request.data.get('logo')
        # 校验参数
        if not all([name, first_letter, logo]):
            return Response('数据不完整')
        if Brand.objects.filter(name=name).count():
            return Response('创建品牌已存在')
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        ret = client.upload_appender_by_buffer(logo.read())
        if ret.get('Status') != 'Upload successed.':
            return Response('logo上传失败')
        logo_url = ret.get('Remote file_id')
        brand = Brand.objects.create(name=name, first_letter=first_letter, logo=logo_url)
        serializer = self.get_serializer(brand)
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        name = request.data.get('name')
        first_letter = request.data.get('first_letter')
        logo = request.data.get('logo')
        logo_old = instance.logo.name
        if not all([name, first_letter, logo]):
            raise serializers.ValidationError('数据不全')
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        ret = client.upload_appender_by_buffer(logo.read())
        if ret.get('Status') != 'Upload successed.':
            return Response('图片上传失败')
        image_url = ret.get('Remote file_id')
        # 保存信息
        instance.name = name
        instance.first_letter = first_letter
        instance.logo = image_url
        instance.save()
        # 删除旧的商标
        client.delete_file(logo_old)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logo_old = instance.logo.name
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        try:
            client.delete_file(logo_old)
        except:
            pass
        response = super().destroy(request, *args, **kwargs)
        return response

