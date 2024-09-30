from django.http import JsonResponse
from utils import baseview
from assets.models import Machine, IDC, DeviceStatus, DeviceType, BusinessProject, BusinessServices, PlatformQixin
from assets.serializers import *
from utils.auth import auth


class SummaryTotalView(baseview.BaseView):
    @auth("dashboard.dashboard.view")
    def get(self, request, args=None):
        total = Machine.objects.filter(del_tag=0).count()
        dt_ids = [1, 2, 3]
        dss = DeviceStatus.objects.filter(del_tag=0,
                                          type_id__in=dt_ids,
                                          name="运行中")
        ds_ids = []
        for ds in dss:
            ds_ids.append(ds.id)
        online = Machine.objects.filter(del_tag=0,
                                        status_id__in=ds_ids).count()
        dss2 = DeviceStatus.objects.filter(del_tag=0,
                                           type_id__in=dt_ids,
                                           name="已停止")
        dss2_ids = []
        for ds in dss2:
            dss2_ids.append(ds.id)
        offline = Machine.objects.filter(del_tag=0,
                                         status_id__in=dss2_ids).count()
        idcs = IDC.objects.filter(del_tag=0)
        idc_total_list = []
        for idc in idcs:
            idc_id = idc.id
            count = Machine.objects.filter(del_tag=0, idc_id=idc_id).count()
            if count > 0:
                idc_total_list.append({
                    "name": idc.name,
                    "percentage": int((count / total) * 100),
                    "count": count
                })
        physical_count = Machine.objects.filter(del_tag=0,
                                                server_type=1).count()
        cloud_count = Machine.objects.filter(del_tag=0, server_type=2).count()
        virtual_count = Machine.objects.filter(del_tag=0,
                                               server_type=3).count()
        projects = BusinessProject.objects.filter(del_tag=0).count()
        services = BusinessServices.objects.filter(del_tag=0).count()
        return JsonResponse({
            "code": 200,
            "data": {
                "header": {
                    "total": total,
                    "online": online,
                    "projects": projects,
                    "services": services,
                },
                "idc_total_list":
                idc_total_list,
                "assets_type_list": [
                    {
                        "name": "物理服务器",
                        "value": physical_count
                    },
                    {
                        "name": "云服务器",
                        "value": cloud_count
                    },
                    {
                        "name": "虚拟机",
                        "value": virtual_count
                    },
                ]
            },
            "msg": "获取数据成功"
        })


def getMsg(item):
    total_cpu = 0
    total_mem = 0
    total_disk = 0
    cpus = item["cpu_total"]
    mem = item["mem_total"]
    disk = item["disk_total"]
    total_cpu += cpus
    total_mem += mem
    total_disk += disk
    return "%d_%d_%d" % (total_cpu, total_mem, total_disk)


class SummaryCMDBTotalNewView(baseview.BaseView):
    @auth("dashboard.dashboard.view")
    def get(self, request, args=None):
        serializer = PlatformQixinZoneSerializers(PlatformQixinZone.objects.all(),
                                              many=True)
        objs = serializer.data
        total_num = 0
        total_cpu = 0
        total_mem = 0
        total_disk = 0
        deps={}
        for item in objs:
            cpu = item["cpu"]
            mem = item["mem"]
            disk = item["disk"]
            num = item["num"]
            total_num += num
            total_cpu += cpu
            total_mem += mem
            total_disk += disk
            if item["deps"] not in deps:
                deps[item["deps"]] = {
                    "cpu": item["cpu"],
                    "mem": item["mem"],
                    "num": item["num"],
                    "disk": item["disk"]
                }
        return JsonResponse({
            "code": 200,
            "data": {
                "total": {
                    "num": total_num,
                    "cpu": total_cpu,
                    "mem": total_mem,
                    "disk": total_disk
                },
                "deps": deps
            },
            "msg": "获取数据成功"
        })
        
        

