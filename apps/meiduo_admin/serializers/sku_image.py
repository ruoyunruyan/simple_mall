from rest_framework import serializers

from apps.goods.models import SKUImage, SKU


class SKUSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class SKUImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKUImage
        fields = ('sku', 'image', 'id')

    sku = serializers.PrimaryKeyRelatedField(read_only=True)
