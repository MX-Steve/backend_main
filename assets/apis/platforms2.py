import datetime
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


def getMsg(item):
    total_cpu = 0
    total_mem = 0
    total_disk = 0
    cpus = item["cpu_total"]
    mem = item["mem_total"]
    disk = item["disk_total"]
    cpu_top_avg = item["cpu_top_avg"]
    mem_top_avg = item["mem_top_avg"]
    total_cpu += cpus
    total_mem += mem
    total_disk += disk
    return "%d_%d_%d_%.3f_%.3f" % (total_cpu, total_mem, total_disk, cpu_top_avg, mem_top_avg)


class PlatformQixinTotalView(baseview.BaseView):
    """
    get:
        获取域汇总信息
    """
    @auth("dashboard.qixin.view")
    def get(self, request, args=None):
        xitong = request.GET.get('xitong', '')
        fuwu = request.GET.get('fuwu', '')
        zone = request.GET.get('zone', '')
        q = Q()
        q.children.append(("del_tag",0))
        if xitong:
            q.children.append(("xitong__contains", xitong))
        if fuwu:
            q.children.append(("fuwu__contains", fuwu))
        if zone:
            q.children.append(("zone__contains", zone))
        serializer = PlatformQixinSerializers(PlatformQixin.objects.filter(q),
                                              many=True)
        objs = serializer.data
        total_num = len(objs)
        total_cpu = 0
        total_mem = 0
        total_disk = 0
        total_cpu_use = 0
        total_mem_use = 0
        for item in objs:
            result = getMsg(item)
            results = result.split("_")
            total_cpu += int(results[0])
            total_mem += int(results[1])
            total_disk += int(results[2])
            total_cpu_use += float(results[3])
            total_mem_use += float(results[4])
        total_mem_avg = total_mem_use / len(objs)
        total_cpu_avg = total_cpu_use / len(objs)
        return JsonResponse({
            "code": 200,
            "data": {
                "total": {
                    "num": total_num,
                    "cpu": total_cpu,
                    "mem": total_mem,
                    "disk": total_disk,
                    "total_mem_avg": total_mem_avg,
                    "total_cpu_avg": total_cpu_avg
                },
            },
            "msg": "获取数据成功"
        })


