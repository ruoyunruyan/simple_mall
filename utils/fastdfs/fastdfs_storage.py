from django.core.files.storage import Storage
from django.conf import settings


class FastDFSStorage(Storage):

    def __init__(self, fdfs_base_url=None):
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        pass

    def url(self, name):
        return self.fdfs_base_url + name