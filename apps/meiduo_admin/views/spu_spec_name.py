from rest_framework.generics import ListAPIView

from apps.goods.models import SPU
from apps.meiduo_admin.serializers.spu_spec_name import SPUNameSerializer


class SPUNameView(ListAPIView):
    queryset = SPU.objects.all()
    serializer_class = SPUNameSerializer
