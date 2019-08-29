from django.contrib.auth.models import Group, Permission

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from apps.meiduo_admin.serializers.group import GroupSerializer, PermissionSimpleSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class GroupModelView(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = PagePagination


class PermissionSimpleView(ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSimpleSerializer
