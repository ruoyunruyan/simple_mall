from rest_framework import serializers

from apps.goods.models import SPUSpecification


class SPUSpecModelSerializer(serializers.ModelSerializer):
    """定义商品spu序列化器"""

    class Meta:
        model = SPUSpecification
        fields = '__all__'

    spu = serializers.StringRelatedField(read_only=True)
    spu_id = serializers.IntegerField()
