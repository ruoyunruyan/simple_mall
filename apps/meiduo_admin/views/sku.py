from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from apps.meiduo_admin.serializers.sku import SKUSerializer, CategorySerializer, SPUSpecsSerializer
from apps.meiduo_admin.utils.paginator import PagePagination
from apps.goods.models import SKU, GoodsCategory, SPUSpecification


class SKUModelViewSet(ModelViewSet):
    serializer_class = SKUSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        queryset = SKU.objects.all()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(name__contains=keyword)
        return queryset.order_by('-id')


class CategoryView(ListAPIView):
    """商品的三级分类"""
    # 第三季商品没有子级
    queryset = GoodsCategory.objects.filter(subs__isnull=True)
    serializer_class = CategorySerializer


class SpuSpecsView(ListAPIView):
    serializer_class = SPUSpecsSerializer

    def get_queryset(self):
        spu_id = self.kwargs.get('pk')

        queryset = SPUSpecification.objects.filter(spu_id=spu_id)

        return queryset