class SummaryCMDBTotalView(baseview.BaseView):
    @auth("dashboard.dashboard.view")
    def get(self, request, args=None):
        serializer = PlatformQixinSerializers(PlatformQixin.objects.all(),
                                              many=True)
        objs = serializer.data
        total_num = len(objs)
        total_cpu = 0
        total_mem = 0
        total_disk = 0
        BSS_CRM_num = 0
        BSS_CRM_cpu = 0
        BSS_CRM_mem = 0
        BSS_CRM_disk = 0
        BSS_BILL_num = 0
        BSS_BILL_cpu = 0
        BSS_BILL_mem = 0
        BSS_BILL_disk = 0
        EDA_num = 0
        EDA_cpu = 0
        EDA_mem = 0
        EDA_disk = 0
        ITM_num = 0
        ITM_cpu = 0
        ITM_mem = 0
        ITM_disk = 0
        MSS_num = 0
        MSS_cpu = 0
        MSS_mem = 0
        MSS_disk = 0
        OSS_num = 0
        OSS_cpu = 0
        OSS_mem = 0
        OSS_disk = 0
        GUIHUA_num = 0
        GUIHUA_cpu = 0
        GUIHUA_mem = 0
        GUIHUA_disk = 0
        JIESUAN_num = 0
        JIESUAN_cpu = 0
        JIESUAN_mem = 0
        JIESUAN_disk = 0
        for item in objs:
            if item["zone"] == "BSS-CRM":
                result = getMsg(item)
                results = result.split("_")
                BSS_CRM_cpu += int(results[0])
                BSS_CRM_mem += int(results[1])
                BSS_CRM_disk += int(results[2])
            elif item["zone"] == "BSS-计费":
                result = getMsg(item)
                results = result.split("_")
                BSS_BILL_cpu += int(results[0])
                BSS_BILL_mem += int(results[1])
                BSS_BILL_disk += int(results[2])
            elif item["zone"] == "EDA":
                result = getMsg(item)
                results = result.split("_")
                EDA_cpu += int(results[0])
                EDA_mem += int(results[1])
                EDA_disk += int(results[2])
            elif item["zone"] == "ITM":
                result = getMsg(item)
                results = result.split("_")
                ITM_cpu += int(results[0])
                ITM_mem += int(results[1])
                ITM_disk += int(results[2])
            elif item["zone"] == "MSS":
                result = getMsg(item)
                results = result.split("_")
                MSS_cpu += int(results[0])
                MSS_mem += int(results[1])
                MSS_disk += int(results[2])
            elif item["zone"] == "OSS":
                result = getMsg(item)
                results = result.split("_")
                OSS_cpu += int(results[0])
                OSS_mem += int(results[1])
                OSS_disk += int(results[2])
            elif item["zone"] == "规划":
                result = getMsg(item)
                results = result.split("_")
                GUIHUA_cpu += int(results[0])
                GUIHUA_mem += int(results[1])
                GUIHUA_disk += int(results[2])
            elif item["zone"] == "清结算":
                result = getMsg(item)
                results = result.split("_")
                JIESUAN_cpu += int(results[0])
                JIESUAN_mem += int(results[1])
                JIESUAN_disk += int(results[2])
        for item in objs:
            cpus = item["cpu_total"]
            mem = item["mem_total"]
            disk = item["disk_total"]
            total_cpu += cpus
            total_mem += mem
            total_disk += int(disk)
            if item["zone"] == "BSS-CRM":
                BSS_CRM_num += 1
            elif item["zone"] == "BSS-计费":
                BSS_BILL_num += 1
            elif item["zone"] == "EDA":
                EDA_num += 1
            elif item["zone"] == "ITM":
                ITM_num += 1
            elif item["zone"] == "MSS":
                MSS_num += 1
            elif item["zone"] == "OSS":
                OSS_num += 1
            elif item["zone"] == "规划":
                GUIHUA_num += 1
            elif item["zone"] == "清结算":
                JIESUAN_num += 1
        return JsonResponse({
            "code": 200,
            "data": {
                "total": {
                    "num": total_num,
                    "cpu": total_cpu,
                    "mem": total_mem,
                    "disk": total_disk
                },
                "deps": {
                    "BSS-CRM": {
                        "cpu": BSS_CRM_cpu,
                        "mem": BSS_CRM_mem,
                        "disk": BSS_CRM_disk,
                        "num": BSS_CRM_num
                    },
                    "BSS-计费": {
                        "cpu": BSS_BILL_cpu,
                        "mem": BSS_BILL_mem,
                        "disk": BSS_BILL_disk,
                        "num": BSS_BILL_num
                    },
                    "EDA": {
                        "cpu": EDA_cpu,
                        "mem": EDA_mem,
                        "disk": EDA_disk,
                        "num": EDA_num
                    },
                    "ITM": {
                        "cpu": ITM_cpu,
                        "mem": ITM_mem,
                        "disk": ITM_disk,
                        "num": ITM_num

                    },
                    "MSS": {
                        "cpu": MSS_cpu,
                        "mem": MSS_mem,
                        "disk": MSS_disk,
                        "num": MSS_num

                    },
                    "OSS": {
                        "cpu": OSS_cpu,
                        "mem": OSS_mem,
                        "disk": OSS_disk,
                        "num": OSS_num

                    },
                    "规划": {
                        "cpu": GUIHUA_cpu,
                        "mem": GUIHUA_mem,
                        "disk": GUIHUA_disk,
                        "num": GUIHUA_num

                    },
                    "清结算": {
                        "cpu": JIESUAN_cpu,
                        "mem": JIESUAN_mem,
                        "disk": JIESUAN_disk,
                        "num": JIESUAN_num
                    },

                }
            },
            "msg": "获取数据成功"
        })
