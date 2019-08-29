from django.db import transaction

from rest_framework import serializers

from apps.goods.models import SKU, GoodsCategory, SPUSpecification, SpecificationOption, SKUSpecification
from celery_tasks.details.tasks import generate_detail_html


class SpecsSerializer(serializers.ModelSerializer):
    """规格的序列化器"""

    class Meta:
        model = SpecificationOption
        fields = ['id', 'value']


class SPUSpecsSerializer(serializers.ModelSerializer):

    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    options = SpecsSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """获取商品类别序列化器"""
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name']


class SKUSpecsSerializer(serializers.Serializer):
    """sku规格序列化器"""
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()


class SKUSerializer(serializers.ModelSerializer):
    """获取SKU序列化器"""

    # 指定外键属性
    category = serializers.StringRelatedField(read_only=True)
    spu = serializers.StringRelatedField(read_only=True)
    # 指定隐藏属性
    spu_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    # sku规格外键
    specs = SKUSpecsSerializer(many=True)

    class Meta:
        model = SKU
        fields = '__all__'
        # exclude = ['create_time', 'update_time', 'comments', 'default_image']

    def create(self, validated_data):
        # 添加 sku　表数据, 添加　skuspecification表数据, 调用异步任务生成详情页
        # 取出 sku 的规格信息 []
        specs = validated_data.pop('specs')
        # 多表操作, 开启事务
        with transaction.atomic():
            try:
                # 设置保存点
                save_point = transaction.savepoint()
                # 创建 SKU
                sku = SKU.objects.create(**validated_data)
                # 遍历 specs 创建规格
                for spec in specs:
                    SKUSpecification.objects.create(sku=sku, **spec)
            except:
                # 出现异常, 回滚到保存点
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError('库存商品保存失败')
            else:
                transaction.savepoint_commit(save_point)
                # 调用异步任务生成 sku 的详情页
                generate_detail_html.delay(sku.id)
                return sku

    def update(self, instance, validated_data):
        # 取出sku规格信息
        specs = validated_data.pop('specs')
        with transaction.atomic():
            try:
                save_point = transaction.savepoint()

                # SKU.objects.filter(id=instance.id).update(**validated_data)
                # 调用父类的update方法
                instance = super().update(instance, validated_data)

                # 删除规格表中原有的数据
                SKUSpecification.objects.filter(sku_id=instance.id).delete()
                # 添加新的数据
                for spec in specs:
                    SKUSpecification.objects.create(sku=instance, **spec)
            except:
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError('修改失败')
            else:
                transaction.savepoint_commit(save_point)
                # 生成　sku　详情页
                generate_detail_html.delay(instance.id)
                return instance
