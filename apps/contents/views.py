from django.shortcuts import render
from django.views import View
from .utils import get_categories
from .models import ContentCategory


class IndexView(View):
    def get(self, request):

        # 广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for category in content_categories:
            contents[category.key] = category.content_set.filter(status=True).order_by('sequence')

        # 查询商品频道和分类
        categories = get_categories()
        context = {
            'categories': categories,
            'contents': contents
        }
        return render(request, 'index.html', context)
