from rest_framework import serializers
from .models import AuditHistory
from users.models import User
import json


def user_obj_reverse(data):
    if data["req_url"] == "/users/v1/login":
        data["req_method"] = "users:登录"
        data["req_data"] = json.dumps({
            "username":
            json.loads(data["req_data"])["username"],
            "password":
            "******"
        })
    elif data["req_url"] == "/users/v1/logout":
        data["req_method"] = "users:退出"
    elif data["req_url"] == "/users/v1/users":
        req_data = json.loads(data["req_data"])
        if req_data["type"] == "status":
            data["req_method"] = "users:修改用户状态"
        elif req_data["type"] == "roles":
            data["req_method"] = "users:修改用户角色"
        else:
            data["req_method"] = "users:更新机器人"
    elif data["req_url"] == "/users/v1/robot-msg":
        data["req_method"] = "users:角色申请"
    return data

def tools_obj_reverse(data):
    if data["req_url"].endswith("/alarm"):
        key = "闹钟"
    elif data["req_url"].endswith("/meat-menus"):
        key = "食谱"
    elif data["req_url"].endswith("/articles"):
        key = "资料"
    elif data["req_url"].endswith("/process-history"):
        key = "执行历史"
    elif data["req_url"].endswith("/process"):
        key = "流程"
    elif data["req_url"].endswith("/article-down"):
        key = "文章下载"
    else:
        key = "未知"
    if data["req_method"] == "POST":
        data["req_method"] = "tools:新增%s" % (key)
    elif data["req_method"] == "PUT":
        data["req_method"] = "tools:更新%s" % (key)
    else:
        data["req_method"] = "tools:移除%s" % (key)
    return data


def chat_obj_reverse(data):
    if data["req_url"].endswith("/intervals"):
        key = "周期"
    elif data["req_url"].endswith("/tasks"):
        key = "设备类型"
    elif data["req_url"].endswith("/crontab"):
        key = "crontab"
    else:
        key = "未知"
    if data["req_method"] == "POST":
        data["req_method"] = "job:新增%s" % (key)
    elif data["req_method"] == "PUT":
        data["req_method"] = "job:更新%s" % (key)
    else:
        data["req_method"] = "job:移除%s" % (key)
    return data


def assets_obj_reverse(data):
    if data["req_url"].endswith("/zones"):
        key = "区域"
    elif data["req_url"].endswith("/device-type"):
        key = "设备类型"
    elif data["req_url"].endswith("/device-status"):
        key = "设备状态"
    elif data["req_url"].endswith("/idc"):
        key = "机房"
    elif data["req_url"].endswith("/machine"):
        key = "机器"
    elif data["req_url"].endswith("/rds"):
        key = "rds"
    elif data["req_url"].endswith("/disk"):
        key = "磁盘"
    elif data["req_url"].endswith("/domain"):
        key = "域名"
    elif data["req_url"].endswith("/oss"):
        key = "存储桶"
    elif data["req_url"].endswith("/vpc"):
        key = "vpc"
    elif data["req_url"].endswith("/slb"):
        key = "slb"
    elif data["req_url"].endswith("/switch"):
        key = "交换机"
    elif data["req_url"].endswith("/environment"):
        key = "环境"
    elif data["req_url"].endswith("/project"):
        key = "项目"
    elif data["req_url"].endswith("/services"):
        key = "服务"
    elif data["req_url"].endswith("/record"):
        key = "域名解析"
    else:
        key = "未知"
    if data["req_method"] == "POST":
        data["req_method"] = "assets:新增%s" % (key)
    elif data["req_method"] == "PUT":
        data["req_method"] = "assets:更新%s" % (key)
    else:
        data["req_method"] = "assets:移除%s" % (key)


def approval_obj_reverse(data):
    if data["req_url"].endswith("/v1/subscribe"):
        key = "飞书订阅"
    elif data["req_url"].endswith("/v1/instance"):
        key = "工单流程发布状态"
    elif data["req_url"].endswith("/v2/approval"):
        key = "工单审批流"
    elif data["req_url"].endswith("/v2/form"):
        key = "表单审批工单"
    elif data["req_url"].endswith("/v2/subscribe"):
        key = "流程订阅禁用"
    elif data["req_url"].endswith("/v2/change-version"):
        key = "版本切换"
    elif data["req_url"].endswith("/v2/node"):
        key = "流程节点"
    elif data["req_url"].endswith("/v2/instance"):
        key = "审批实例"
    elif data["req_url"].endswith("/v2/fiform"):
        key = "实例表单"
    elif data["req_url"].endswith("/v2/tasks"):
        key = "实例流程"
    elif data["req_url"].endswith("/v2/task-modify-user"):
        key = "审批人更新"
    elif data["req_url"].endswith("/v2/direct-deploy"):
        key = "jenkins直接触发"
    elif data["req_url"].endswith("/v2/upload-file"):
        key = "上传文件"
    elif data["req_url"].endswith("/v2/download-file"):
        key = "下载文件"
    else:
        key = "未知"
    if data["req_method"] == "POST":
        data["req_method"] = "approval:新增%s" % (key)
    elif data["req_method"] == "PUT":
        data["req_method"] = "approval:更新%s" % (key)
    else:
        data["req_method"] = "approval:移除%s" % (key)
    return data


def manage_obj_reverse(data):
    if data["req_url"].endswith("/v1/role"):
        key = "角色"
    else:
        key = "未知"
    if data["req_method"] == "POST":
        data["req_method"] = "manages:新增%s" % (key)
    elif data["req_method"] == "PUT":
        data["req_method"] = "manages:更新%s" % (key)
    else:
        data["req_method"] = "manages:移除%s" % (key)
    return data


def obj_reverse(data):
    # users
    if "users" in data["req_url"]:
        data = user_obj_reverse(data)
    elif "chat" in data["req_url"]:
        # chat
        data = chat_obj_reverse(data)
    elif "assets" in data["req_url"]:
        # assets
        data = assets_obj_reverse(data)
    elif "approval" in data["req_url"]:
        # approval
        data = approval_obj_reverse(data)
    elif "v1/role" in data["req_url"]:
        # manages
        data = manage_obj_reverse(data)
    elif "tools" in data["req_url"]:
        # tools
        data = tools_obj_reverse(data)
    if data:
        if data["operate_time"]:
            data["operate_time"] = data["operate_time"].replace(
                "T", " ").split("+")[0]
        data["res_data"] = json.loads(data["res_data"])
        data["req_data"] = json.loads(data["req_data"])
    return data


class AuditHistorySerializer(serializers.ModelSerializer):
    """audit history serializer"""
    class Meta:
        model = AuditHistory
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(username=data["operater"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["operater"] = un
        data = obj_reverse(data)
        return data