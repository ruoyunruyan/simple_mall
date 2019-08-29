from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from apps.meiduo_admin.serializers.permission import PermissionSerializer, ContentSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class PermissionView(ModelViewSet):
    queryset = Permission.objects.order_by('-id')
    serializer_class = PermissionSerializer
    pagination_class = PagePagination


class ContentView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentSerializer
