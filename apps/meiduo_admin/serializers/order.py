from rest_framework import serializers

from apps.orders.models import OrderInfo


class OrderSimpleSerializer(serializers.Serializer):
    order_id = serializers.CharField(read_only=True)
    create_time = serializers.DateTimeField(read_only=True)


class SKUSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    default_image = serializers.ImageField(read_only=True)


class OrderGoodsSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sku = SKUSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = '__all__'

    user = serializers.StringRelatedField(read_only=True)
    skus = OrderGoodsSerializer(read_only=True, many=True)
