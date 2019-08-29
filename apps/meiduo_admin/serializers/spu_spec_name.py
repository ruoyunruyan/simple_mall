from rest_framework import serializers
from apps.goods.models import SPU


class SPUNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id', 'name']
