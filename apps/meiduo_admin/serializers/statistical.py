from rest_framework import serializers

from apps.goods.models import GoodsVisitCount


class GoodsVisitModelSerializer(serializers.ModelSerializer):
    """商品日访问量序列化器"""
    class Meta:
        model = GoodsVisitCount
        fields = ['count', 'category']

    category = serializers.StringRelatedField()
