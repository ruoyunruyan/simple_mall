from celery import Celery
import os

# 配置　django 的运行环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 实例化　celery 对象
celery_app = Celery('celery_tasks.sms.tasks')

# 给 实例化的celery对象 添加配置信息
celery_app.config_from_object('celery_tasks.config')

# 设置　实例化的 celery　对象　自动添加任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.detail'])
