from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from apps.goods.models import SPU, Brand, GoodsCategory
from apps.meiduo_admin.serializers.spu import SPUSerializer, BrandSerializer, CategorySerializer, SPUCreateSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class SPUView(ModelViewSet):
    queryset = SPU.objects.all()
    pagination_class = PagePagination

    def get_serializer_class(self):
        if self.action == 'list':
            return SPUSerializer
        else:
            return SPUCreateSerializer


class BrandView(ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class CategoryView(ReadOnlyModelViewSet):
    queryset = GoodsCategory.objects.all()
    serializer_class = CategorySerializer

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        categories = self.queryset.filter(parent_id=pk)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

