from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings

# SECRET_KEY


class SecretOauth(object):
    def __init__(self, expiry=7 * 24 * 3600):
        self.serializer = Serializer(settings.SECRET_KEY, expires_in=expiry)

    def dumps(self, content_dict):
        result = self.serializer.dumps(content_dict)
        # result 是 bytes 类型
        return result.decode('utf-8')

    def loads(self, content_dic):
        result = self.serializer.loads(content_dic)
        return result
