from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from apps.goods.models import SpecificationOption, SPUSpecification
from apps.meiduo_admin.serializers.spec_options import SpecificationSerializer, SPUSpecsSerializer
from apps.meiduo_admin.utils.paginator import PagePagination


class SPUSpecsSimpleView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecsSerializer


class SpecificationModelViewSet(ModelViewSet):
    queryset = SpecificationOption.objects.order_by('-id')
    serializer_class = SpecificationSerializer
    pagination_class = PagePagination
