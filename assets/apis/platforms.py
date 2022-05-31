from django.http import JsonResponse
from django.db.models import Count, Q
from assets.models import PlatformHosts
from assets.serializers import *
from utils import baseview
from utils.auth import auth
from audit.apis.audit import PutAudit


class PlatformHostsView(baseview.BaseView):
    """
    get:
        获取所有机器
    put:
        更新机器
    post:
        新增机器
    delete:
        删除机器
    """
    @auth("assets.platform-hosts.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "机器信息更新成功."}
        needs = {"v_pool",
                 "zone",
                 "tenant",
                 "hostname",
                 "host_type",
                 "ssh_user",
                 "ssh_pwd",
                 "ssh_port",
                 "vpc",
                 "iso",
                 "system_disk_size",
                 "cpus",
                 "memery",
                 "data_disk_size",
                 "data_disk_type",
                 "host_ip",
                 "uuid",
                 "vip",
                 "system_type",
                 "description"}
        if set(data.keys()).intersection(needs) != needs:
            res = {
                "code": 10003,
                "data": {},
                "msg": "需要参数不对"
            }
        else:
            if not PlatformHosts.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "机器不存在无法更新."}
            PlatformHosts.objects.filter(id=data["id"]).update(**data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.platform-hosts.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        v_pool = request.GET.get('v_pool', '')
        zone = request.GET.get('zone', '')
        tenant = request.GET.get('tenant', '')
        hostname = request.GET.get('hostname', '')
        host_type = request.GET.get('host_type', '')
        ssh_user = request.GET.get('ssh_user', '')
        vpc = request.GET.get('vpc', '')
        iso = request.GET.get('iso', '')
        host_ip = request.GET.get('host_ip', '')
        uuid = request.GET.get('uuid', '')
        vip = request.GET.get('vip', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = (pageNo - 1) * pageSize
        end = pageNo * pageSize
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(("id", id))
        if v_pool:
            q.children.append(("v_pool__contains", v_pool))
        if zone:
            q.children.append(("zone__contains", zone))
        if tenant:
            q.children.append(("tenant__contains", tenant))
        if hostname:
            q.children.append(("hostname__contains", hostname))
        if host_type:
            q.children.append(("host_type__contains", host_type))
        if ssh_user:
            q.children.append(("ssh_user__contains", ssh_user))
        if vpc:
            q.children.append(("vpc__contains", vpc))
        if iso:
            q.children.append(("iso__contains", iso))
        if host_ip:
            q.children.append(("host_ip__contains", host_ip))
        if uuid:
            q.children.append(("uuid", uuid))
        if vip:
            q.children.append(("vip__contains", vip))
        serializer = PlatformHostsSerializers(
            PlatformHosts.objects.filter(q), many=True)
        total = len(serializer.data)
        data = serializer.data[start:end]
        return JsonResponse({
            "code": 200,
            "data": {"hosts": data, "total": total},
            "msg": "获取机器数据成功"
        })

    @auth("assets.platform-hosts.edit")
    def post(self, request, args=None):
        data = request.data
        data.pop("id")
        res = {"code": 200, "data": {}, "msg": "机器新增成功"}
        needs = {"v_pool",
                 "zone",
                 "tenant",
                 "hostname",
                 "host_type",
                 "ssh_user",
                 "ssh_pwd",
                 "ssh_port",
                 "vpc",
                 "iso",
                 "system_disk_size",
                 "cpus",
                 "memery",
                 "data_disk_size",
                 "data_disk_type",
                 "host_ip",
                 "uuid",
                 "vip",
                 "system_type",
                 "description"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要参数不对."}
        else:
            if data["hostname"].strip() == "":
                res = {"code": 10005, "data": {}, "msg": "参数hostname值不能为空."}
            else:
                if PlatformHosts.objects.filter(hostname=data["hostname"],
                                                del_tag=0).exists():
                    res = {"code": 10001, "data": {}, "msg": "机器已经存在，不能新建"}
                else:
                    PlatformHosts.objects.create(**data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("assets.platform-hosts.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "机器删除成功."}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要参数id."}
        else:
            if not PlatformHosts.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "机器不存在，不能删除."}
            else:
                PlatformHosts.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)
