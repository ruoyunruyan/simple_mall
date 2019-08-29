from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PagePagination(PageNumberPagination):
    # 每页显示数量
    page_size = 5
    # 每页显示的最大数量
    max_page_size = 10
    # 查询参数中的每一页数量
    page_size_query_param = 'pagesize'

    # 重写分页器的相应对象
    def get_paginated_response(self, data):
        # 根据　self　的page属性获取对应的结果
        return Response({
            'count': self.page.paginator.count,  # 用户总数
            'lists': data,  # 返回数据
            'page': self.page.number,  # 当前页面
            'pages': self.page.paginator.num_pages,  # 总页数
            'pagesize': self.page_size,  # 每页显示数量
        })
