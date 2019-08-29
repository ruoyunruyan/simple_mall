from apps.goods.models import GoodsChannel
from collections import OrderedDict


def get_categories():

    # 方便排序，使用有序字典
    categories = OrderedDict()

    # 取出　37 中种商品分类
    # 首页展示需要排序，根据所属频道和 sequence
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')

    for channel in channels:

        # 查询商品的所属频道
        group_id = channel.group_id

        # 判断字典中是否已经存在频道
        if group_id not in categories:

            # 不存在则创建频道
            categories[channel.group_id] = {'channels': [], 'sub_cats': []}

        # 存在则根据外键 category 去除商品类别的对象
        cat1 = channel.category

        # 在对象中添加 url 属性
        cat1.url = channel.url

        # 将对象添加到频道列表
        categories[group_id]['channels'].append(cat1)

        # 自链接根据　related_name 取出对应的商品
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)

    return categories
