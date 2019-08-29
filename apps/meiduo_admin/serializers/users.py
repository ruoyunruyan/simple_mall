from rest_framework import serializers

from apps.ausers.models import User


class UserModelSerializer(serializers.ModelSerializer):
    """获取用户的序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email']


class UserAddModelSerializer(serializers.ModelSerializer):
    """创建用户的序列化器"""
    class Meta:
        model = User
        fields = ['username', 'password', 'mobile', 'email']
        read_only_field = 'id'
        # 设置password为只写
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate(self, attrs):
        """
        自定义验证方法
        """
        # 验证用户名
        username = attrs.get('username')
        if User.objects.filter(username=username).count():
            raise serializers.ValidationError('用户名已存在')
        # 验证手机号
        mobile = attrs.get('mobile')
        if User.objects.filter(mobile=mobile).count():
            raise serializers.ValidationError('手机号已注册')
        return attrs

    def create(self, validated_data):
        """
        因为要创建用户,　需要保存密码, 所以重写create方法
        :param validated_data:
        :return:
        """
        user = User.objects.create_user(**validated_data)
        return user


