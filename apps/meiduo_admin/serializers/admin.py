from rest_framework import serializers

from apps.ausers.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        """重写create方法 密码加密  修改is_staff 为True"""
        validated_data['is_staff'] = True
        admin = super().create(validated_data)
        password = validated_data['password']
        admin.set_password(password)
        admin.save()
        return admin

    def update(self, instance, validated_data):
        validated_data['is_staff'] = True
        admin = super().update(instance, validated_data)
        password = validated_data['password']
        admin.set_password(password)
        admin.save()
        return admin
