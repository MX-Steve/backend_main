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


class DeviceTypeView(baseview.BaseView):
    """
    get:
        获取所有设备类型
    put:
        更新设备类型
    post:
        新增设备类型
    delete:
        删除设备类型
    """
    @auth("assets.basic.view")
    def get(self, request, args=None):
        id = request.GET.get("id", "")
        if id != "":
            serializer = DeviceTypeSerializers(DeviceType.objects.filter(
                id=id, del_tag=0),
                many=True)
        else:
            q = Q()
            q.children.append(("del_tag", 0))
            name = request.GET.get("name", "")
            if name:
                q.children.append(("name", name))
            serializer = DeviceTypeSerializers(DeviceType.objects.filter(q),
                                               many=True)
        return JsonResponse({
            "code": 200,
            "data": serializer.data,
            "msg": "获取设备类型成功[资产标签]"
        })

    @auth("assets.basic.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "更新设备类型成功."}
        needs = {"name", "id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id，name"}
        else:
            if data["name"].strip() == "":
                res = {"code": 10005, "data": {}, "msg": "参数 name 值不能为空."}
            else:
                if int(data["id"]) in [1, 2, 3]:
                    res = {"code": 10005, "data": {}, "msg": "当前数据无法修改"}
                else:
                    if not DeviceType.objects.filter(id=data["id"]).exists():
                        res = {"code": 10002, "data": {}, "msg": "设备类型不存在."}
                    else:
                        DeviceType.objects.filter(id=data["id"]).update(
                            name=data["name"].strip())
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "创建设备类型成功"}
        if "name" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数 name."}
        elif data["name"].strip() == "":
            res = {"code": 10005, "data": {}, "msg": "参数 name 值不能为空."}
        else:
            if DeviceType.objects.filter(name=data["name"],
                                         del_tag=0).exists():
                res = {"code": 10001, "data": {}, "msg": "设备类型已经存在，不能新增"}
            else:
                if DeviceType.objects.filter(name=data["name"]).exists():
                    DeviceType.objects.filter(name=data["name"]).update(
                        del_tag=0)
                else:
                    DeviceType.objects.create(name=data["name"].strip(),
                                              del_tag=0)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除设备类型成功."}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数 id."}
        else:
            if not DeviceType.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "设备类型不存在，无法删除"}
            else:
                DeviceType.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)


class DeviceStatusView(baseview.BaseView):
    """
    get:
        获取所有设备状态
    put:
        更新设备状态
    post:
        新增设备状态
    delete:
        删除设备状态
    """
    @auth("assets.basic.view")
    def get(self, request, args=None):
        id = request.GET.get("id", "")
        if id != "":
            serializer = DeviceStatusSerializers(DeviceStatus.objects.filter(
                id=id, del_tag=0),
                many=True)
        else:
            data = []
            type_id = request.GET.get("type_id", "")
            if type_id:
                serializer = DeviceStatusSerializers(
                    DeviceStatus.objects.filter(del_tag=0, type_id=type_id),
                    many=True)
                data.extend(serializer.data)
            else:
                serializer = DeviceStatusSerializers(
                    DeviceStatus.objects.filter(del_tag=0), many=True)
                data.extend(serializer.data)
        return JsonResponse({"code": 200, "data": data, "msg": "获取设备状态成功"})

    @auth("assets.basic.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "设备状态更新成功."}
        needs = {"name", "id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要参数 id,name"}
        else:
            name = data["name"].strip()
            if name == "":
                res = {"code": 10005, "data": {}, "msg": "参数 name 不能为空."}
            else:
                if not DeviceStatus.objects.filter(id=data["id"]).exists():
                    res = {"code": 10002, "data": {}, "msg": "设备状态不存在."}
                else:
                    DeviceStatus.objects.filter(id=data["id"]).update(
                        name=name,
                        type_id=data["type_id"],
                        description=data["description"])
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增设备状态成功"}
        if "name" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数 10003."}
        else:
            if data["name"].strip() == "":
                res = {"code": 10005, "data": {}, "msg": "参数 name 不能为空."}
            else:
                if DeviceStatus.objects.filter(name=data["name"],
                                               type_id=data["type_id"],
                                               del_tag=0).exists():
                    res = {"code": 10001, "data": {}, "msg": "设备状态已经存在."}
                else:
                    if DeviceStatus.objects.filter(name=data["name"], type_id=data["type_id"]).exists():
                        DeviceStatus.objects.filter(name=data["name"], type_id=data["type_id"]).update(
                            del_tag=0,
                            type_id=data["type_id"],
                            description=data["description"])
                    else:
                        DeviceStatus.objects.create(
                            name=data["name"].strip(),
                            del_tag=0,
                            type_id=data["type_id"],
                            description=data["description"])
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "设备状态删除成功."}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数 id."}
        else:
            if not DeviceStatus.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "设备状态不存在"}
            else:
                DeviceStatus.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)


