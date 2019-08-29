from django import http
from django.shortcuts import render
from django.views import View
from utils.response_code import RETCODE
from .models import Areas
from meiduo_mall.settings.dev import logger
from django.core.cache import cache


class AreasView(View):

    def get(self, request):
        area_id = request.GET.get('area_id')
        if area_id is None:
            # 查询django 的缓存，如果有则直接使用，如果没有，则去数据库中取
            province_list = cache.get('province_list')
            if not province_list:
                try:
                    province_model_list = Areas.objects.filter(parent_id__isnull=True)
                    province_list = [{'id': province.id, 'name': province.name} for province in province_model_list]
                    # 从数据库中查完数据后，存入缓存中
                    cache.set('province_list', province_list, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 查询django 的缓存，如果有则直接使用，如果没有，则去数据库中取
            sub_data = cache.get('sub_data_'+area_id)
            if not sub_data:
                subs = Areas.objects.filter(parent_id=area_id)
                parent_model = Areas.objects.get(id=area_id)
                sub_list = [{"id": sub.id, "name": sub.name} for sub in subs]
                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': sub_list
                }
                # 从数据库中查完数据后，存入缓存中
                cache.set('sub_data_'+area_id, sub_data, 3600)

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})


