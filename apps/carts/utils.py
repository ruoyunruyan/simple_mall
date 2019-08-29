from utils.cookiesecret import CookieSecret
from django_redis import get_redis_connection
import json


# 合并购物车, 用 cookie 中的数据覆盖 redis中的数据
def merge_cart_cookie_to_redis(request, response):
    cookie_data = request.COOKIES.get('carts')
    # 如果 cookie 中没有值，则直接返回
    if not cookie_data:
        return response
    # 获取 cookie 中的数据
    cookie_dict = CookieSecret.loads(cookie_data)
    user = request.user
    redis_client = get_redis_connection('carts')
    redis_data = redis_client.hgetall(user.id)
    # 获取 redis 中的数据
    redis_dict = {int(data[0].decode()): json.loads(data[1].decode()) for data in redis_data.items()}
    # 更新　redis 中取出的数据
    redis_dict.update(cookie_dict)
    # 将更新后的数据写入 redis　数据库中
    for sku_id in redis_dict:
        redis_client.hset(request.user.id, sku_id, json.dumps(redis_dict[sku_id]))
    # 删除 cookie 中的值
    response.delete_cookie('carts')
    return response
