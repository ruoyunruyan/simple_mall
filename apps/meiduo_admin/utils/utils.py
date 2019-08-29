from rest_framework_jwt.utils import jwt_payload_handler


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义返回前端的响应数据
    """
    return {
        'token': token,
        'username': user.username,
        'user_id': user.id
    }


def my_payload_handler(user):
    """
    自定义payload内容
    """
    # 通过rest_framework_jwt中jwt_payload_handler得到生成的payload字典
    payload = jwt_payload_handler(user)
    # 判断是否有email有就删除
    if 'email' in payload:
        del payload['email']
    # 在payload中添加手机号
    payload['mobile'] = user.mobile
    return payload
