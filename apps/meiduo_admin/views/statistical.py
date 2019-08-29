from datetime import date, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from apps.ausers.models import User
from apps.orders.models import OrderInfo
from apps.goods.models import GoodsVisitCount
from apps.meiduo_admin.serializers import statistical


class UserCountView(APIView):
    """统计用户总数"""

    # 权限认证
    permission_classes = [IsAdminUser]

    def get(self, request):
        count = User.objects.filter(is_staff=False).count()
        now_date = date.today()
        return Response({'count': count, 'date': now_date})


class UserIncrementDailyView(APIView):
    """统计日增用户"""
    def get(self, request):
        now_date = date.today()
        count = User.objects.filter(date_joined__gte=now_date).count()
        return Response({'count': count, 'date': now_date})


class UserActiveDailyView(APIView):
    """统计日活用户"""
    def get(self, request):
        now_date = date.today()
        count = User.objects.filter(last_login__gte=now_date, is_staff=False).count()
        return Response({'count': count, 'date': now_date})


class UserOrderDailyView(APIView):
    """统计日下单用户量"""
    def get(self, request):
        now_date = date.today()
        # count = User.objects.filter(orders__create_time__gte=now_date).distinct().count()
        count = OrderInfo.objects.filter(create_time__gte=now_date).values('user_id').distinct().count()

        return Response({'count': count, 'date': now_date})


class UserIncrementMonthView(APIView):
    """月增用户统计"""
    def get(self, request):
        now_date = date.today()
        date_list = []
        for i in range(1, 31):
            current_date = now_date - timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            count = User.objects.filter(date_joined__gte=current_date, date_joined__lt=next_date).count()
            date_list.insert(0, {'count': count, 'date': current_date})

        return Response(date_list)


class GoodsCategoryVisitView(APIView):
    """日分类商品访问量"""
    def get(self, request):
        now_date = date.today()
        categories = GoodsVisitCount.objects.filter(date=now_date)
        serializer = statistical.GoodsVisitModelSerializer(categories, many=True)
        return Response(serializer.data)
