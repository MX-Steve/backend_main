import os
from celery import Celery, platforms
from django.conf import settings

platforms.C_FORCE_ROOT = True

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')
red = "redis://:%s@127.0.0.1:%s/0" % (settings.REDIS_PASS, settings.REDIS_PORT)
# 实例化
app = Celery('djentry', broker=red, backend=red, include=['assets.tasks'])

# namespace='CELERY'作用是允许你在Django配置文件中对Celery进行配置
# 但所有Celery配置项必须以CELERY开头，防止冲突
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从Django的已注册app中发现任务
app.autodiscover_tasks()


# 测试任务1
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
