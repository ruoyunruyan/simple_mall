from fdfs_client.client import Fdfs_client


client = Fdfs_client('client.conf')

# 上传文件
# ret = client.upload_by_filename('/home/python/Desktop/iphone.jpg')
"""
{
    'Group name': 'group1',
    'Storage IP': '192.168.136.130',
    'Local file name': '/home/python/Desktop/iphone.jpg',
    'Status': 'Upload successed.',
    'Uploaded size': '6.00KB',
    'Remote file_id': 'group1/M00/00/02/wKiIgl09S5SAM9cSAAAaSQ5Z0Cc893.jpg'
}
"""
# 修改文件
# ret = client.modify_by_file('/home/python/Desktop/huawei.jpg', 'group1/M00/00/02/wKiIgl09S5SAM9cSAAAaSQ5Z0Cc893.jpg')
"""
包错误
使用先删除在上传的方法
"""

# 删除
ret = client.delete_file('group1/M00/00/02/wKiIgl09S5SAM9cSAAAaSQ5Z0Cc893.jpg')
"""
(
    'Delete file successed.',
    'group1/M00/00/02/wKiIgl09S5SAM9cSAAAaSQ5Z0Cc893.jpg', '192.168.136.130'
)
"""
print(ret)
