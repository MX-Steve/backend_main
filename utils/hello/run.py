import os
from utils.hello.api import MessageApiClient
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')


def Run(open_id, msg):
    APP_ID = settings.HELLO_APP_ID
    APP_SECRET = settings.HELLO_APP_SECRET
    LARK_HOST = "https://open.feishu.cn"
    message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)
    text_content = """{"text":"%s"}""" % (msg)
    message_api_client.send_text_with_open_id(open_id, text_content)