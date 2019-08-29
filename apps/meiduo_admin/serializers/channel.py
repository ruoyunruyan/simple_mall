from rest_framework import serializers

from apps.goods.models import GoodsChannel


class ChannelSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)
    category_id = serializers.IntegerField()
    group = serializers.StringRelatedField(read_only=True)
    group_id = serializers.IntegerField()

    class Meta:
        model = GoodsChannel
        # fields = '__all__'
        exclude = ['create_time', 'update_time']


class CatogrySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class ChannelGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)