from rest_framework import serializers

from apps.goods.models import SPU


class SPUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        # fields = '__all__'
        exclude = ['desc_detail', 'desc_pack', 'desc_service']

    category1 = serializers.StringRelatedField(read_only=True)
    category2 = serializers.StringRelatedField(read_only=True)
    category3 = serializers.StringRelatedField(read_only=True)

    category1_id = serializers.IntegerField()
    category2_id = serializers.IntegerField()
    category3_id = serializers.IntegerField()
    brand = serializers.StringRelatedField(read_only=True)
    brand_id = serializers.IntegerField()


class SPUCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = '__all__'

    category1 = serializers.StringRelatedField(read_only=True)
    category2 = serializers.StringRelatedField(read_only=True)
    category3 = serializers.StringRelatedField(read_only=True)

    category1_id = serializers.IntegerField()
    category2_id = serializers.IntegerField()
    category3_id = serializers.IntegerField()
    brand = serializers.StringRelatedField(read_only=True)
    brand_id = serializers.IntegerField()


class BrandSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class CategorySerializer(serializers.Serializer):
    # 商品类别序列化器
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


