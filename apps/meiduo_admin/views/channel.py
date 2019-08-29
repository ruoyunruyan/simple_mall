from django.db import transaction

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework import serializers
from rest_framework.response import Response

from apps.goods.models import GoodsChannel, GoodsCategory, GoodsChannelGroup
from apps.meiduo_admin.serializers.channel import ChannelSerializer, CatogrySerializer, ChannelGroupSerializer
from apps.meiduo_admin.utils.paginator import PagePagination
from apps.meiduo_admin.utils.sequence import channel_sequence_handler


class ChannelModelView(ModelViewSet):
    queryset = GoodsChannel.objects.order_by('group_id')
    serializer_class = ChannelSerializer
    pagination_class = PagePagination

    def create(self, request, *args, **kwargs):
        # 接收数据
        group_id = request.data.get('group_id')
        category_id = request.data.get('category_id')
        url = request.data.get('url')
        sequence = request.data.get('sequence')
        # 数据校验
        if not all([group_id, category_id, sequence, url]):
            raise serializers.ValidationError({'name': ['数据不完整']})

        try:
            sequence = int(sequence)
        except:
            raise serializers.ValidationError({'name': ['请输入数字序号']})

        try:
            group = GoodsChannelGroup.objects.get(id=group_id)
        except:
            raise serializers.ValidationError({'name': ['添加组失败']})

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except:
            raise serializers.ValidationError({'name': ['添加一级分类失败']})
        channel_list = group.channels.all()

        # 判断是否重复添加
        if category.category.all()[0] in channel_list:
            raise serializers.ValidationError({'name': ['重复添加']})

        # 总共有多少一级分类
        categories_count = group.channels.count()

        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                # 确定添加的位置
                # 判断添加的展示顺序是否大于 categories_count
                if sequence > categories_count:
                    sequence = categories_count + 1
                else:
                    categories = group.channels.filter(sequence__gte=sequence).order_by('sequence')
                    # 将其他的以及分类顺序加一
                    for categ in categories:
                        categ.sequence += 1
                        categ.save()

                channel = GoodsChannel.objects.create(group=group, category=category, url=url, sequence=sequence)
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError({'name': ['添加失败']})
            else:
                transaction.savepoint_commit(save_point)
                serializer = self.get_serializer(channel)
                return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        # 获取要修改的对象
        instance = self.get_object()
        # 接收修改的数据
        group_id = request.data.get('group_id')
        category_id = request.data.get('category_id')
        url = request.data.get('url')
        sequence = request.data.get('sequence')
        # 数据校验
        if not all([group_id, category_id, sequence, url]):
            raise serializers.ValidationError({'name': ['数据不完整']})

        try:
            sequence = int(sequence)
        except:
            raise serializers.ValidationError({'name': ['请输入数字序号']})

        try:
            group = GoodsChannelGroup.objects.get(id=group_id)
        except:
            raise serializers.ValidationError({'name': ['修改组失败']})

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except:
            raise serializers.ValidationError({'name': ['修改一级分类失败']})

        # 获取修改前频道总数
        channels_count_instance = instance.group.channels.count()

        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                # 所在频道的总频道数
                # 判断是否修改频道组
                if instance.group_id == group_id:
                    sequence = sequence if sequence <= channels_count_instance else channels_count_instance
                    # 一样则不影响其他频道组
                    # 判断sequence是否修改
                    if instance.sequence != sequence:
                        # 修改sequence
                        channel_sequence_handler(group, sequence, instance.sequence)
                else:
                    # 判断修改的一级分类是否存在
                    category_channel = category.category.all()
                    if category_channel:
                        if category_channel[0] in group.channels.all():
                            raise serializers.ValidationError('分类已存在')

                    old_group = instance.group
                    old_sequence = instance.sequence
                    channels_count_new = group.channels.count()
                    sequence = sequence if sequence <= channels_count_new else channels_count_new + 1

                    # 不一样则也要修改其他频道组
                    # 修改原来的频道组
                    channel_sequence_handler(old_group, sequence=old_sequence, channel_count=channels_count_instance, add=False)

                    # 修改新的频道组
                    channel_sequence_handler(group, sequence=sequence, channel_count=channels_count_new)

                instance.group_id = group_id
                instance.url = url
                instance.category_id = category_id
                instance.sequence = sequence
                instance.save()
                serializer = self.get_serializer(instance)
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError({'name': ['修改失败']})
            else:
                transaction.savepoint_commit(save_point)
                return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        # 获取删除对象
        instance = self.get_object()
        # 获取所有的频道, 及要删除的频道
        channels_count = instance.group.channels.count()
        sequence = instance.sequence

        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                if sequence < channels_count:
                    # 获取全部序号大于删除频道的序号
                    channels = instance.group.channels.filter(sequence__gt=sequence)
                    for channel in channels:
                        channel.sequence -= 1
                        channel.save()
                instance.delete()
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError({'name': ['删除失败']})
            else:
                transaction.savepoint_commit(save_point)
                return Response(status=204)


class CategoryView(ListAPIView):
    queryset = GoodsCategory.objects.filter(parent__isnull=True)
    serializer_class = CatogrySerializer


class ChannelGroupView(ListAPIView):
    queryset = GoodsChannelGroup.objects.all()
    serializer_class = ChannelGroupSerializer

