from django.conf import settings
from django.db import transaction

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import serializers

from fdfs_client.client import Fdfs_client

from apps.meiduo_admin.serializers.sku_image import SKUImageSerializer, SKUSimpleSerializer
from apps.goods.models import SKUImage, SKU
from apps.meiduo_admin.utils.paginator import PagePagination
from celery_tasks.details.tasks import generate_detail_html


class SKUImageView(ModelViewSet):
    queryset = SKUImage.objects.order_by('-id')
    serializer_class = SKUImageSerializer
    pagination_class = PagePagination

    def create(self, request, *args, **kwargs):
        # 接收 sku_id
        sku_id = request.data.get('sku')
        # 接收图片数据
        image_file = request.data.get('image')
        # 数据校验
        if not all([sku_id, image_file]):
            raise serializers.ValidationError('数据不完整')
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            raise serializers.ValidationError('修改的商品不存在')
        # 数据处理
        # 实例化 Fdfs_client
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        # 通过二进制流上传图片
        ret = client.upload_appender_by_buffer(image_file.read())
        # 判断状态
        if ret.get('Status') != 'Upload successed.':
            return Response('图片上传失败')
        # 获取上传图片的 url
        image_url = ret.get('Remote file_id')
        # 保存到数据库
        # 判断商品以前是否有图片及是否有默认图片, 没有就将上传的图片作为默认图片
        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                if not sku.images.count() or sku.default_image == '':
                    # 没有就修改 sku 表中商品的默认图片
                    sku.default_image = image_url
                    sku.save()
                sku_image = SKUImage.objects.create(sku=sku, image=image_url)
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError()
            else:
                transaction.savepoint_commit(save_point)
                # 生成新的静态页面
                generate_detail_html.delay(sku_id)
                # 返回响应
                serializer = self.get_serializer(sku_image)
                return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        # 获取修改的对象
        instance = self.get_object()
        # 接收 sku_id
        sku_id = request.data.get('sku')
        # 接收图片数据
        image_file = request.data.get('image')
        # 校验参数
        if not sku_id:
            raise serializers.ValidationError('数据不完整')
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            raise serializers.ValidationError('修改的商品不存在')
        # 获取修改对象的image_url
        image_url_instance = instance.image.name
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        # 删除旧的image, 将其放在事务中执行
        # client.delete_file(image_url_instance)
        # 上传新的图片
        ret = client.upload_appender_by_buffer(image_file.read())
        if ret.get('Status') != 'Upload successed.':
            return Response('图片上传失败')
        # 获取新的url
        image_url = ret.get('Remote file_id')
        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                # 判断是否修改商品
                if instance.sku_id == int(sku_id):
                    # 只是修改了图片
                    # 判断修改的是否是商品的默认图片, 如果是就要修改sku表
                    if sku.default_image == image_url_instance:
                        sku.default_image = image_url
                        sku.save()
                else:
                    # 商品及图片都修改
                    # 获取被修改的sku
                    sku_old = SKU.objects.get(id=instance.sku_id)
                    # 判断修改的图片是不是被修改商品的默认图片
                    if sku_old.default_image == image_url_instance:
                        # 判断　sku_old　是否还有图片, 要先排除要被修改的图片
                        images = sku_old.images.exclude(image=image_url_instance)
                        if images:
                            # 有就将查询集中的第一张图片设置为默认图片
                            sku_old.default_image = images[0].image
                        else:
                            # 没有就设置为空
                            sku_old.default_image = None
                        sku_old.save()
                    # 判断要修改的商品有没有默认图片, 及有没有图片
                    if not sku.default_image or not sku.images.count():
                        # 如果没有, 就将其设置为默认图片
                        sku.default_image = image_url
                        sku.save()
                # 修改图片表
                instance.image = image_url
                instance.sku_id = sku_id
                instance.save()
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError('修改失败')
            else:
                client.delete_file(image_url_instance)
                transaction.savepoint_commit(save_point)
                serializer = self.get_serializer(instance)
                return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        sku = instance.sku
        image_url = instance.image.name
        try:
            # 删除文件
            client = Fdfs_client(settings.FDFS_CLIENT_CONF)
            client.delete_file(image_url)
        except:
            pass
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                instance.delete()
                # 如果删除的图片，是sku的默认图片
                if sku.default_image.name == image_url:
                    # 查询sku的所有图片
                    images = sku.images.all()
                    if images:
                        # 将第一个作为默认图片
                        sku.default_image = images[0].image
                    else:
                        sku.default_image = None
                    sku.save()
            except Exception as e:
                transaction.savepoint_rollback(sid)
                raise serializers.ValidationError('图片删除失败')
                # raise e
            else:
                transaction.savepoint_commit(sid)

                generate_detail_html.delay(sku.id)

                return Response(status=204)


class SKUSimpleView(ListAPIView):
    queryset = SKU.objects.all()
    serializer_class = SKUSimpleSerializer