class IdleAssetsView(baseview.BaseView):
    """
    get:
        获取所有闲置资产
    put:
        更新闲置资产
    post:
        新增闲置资产
    delete:
        删除闲置资产
    """
    @auth("assets.basic.view")
    def get(self, request, args=None):
        id = request.GET.get("id", "")
        if id != "":
            serializer = IdleAssetsSerializers(IdleAssets.objects.filter(
                id=id, del_tag=0),
                many=True)
        else:
            serializer = IdleAssetsSerializers(
                IdleAssets.objects.filter(del_tag=0), many=True)
        return JsonResponse({
            "code": 200,
            "data": serializer.data,
            "msg": "获取闲置资产信息成功"
        })

    @auth("assets.basic.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "更新闲置资产信息成功."}
        needs = {"id", "idc", "name", "count", "description"}
        if set(data.keys()).intersection(needs) != needs:
            res = {
                "code": 10003,
                "data": {},
                "msg": "需要携带参数 id,name,idc,count,description"
            }
        else:
            if not DeviceType.objects.filter(name=data["name"],
                                             del_tag=0).exists():
                res = {"code": 10002, "data": {}, "msg": "设备类型不存在."}
            else:
                if not IdleAssets.objects.filter(id=data["id"]).exists():
                    res = {"code": 10002, "data": {}, "msg": "闲置资产不存在."}
                else:
                    IdleAssets.objects.filter(id=data["id"]).update(
                        name=data["name"],
                        idc=data["idc"],
                        count=int(data["count"]),
                        recorder=request.user.username,
                        description=data["description"],
                        update_time=now())
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "创建闲置资产信息成功."}
        needs = {"idc", "name", "count", "description"}
        if set(data.keys()) != needs:
            res = {
                "code": 10003,
                "data": {},
                "msg": "需要参数 idc,name,count,description."
            }
        else:
            if not DeviceType.objects.filter(name=data["name"],
                                             del_tag=0).exists():
                res = {"code": 10002, "data": {}, "msg": "设备类型不存在."}
            else:
                if IdleAssets.objects.filter(name=data["name"],
                                             idc=data["idc"],
                                             del_tag=0).exists():
                    res = {"code": 10001, "data": {}, "msg": "闲置资产信息已存在"}
                else:
                    if IdleAssets.objects.filter(name=data["name"],
                                                 idc=data["idc"]).exists():
                        IdleAssets.objects.filter(
                            name=data["name"],
                            idc=data["idc"]).update(del_tag=0)
                    else:
                        IdleAssets.objects.create(
                            name=data["name"],
                            idc=data["idc"],
                            count=int(data["count"]),
                            recorder=request.user.username,
                            description=data["description"],
                            update_time=now(),
                            del_tag=0)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.basic.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除闲置资产信息成功."}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数 id."}
        else:
            if not IdleAssets.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "闲置资产信息不存在"}
            else:
                IdleAssets.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)
