from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'
