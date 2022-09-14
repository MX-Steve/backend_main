# pylint: disable=wildcard-import,unused-wildcard-import
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'HOST': "127.0.0.1",
        'PORT': 3306,
        'USER': "root",
        'PASSWORD': "123456",
    }
}
HELLO_APP_ID = "cli_a1543517eaf9100b"
HELLO_APP_SECRET = "hjaC6YU7LF25DQNY3aNkkcjfu6PKD7xr"
JENKINS_HOST = "http://121.43.41.139:8080/"
JENKINS_USER = "admin"
JENKINS_PASSWD = "root123"
REDIS_PORT = 6379
REDIS_PASS = "123456"
CMDB_BACK_PORT = 8000
ITSMURL = "http://localhost:9093/approval/v2/process"
# 最重要的配置，设置消息broker,格式为：db://user:password@host:port/dbname
CELERY_BROKER_URL = "redis://:%s@127.0.0.1:%s/0" % (REDIS_PASS, REDIS_PORT)
ASGI_APPLICATION = 'djentry.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": ["redis://:%s@127.0.0.1:%s/1" % (REDIS_PASS, REDIS_PORT)],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    },
}

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