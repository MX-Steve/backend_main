from django.http import JsonResponse
from utils import baseview
from assets.models import Machine, IDC, DeviceStatus, DeviceType, BusinessProject, BusinessServices
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
