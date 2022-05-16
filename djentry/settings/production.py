# pylint: disable=wildcard-import,unused-wildcard-import
from os import environ
import pymysql
from djentry.settings.common import *

pymysql.install_as_MySQLdb()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = ["*"]
DEBUG = True

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': environ.get("CLOVER_MYSQL_DB"),
        'USER': environ.get("CLOVER_MYSQL_USER"),
        'PASSWORD': environ.get("CLOVER_MYSQL_PASSWORD"),
        'HOST': environ.get("CLOVER_MYSQL_HOST"),
        'PORT': environ.get("CLOVER_MYSQL_PORT") or '3306'
    }
}
HELLO_APP_ID = environ.get("HELLO_APP_ID")
HELLO_APP_SECRET = environ.get("HELLO_APP_SECRET")
JENKINS_HOST = "http://121.43.41.139:8080/"
JENKINS_USER = "admin"
JENKINS_PASSWD = "root123"
REDIS_PORT = environ.get("REDIS_PORT")
REDIS_PASS = environ.get("REDIS_PASS")
CMDB_BACK_PORT = environ.get("CMDB_BACK_PORT")
ITSMURL = environ.get("ITSMURL")
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
ALICLOUD_SECRET_KEY2 = environ.get("ALICLOUD_")
#Cloudflare
ALICLOUD_TOKEN = environ.get("ClOUDFLARE_TOKEN")