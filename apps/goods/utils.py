from apps.goods.models import GoodsChannel


def get_breadcrumb(cat3):
    """面包屑组件"""
    cat2 = cat3.parent

    cat1 = cat2.parent

    breadcrumb = {
        'cat1': {
            'url': cat1.goodschannel_set.all()[0].url,
            # 'url': GoodsChannel.objects.get(category=cat1).url,
            'name': cat1.name
        },
        'cat2': cat2,
        'cat3': cat3
    }

    return breadcrumb