class PlatformQixinView(baseview.BaseView):
    """
    get:
        获取所有机器
    """
    @auth("dashboard.qixin.view")
    def get(self, request, args=None):
        hostname = request.GET.get('hostname', '')
        host_ip = request.GET.get('host_ip', '')
        proxy = request.GET.get('proxy', '')
        cpu_avg = request.GET.get('cpu_avg', '')
        cpu_max = request.GET.get('cpu_max', '')
        cpu_top_avg = request.GET.get('cpu_top_avg', '')
        mem_pused_avg = request.GET.get('mem_pused_avg', '')
        mem_pused_calu_avg = request.GET.get('mem_pused_calu_avg', '')
        mem_pused_max = request.GET.get('mem_pused_max', '')
        mem_pused_calu_max = request.GET.get('mem_pused_calu_max', '')
        mem_top_avg = request.GET.get('mem_top_avg', '')
        xitong = request.GET.get('xitong', '')
        fuwu = request.GET.get('fuwu', '')
        zone = request.GET.get('zone', '')
        cpu_total = request.GET.get('cpu_total', '')
        mem_total = request.GET.get('mem_total', '')
        disk_total = request.GET.get('disk_total', '')
        xuliehao = request.GET.get('xuliehao', '')
        xitongleixing = request.GET.get('xitongleixing', '')
        jifang = request.GET.get('jifang', '')
        jijia = request.GET.get('jijia', '')
        fuzeren = request.GET.get('fuzeren', '')
        vip = request.GET.get('vip', '')
        xitongbanben = request.GET.get('xitongbanben', '')
        insert_date = request.GET.get('insert_date', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = (pageNo - 1) * pageSize
        end = pageNo * pageSize
        q = Q()
        q.children.append(("del_tag",0))
        if hostname:
            q.children.append(("hostname__contains", hostname))
        if host_ip:
            q.children.append(("host_ip__contains", host_ip))
        if proxy:
            q.children.append(("proxy__contains", proxy))
        if vip:
            q.children.append(("vip__contains", vip))
        if cpu_avg:
            q.children.append(("cpu_avg__contains", cpu_avg))
        if cpu_max:
            q.children.append(("cpu_max__contains", cpu_max))
        if cpu_top_avg:
            q.children.append(("cpu_top_avg__contains", cpu_top_avg))
        if mem_pused_avg:
            q.children.append(("mem_pused_avg__contains", mem_pused_avg))
        if mem_pused_calu_avg:
            q.children.append(
                ("mem_pused_calu_avg__contains", mem_pused_calu_avg))
        if mem_pused_max:
            q.children.append(("mem_pused_max__contains", mem_pused_max))
        if mem_pused_calu_max:
            q.children.append(
                ("mem_pused_calu_max__contains", mem_pused_calu_max))
        if mem_top_avg:
            q.children.append(("mem_top_avg__contains", mem_top_avg))
        if xitong:
            q.children.append(("xitong__contains", xitong))
        if fuwu:
            q.children.append(("fuwu__contains", fuwu))
        if zone:
            q.children.append(("zone__contains", zone))
        if cpu_total:
            q.children.append(("cpu_total__contains", cpu_total))
        if mem_total:
            q.children.append(("mem_total__contains", mem_total))
        if disk_total:
            q.children.append(("disk_total__contains", disk_total))
        if xuliehao:
            q.children.append(("xuliehao__contains", xuliehao))
        if xitongleixing:
            q.children.append(("xitongleixing__contains", xitongleixing))
        if jifang:
            q.children.append(("jifang__contains", jifang))
        if jijia:
            q.children.append(("jijia__contains", jijia))
        if fuzeren:
            q.children.append(("fuzeren__contains", fuzeren))
        if xitongbanben:
            q.children.append(("xitongbanben__contains", xitongbanben))
        if insert_date:
            q.children.append(("insert_date__contains", insert_date))
        serializer = PlatformQixinSerializers(
            PlatformQixin.objects.filter(q), many=True)
        zones = []
        xitongs = []
        fuwus = []
        for item in serializer.data:
            if item["zone"] not in zones:
                zones.append(item["zone"])
            if item["xitong"] not in xitongs:
                xitongs.append(item["xitong"])
            if item["fuwu"] not in fuwus:
                fuwus.append(item["fuwu"])
        total = len(serializer.data)
        data = serializer.data[start:end]
        return JsonResponse({
            "code": 200,
            "data": {"hosts": data, "zones": zones, "xitongs": xitongs, "fuwus": fuwus, "total": total},
            "msg": "获取机器数据成功"
        })


class PlatformQixinDownView(baseview.BaseView):
    """
    get:
        获取所有机器
    """
    @auth("dashboard.qixin.view")
    def get(self, request, args=None):
        q = Q()
        q.children.append(("del_tag",0))
        serializer = PlatformQixinSerializers(
            PlatformQixin.objects.filter(q), many=True)
        objs = serializer.data
        total = {}
        for obj in objs:
            zone = obj["zone"]
            if zone not in total:
                total[zone] = {}
            xitong = obj["xitong"]
            fuwu = obj["fuwu"]
            xitongleixing = obj["xitongleixing"]
            if xitong not in total[zone]:
                total[zone][xitong] = {}
            if fuwu not in total[zone][xitong]:
                total[zone][xitong][fuwu] = {}
            if xitongleixing not in total[zone][xitong][fuwu]:
                total[zone][xitong][fuwu][xitongleixing] = {
                    "cpu": int(obj["cpu_total"]),
                    "mem": int(obj["mem_total"]),
                    "disk": int(obj["disk_total"]),
                    "num": 1,
                    "total_cpu": float(obj["cpu_top_avg"]),
                    "total_mem": float(obj["mem_top_avg"])
                }
            total[zone][xitong][fuwu][xitongleixing]["num"] += 1
            total[zone][xitong][fuwu][xitongleixing]["cpu"] += int(obj["cpu_total"])
            total[zone][xitong][fuwu][xitongleixing]["mem"] += int(obj["mem_total"])
            total[zone][xitong][fuwu][xitongleixing]["disk"] += int(obj["disk_total"])
            total[zone][xitong][fuwu][xitongleixing]["total_cpu"] += int(obj["cpu_top_avg"])
            total[zone][xitong][fuwu][xitongleixing]["total_mem"] += int(obj["mem_top_avg"])
        return JsonResponse({
            "code": 200,
            "data": total,
            "msg": "获取机器数据成功"
        })


class PlatformQixinMoreView(baseview.BaseView):
    """
    get:
        获取详细信息
    """
    @auth("dashboard.qixin.view")
    def get(self, request, args=None):
        ip_input = request.GET.get('ip_input', '')
        date_created = datetime.datetime.now().strftime("%Y-%m-%d")
        q = Q()
        q.children.append(("ip_input", ip_input))
        q.children.append(("date_created__contains",date_created))
        serializer = PlatformQixinMoreSerializers(
            PlatformQixinMore.objects.filter(q), many=True)
        data = serializer.data
        return JsonResponse({
            "code": 200,
            "data": {"details": data},
            "msg": "获取机器详情数据成功"
        })

