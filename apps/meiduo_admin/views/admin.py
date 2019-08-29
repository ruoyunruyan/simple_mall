from django.contrib.auth.models import Group
from rest_framework.response import Response

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from apps.ausers.models import User
from apps.meiduo_admin.serializers.admin import UserSerializer
from apps.meiduo_admin.serializers.group import GroupSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class UserModelView(ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserSerializer
    pagination_class = PagePagination

    @action(methods=['list'], detail=False)
    def simple(self, request):
        permissions = Group.objects.all()
        serializer = GroupSerializer(permissions, many=True)
        return Response(serializer.data)
