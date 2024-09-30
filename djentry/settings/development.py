# pylint: disable=wildcard-import,unused-wildcard-import
import platform
from os import environ
from pathlib import Path
from djentry.settings.common import *
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

plat = platform.system().lower()
if plat == "linux":
    DB = "172.17.0.1"
else:
    DB = "mysql-db"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'HOST': DB,
        'PORT': 38085,
        'USER': "root",
        'PASSWORD': "Xwzsl180a.*T",
    }
}
HELLO_APP_ID = "cli_a1543517eaf9100b"
HELLO_APP_SECRET = "hjaC6YU7LF25DQNY3aNkkcjfu6PKD7xr"
JENKINS_HOST = "http://121.43.41.139:8080/"
JENKINS_USER = "admin"
JENKINS_PASSWD = "root123"
REDIS_PORT = 38084
REDIS_PASS = "Xwzsl180aT"
CMDB_BACK_PORT = 8000
ITSMURL = "http://localhost:9093/approval/v2/process"
# 最重要的配置，设置消息broker,格式为：db://user:password@host:port/dbname
# CELERY_BROKER_URL = "redis://:%s@192.168.177.133:%s/0" % (REDIS_PASS, REDIS_PORT)
ASGI_APPLICATION = 'djentry.asgi.application'
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": ["redis://:%s@192.168.177.133:%s/1" % (REDIS_PASS, REDIS_PORT)],
#             "symmetric_encryption_keys": [SECRET_KEY],
#         },
#     },
# }

# alicloud
ALICLOUD_ACESS_KEY = environ.get("ALICLOUD_ACCESS_KEY")
ALICLOUD_SECRET_KEY = environ.get("ALICLOUD_SECRET_KEY")
# CELERY_BEAT_SCHEDULE = {
#     "add-every-30s": {
#         "task": "assets.tasks.add2",
#         "schedule": 30.0,
#         "args": (3, 8)
#     }
# }
ALICLOUD_TOKEN = environ.get("ClOUDFLARE_TOKEN")
