import json
from unicodedata import name
from django.http import JsonResponse
from django.db.models import Count, Q
from assets.models import PlatformHosts, ZoneInfo, IDC, Machine
from assets.serializers import *
from utils import baseview
from utils.auth import auth
from audit.apis.audit import PutAudit
from utils.util import now

class Ph2M(baseview.AnyLogin):
    def post(self, request, args=None):
        q=Q()
        q.children.append(("del_tag",0))
        serializer=PlatformHostsSerializers(PlatformHosts.objects.filter(q),many=True)
        data = serializer.data
        for host in data:
            zone=ZoneInfo.objects.filter(name=host["zone"],del_tag=0).first()
            if not zone:
                ZoneInfo.objects.create(name=host["zone"],description=host["zone"],del_tag=0)
                zone=ZoneInfo.objects.filter(name=host["zone"],del_tag=0).first()
            idc=IDC.objects.filter(name=host["tenant"],zone_id=zone.id,del_tag=0).first()
            if not idc:
                IDC.objects.create(name=host["tenant"],zone_id=zone.id,del_tag=0)
                idc=IDC.objects.filter(name=host["tenant"],zone_id=zone.id,del_tag=0).first()
            sn_id=host["uuid"]
            instance_name=host["hostname"]
            zone_id=zone.id
            idc_id=idc.id
            if host["host_type"] == "虚拟机":
                server_type=2
                status_id=3
            elif host["host_type"] == "云主机":
                server_type=3
                status_id=5
            else:
                server_type=1
                status_id=1
            ip_address=host["host_ip"]
            os_type=host["system_type"]
            username=host["ssh_user"]
            authentication_type=1
            port=host["ssh_port"]
            password=host["ssh_pwd"]
            optional={
                "vpc": host["vpc"],
                "iso": host["iso"],
                "system_disk_size": host["system_disk_size"],
                "cpus": host["cpus"],
                "memery": host["memery"],
                "data_disk_size": host["data_disk_size"],
                "vip": host["vip"],
                "description": host["description"]
            }
            u_time=now()
            machine=Machine.objects.filter(instance_name=instance_name,del_tag=0).first()
            if machine:
                Machine.objects.filter(instance_name=instance_name,del_tag=0).update(del_tag=1)
            Machine.objects.create(
                sn_id=sn_id,
                instance_name=instance_name,
                zone_id=zone_id,
                idc_id=idc_id,
                server_type=server_type,
                status_id=status_id,
                ip_address=ip_address,
                os_type=os_type,
                username=username,
                password=password,
                port=port,
                authentication_type=authentication_type,
                u_time=u_time,
                optional=json.dumps(optional)
            )
            
        return JsonResponse({
            "code": 200,
            "data": {},
            "msg": "同步机器成功"
        })