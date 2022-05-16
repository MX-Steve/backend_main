import json
import requests
import time
import sys, os, logging
from django.conf import settings

#初始化logger
logger = logging.getLogger("djentry.app")
# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')


def request_method(url, headers, data):
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    return r.json()


class ApprovalT():
    def __init__(self) -> None:
        self.app_id = settings.HELLO_APP_ID
        self.app_secret = settings.HELLO_APP_SECRET
        self.headers = {
            "content-type": "application/json; charset=utf-8",
            "Authorization": ""
        }

    # 获取租户 access token
    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"content-type": "application/json; charset=utf-8"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        res = request_method(url, headers, data)
        if res["code"] == 0:
            self.headers[
                "Authorization"] = "Bearer " + res["tenant_access_token"]

    # 订阅审批事件
    def subscribe_events(self, appproval_code):
        url = "https://www.feishu.cn/approval/openapi/v2/subscription/subscribe"
        headers = self.headers
        data = {"approval_code": appproval_code}
        res = request_method(url, headers, data)
        return res

    # 取消订阅审批事件
    def unsubscribe_events(self, approval_code):
        url = "https://www.feishu.cn/approval/openapi/v2/subscription/unsubscribe"
        headers = self.headers
        data = {"approval_code": approval_code}
        res = request_method(url, headers, data)
        return res

    # 获取审批定义详情
    def approval_details(self, approval_code):
        url = "https://www.feishu.cn/approval/openapi/v2/approval/get"
        headers = self.headers
        data = {"approval_code": approval_code, "locale": "en-US"}
        res = request_method(url, headers, data)
        return res

    # 批量获取审批实例
    def get_instance_list(self, approval_code):
        url = "https://www.feishu.cn/approval/openapi/v2/instance/list"
        end_time = int(time.time() * 1000)
        start_time = int((time.time() - 3 * 24 * 60 * 60) * 1000)
        headers = self.headers
        data = {
            "approval_code": approval_code,
            "start_time": start_time,
            "end_time": end_time,
            "offset": 0,
            "limit": 100
        }
        res = request_method(url, headers, data)
        return res

    # 获取单个审批实例详情
    def get_instance(self, instance_code):
        url = "https://www.feishu.cn/approval/openapi/v2/instance/get"
        headers = self.headers
        data = {
            "instance_code": instance_code,
            "locale": "zh-CN",
            "open_id": "",
            "user_id": ""
        }
        res = request_method(url, headers, data)
        return res

    # 审批任务同意
    def approve_instance(self, approval_code, instance_code):
        url = "https://www.feishu.cn/approval/openapi/v2/instance/approve"
        headers = self.headers
        data = {
            "approval_code": approval_code,
            "instance_code": instance_code,
        }

    # 通过邮箱获取用户 open_id
    def get_open_id(self, email):
        url = "https://open.feishu.cn/open-apis/user/v1/batch_get_id?emails=%s" % (
            email)
        headers = self.headers
        r = requests.get(url=url, headers=headers)
        return r.json()

    def send_data(self, chat_id, user_id, msg):
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = self.headers
        data = {
            "receive_id":
            chat_id,
            "content":
            "{\"text\":\"<at user_id=\\\"%s\\\">Tom</at> %s\"}" %
            (user_id, msg),
            "msg_type":
            "text"
        }
        res = request_method(url, headers, data)
        return res

    def send_card_data_self(self,color, title, open_id, username, approval_name, address):
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        headers = self.headers
        data = {
            "receive_id":
            open_id,
            "content":
            "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"template\": \"%s\",\"title\":{\"tag\":\"plain_text\",\"content\":\"%s\"}},\"elements\":[{\"tag\":\"div\",\"fields\":[{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**申请人**\\n%s\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**审批流**\\n[%s]\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"**时间：**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"**地址：**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}}]}]}"
            % (color, title, username, approval_name, now, address),
            "msg_type":
            "interactive"
        }
        res = request_method(url, headers, data)
        return res

    def send_card_data(self, chat_id, username, env, project, service,
                       jenkins_url, result):
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        headers = self.headers
        if result == "SUCCESS":
            color = "green"
            title = "服务发布成功"
        else:
            color = "red"
            title = "服务发布失败"
        data = {
            "receive_id":
            chat_id,
            "content":
            "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"template\": \"%s\",\"title\":{\"tag\":\"plain_text\",\"content\":\"%s\"}},\"elements\":[{\"tag\":\"div\",\"fields\":[{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**申请人**\\n%s\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**服务**\\n[%s][%s][%s]\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"**时间：**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**详情**\\n%s\"}}]},{\"tag\":\"hr\"}]}"
            %
            (color, title, username, env, project, service, now, jenkins_url),
            "msg_type":
            "interactive"
        }
        res = request_method(url, headers, data)
        return res
    
    def send_card_data_test(self, open_id, username, env, project, service,
                       jenkins_url, result):
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if result == "SUCCESS":
            color = "green"
            title = "服务发布成功"
        else:
            color = "red"
            title = "服务发布失败"
        headers = self.headers
        data = {
            "receive_id":
            open_id,
            "content":
            "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"template\": \"%s\",\"title\":{\"tag\":\"plain_text\",\"content\":\"%s\"}},\"elements\":[{\"tag\":\"div\",\"fields\":[{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**申请人**\\n%s\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**服务**\\n[%s][%s][%s]\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"**时间：**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**详情**\\n%s\"}}]},{\"tag\":\"hr\"}]}"
            %
            (color, title, username, env, project, service, now, jenkins_url),
            "msg_type":
            "interactive"
        }
        res = request_method(url, headers, data)
        return res
    
    def need_roles(self, open_id, username, role):
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        color = "green"
        title = "角色申请"
        headers = self.headers
        data = {
            "receive_id": open_id,
            "content": "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"template\": \"%s\",\"title\":{\"tag\":\"plain_text\",\"content\":\"%s\"}},\"elements\":[{\"tag\":\"div\",\"fields\":[{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**申请人**\\n%s\"}},{\"is_short\":true,\"text\":{\"tag\":\"lark_md\",\"content\":\"**申请角色**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"**时间：**\\n%s\"}},{\"is_short\":false,\"text\":{\"tag\":\"lark_md\",\"content\":\"\"}}]},{\"tag\":\"hr\"}]}"%(color, title, username, role, now),
            "msg_type": "interactive"
        }
        res = request_method(url, headers, data)
        return res


if __name__ == "__main__":
    app = ApprovalT()
    app.get_tenant_access_token()
    print(app)
    # app = ApprovalT()
    # app.get_tenant_access_token()
    # res = app.get_instance_list("D9E74921-D5C0-4056-921B-B0A74B415596")
    # instance_code_list = res["data"]["instance_code_list"]
    # for instance_code in instance_code_list:
    #     res = app.get_instance(instance_code)
    #     print("单个审批实例详情")
    #     data = res['data']
    #     approval_code = data["approval_code"]
    #     approval_name = data["approval_name"]
    #     open_id = data["open_id"]
    #     form = data["form"]
    #     print(approval_code)
    #     print(approval_name)
    #     print(open_id)
    #     print(form)
    #     print(instance_code)
