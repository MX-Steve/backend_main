import logging
from django.http import JsonResponse
from django.db.models import Count, Q
# pylint: disable=no-name-in-module
from assets.models import ZoneInfo, DeviceType, DeviceStatus
from assets.serializers import *
from utils import baseview
from utils.util import now
from utils.auth import auth
from audit.apis.audit import PutAudit

logger = logging.getLogger("ttool.app")


class ZoneInfoView(baseview.BaseView):
    """
    get:
        获取所有区域
    put:
        更新区域
    post:
        新增区域
    delete:
        删除区域
    """
    @auth("assets.basic.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "区域信息更新成功."}
        needs = {"id", "name", "description"}
        if set(data.keys()).intersection(needs) != needs:
            res = {
                "code": 10003,
                "data": {},
                "msg": "需要参数 id,name,description"
            }
        else:
            name = data["name"].strip()
            if name == "":
                res = {"code": 10005, "data": {}, "msg": "参数 name 值不能为空."}
            if not ZoneInfo.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "区域不存在无法更新."}
            ZoneInfo.objects.filter(id=data["id"]).update(
                name=name, description=data["description"].strip())
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        if id != "":
            serializer = ZoneInfoSerializers(ZoneInfo.objects.filter(
                id=id, del_tag=0),
                many=True)
        else:
            serializer = ZoneInfoSerializers(
                ZoneInfo.objects.filter(del_tag=0), many=True)
        return JsonResponse({
            "code": 200,
            "data": serializer.data,
            "msg": "获取区域数据成功"
        })

    @auth("assets.basic.edit")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "区域创建成功"}
        needs = {"name", "description"}
        if set(data.keys()) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要参数name, description."}
        else:
            if data["name"].strip() == "":
                res = {"code": 10005, "data": {}, "msg": "参数name值不能为空."}
            else:
                if ZoneInfo.objects.filter(name=data["name"],
                    del_tag=0).exists():
                    res = {"code": 10001, "data": {}, "msg": "区域已经存在，不能新建"}
                else:
                    if ZoneInfo.objects.filter(name=data["name"]).exists():
                        ZoneInfo.objects.filter(name=data["name"]).update(
                            description=data["description"].strip(), del_tag=0)
                    else:
                        ZoneInfo.objects.create(
                            name=data["name"].strip(),
                            description=data["description"].strip(),
                            del_tag=0)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "区域删除成功."}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数id."}
        else:
            if not ZoneInfo.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "区域不存在，不能删除."}
            else:
                ZoneInfo.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)
