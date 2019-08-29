from rest_framework.viewsets import ModelViewSet

from apps.meiduo_admin.serializers.spu_spec import SPUSpecModelSerializer
from apps.meiduo_admin.utils.paginator import PagePagination
from apps.goods.models import SPUSpecification


class SPUModelViewSetView(ModelViewSet):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecModelSerializer
    pagination_class = PagePagination
