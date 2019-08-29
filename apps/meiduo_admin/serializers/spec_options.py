from rest_framework import serializers

from apps.goods.models import SpecificationOption, SPUSpecification


class SPUSpecsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = '__all__'
    spec = serializers.StringRelatedField(read_only=True)
    spec_id = serializers.IntegerField()
