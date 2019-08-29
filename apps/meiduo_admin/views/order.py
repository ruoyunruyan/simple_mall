from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from apps.meiduo_admin.serializers.order import OrderSimpleSerializer, OrderSerializer
from apps.meiduo_admin.utils.paginator import PagePagination
from apps.orders.models import OrderInfo


class OrderModelView(ModelViewSet):
    pagination_class = PagePagination

    def get_queryset(self):
        queryset = OrderInfo.objects.all()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(order_id__contains=keyword)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderSimpleSerializer
        return OrderSerializer

    @action(methods=['put'], detail=True)
    def status(self, request, pk):
        instance = self.get_object()
        status = self.request.data.get('status')
        instance.status = status
        instance.save()
        serializer = self.get_serializer(instance)
        return Response({
            'order_id': instance.order_id,
            'status': status
        }, status=201)