import pickle
import base64


class CookieSecret(object):
    """生成用于浏览器cookie信息加密的工具类"""
    @classmethod
    def dumps(cls, data):
        # 将信息转成 二进制流
        data_bytes = pickle.dumps(data)
        # 将生成的二进制流进行 base64加密,　生成加密的bytes
        b64_bytes = base64.b64encode(data_bytes)
        return b64_bytes.decode()

    @classmethod
    def loads(cls, data):
        # 将信息进行base64解密生成二进制流
        b64_bytes = base64.b64decode(data)
        # 将 bytes 转换成　python 的字典类型
        data = pickle.loads(b64_bytes)
        return data