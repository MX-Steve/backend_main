import os
import sys
import json
import logging
import paramiko
from django.http import JsonResponse
from django.db.models import Count, Q
from django.conf import settings
from assets import models
from assets.serializers import *
from audit.apis.audit import PutAudit
from utils import baseview
from utils.util import now, time_trans, gen_shortuuid, LinuxRemoteConn
from utils.auth import auth
# from utils.cloudflare import CloudFlareApi

logger = logging.getLogger("ttool.app")

class MachineListView(baseview.BaseView):
    @auth("assets.machine-list.view")
    def get(self, request, args=None):
        """

        :param request:  idc_id,id_address,server_type,status_id
        :param args:
        :return:
        """
        res_type = request.GET.get('type')
        if res_type == "get_all_machines":
            idc_id = int(request.GET.get('idc_id')) if request.GET.get(
                'idc_id') else None
            ip_address = request.GET.get('ip_address')
            MgrIp = request.GET.get("MgrIp")
            manager = request.GET.get("manager")
            cabinet = request.GET.get("cabinet")
            server_type = request.GET.get('server_type')
            status_id = request.GET.get('status_id')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if idc_id:
                q.children.append(('idc_id', idc_id))
            if ip_address:
                q.children.append(('ip_address__contains', ip_address))
            if server_type:
                q.children.append(('server_type', server_type))
            if status_id:
                q.children.append(('status_id', status_id))
            if cabinet:
                obj = '"cabinet": "%s"'%(cabinet)
                q.children.append(("optional__contains", obj))
            if MgrIp:
                obj = '"MgrIp": "%s"'%(MgrIp)
                q.children.append(("optional__contains", obj))
            if manager:
                obj = '"manager": "%s"'%(manager)
                q.children.append(("optional__contains", obj))
            machine_infos = models.Machine.objects.filter(q)
            total = machine_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize

            machine_show_infos = machine_infos[start:end].values(
                'id', 'sn_id', 'zone_id', 'instance_name', 'idc_id',
                'status_id', 'server_type', 'ip_address', 'os_type',
                'username', 'authentication_type', 'port', 'password',
                'sudo_password', 'optional', 'u_time')
            data = []
            for item in machine_show_infos:
                data.append({
                    'id': item['id'],
                    'sn_id': item['sn_id'],
                    'zone_id': item['zone_id'],
                    'idc_id': item['idc_id'],
                    'instance_name': item['instance_name'],
                    'ip_address': item['ip_address'],
                    'status_id': item['status_id'],
                    'server_type': item['server_type'],
                    'os_type': item['os_type'],
                    'username': item['username'],
                    'authentication_type': item['authentication_type'],
                    'port': item['port'],
                    'password': item['password'],
                    'sudo_password': item['sudo_password'],
                    'optional': item['optional'],
                    'u_time': item['u_time']
                })
            msg = {
                'code': 200,
                'data': {
                    'machines': data,
                    "total": total
                },
                'msg': 'success'
            }

        elif res_type == "machine_details":
            id = request.GET.get('id')
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_machine_detail = models.Machine.objects.filter(id=id, del_tag=0)
            if query_machine_detail:
                serializer = MachineSerializers(query_machine_detail,
                                                many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': '未查询到此ID:%s相关服务器' % id
                }
        elif res_type == "ins_details":
            ins_id = request.GET.get('instance_id', None)
            if not ins_id:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': 'instance id required'
                }
                return JsonResponse(msg)
            else:
                query_machine = models.Machine.objects.filter(
                    del_tag=0, server_type=2).values('id', 'optional')  # 查询云盘
                msg = {'code': 200, 'data': [], 'msg': 'success'}
                if query_machine:
                    for ins in query_machine:
                        if json.loads(
                                ins['optional'])['instance_id'] == ins_id:
                            ins_info = MachineSerializers(
                                models.Machine.objects.filter(id=ins['id']),
                                many=True)
                            msg['data'] = ins_info.data
                            break
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.machine-list.add|assets.machine-input.add")
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "获取成功"}
        data = request.data
        op_type = data.get('type')
        if op_type == 'machine_add':
            post_query_machine = models.Machine.objects.filter(
                instance_name=data["instance_name"], del_tag=0)
            data.pop('type')
            if not post_query_machine:
                models.Machine.objects.create(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息添加成功！'}
                PutAudit(request, msg)  # 审计
            else:
                msg = {'code': 10001, 'data': {}, 'msg': '服务器名称已存在，请勿重复添加！'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': 'op_type参数有误'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("assets.machine-list.edit")
    def put(self, request, args=None):
        data = request.data
        id = int(data['id'])
        instance_name = data['instance_name']
        optional = data.get('optional', None)
        if optional:
            data['optional'] = json.dumps(optional)
        put_query_machine = models.Machine.objects.filter(id=id, del_tag=0)
        if put_query_machine:
            data['u_time'] = now()
            query_machine_id = models.Machine.objects.filter(
                instance_name=instance_name, del_tag=0)
            machine_id = query_machine_id[0].id if query_machine_id else None
            if not machine_id:
                put_query_machine.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息修改成功'}
            elif machine_id == id:
                put_query_machine.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息修改成功'}
            else:
                msg = {'code': 10002, 'data': {}, 'msg': '服务器名称已存在，请勿重复添加！'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未查询到服务器ID,请联系相关运维！'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("assets.machine-list.del")
    def delete(self, request, args=None):
        data = request.data
        if "id" not in data:
            return JsonResponse({
                'code': 10003,
                'data': {},
                'msg': "id required."
            })
        not_found_machine = []
        bind_service = []
        have_virts = []
        ids = data['id']  # list
        for m_id in ids:
            query_virt = models.Machine.objects.filter(del_tag=0,
                                                rel_server_id=m_id).exists()
            if query_virt:
                have_virts.append(m_id)
        if have_virts:
            msg = {
                'code': 10003,
                'data': {},
                'msg': "ID为%s的服务器有虚拟机,请先删除虚拟机" % have_virts
            }
            PutAudit(request, msg)  # 审计
            return JsonResponse(msg)
        for item in ids:
            query_machine = models.Machine.objects.filter(id=item, del_tag=0)
            if query_machine:
                query_rel = models.ServiceToEnv.objects.filter(
                    rel_ips__contains=',' + str(item) + ',')
                if query_rel:
                    bind_service.append(item)
                else:
                    query_machine.update(del_tag=1)
            else:
                not_found_machine.append(item)
        msg1, msg2 = '', ''
        if not_found_machine:
            msg1 = 'ID为%s不存在，删除失败\n' % not_found_machine
        if bind_service:
            msg2 = 'ID为%s已绑定服务，请先解绑' % bind_service
        t_msg = msg1 + msg2
        if t_msg:
            msg = {'code': 10003, 'data': {}, 'msg': t_msg}
        else:
            msg = {'code': 200, 'data': {}, 'msg': '删除成功'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)


