import logging
import os
import sys
from django.http import JsonResponse
from assets.models import  IDC
from assets import models
from assets.serializers import *
from utils import baseview
from audit.apis.audit import PutAudit
from utils.auth import auth

logger = logging.getLogger("ttool.app")


class IDCView(baseview.BaseView):
    """
    机房信息
    """
    auth("assets.idc-input.view")

    def get(self, request, args=None):
        res_type = request.GET.get('type')
        if res_type == 'get_all_idcs':
            serializer = IDCSerializers(IDC.objects.filter(del_tag=0),
                                        many=True)
            msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
        elif res_type == 'idc_details':
            zone_id = request.GET.get('zone_id')
            if zone_id:
                serializer = IDCSerializers(IDC.objects.filter(
                    zone_id=zone_id, del_tag=0).values('id', 'name'),
                    many=True)
            else:
                serializer = IDCSerializers(IDC.objects.filter(del_tag=0),
                                            many=True)
            msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
        elif res_type == 'query_idc':
            zone_id = request.GET.get('zone_id')
            if not zone_id:
                msg = {'code': 10003, 'data': {}, 'msg': 'zone_id required'}
                return JsonResponse(msg)
            query_idc_name = models.IDC.objects.filter(
                del_tag=0, zone_id=zone_id)
            idc_names = []
            if query_idc_name:
                for item in query_idc_name:
                    idc_names.append({'name': item.name})
            msg = {'code': 200, 'data': idc_names, 'msg': 'success'}
        else:
            msg = {'code': 10005, 'data': {}, 'msg': '目前不支持此type'}
        return JsonResponse(msg)

    auth("assets.idc-input.add")

    def post(self, request, args=None):
        '''
        机房信息页面录入
        '''
        data = request.data
        try:
            zone_id = data.get('zone_id')  # 区域
            idc_name = data.get('name')  # 机房名称
            provider = data.get('provider')
            if zone_id and idc_name and provider:
                idc_info = IDC.objects.filter(zone_id=zone_id,
                                              name=idc_name,
                                              provider=provider,
                                              del_tag=0).exists()
                if not idc_info:
                    IDC.objects.create(**data)
                    msg = {'code': 200, 'data': {}, 'msg': '创建机房成功!'}
                else:
                    msg = {'code': 10001, 'data': {}, 'msg': '机房信息已存在，请勿重复添加！'}
            else:
                msg = {'code': 10002, 'data': {}, 'msg': '请检查必填参数！'}
            PutAudit(request, msg)  # 审计
            return JsonResponse(msg)
        except:
            err = '%s [%s] happend on %s line at %s' % (
                sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

    auth("assets.basic.edit")

    def put(self, request, args=None):
        data = request.data
        if "id" not in data:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id required."
            })
        try:
            id = data['id']
            idc_name = data.get('name').strip()  # 机房名称
            idc = IDC.objects.filter(id=id, del_tag=0)
            if idc:
                query_idc_id = IDC.objects.filter(name=idc_name, del_tag=0)
                idc_id = query_idc_id[0].id if query_idc_id else None
                if not idc_id:
                    idc.update(**data)
                    msg = {'code': 200, 'data': {}, 'msg': '机房信息修改成功'}
                elif idc_id == id:
                    idc.update(**data)
                    msg = {'code': 200, 'data': {}, 'msg': '机房信息修改成功'}
                else:
                    msg = {'code': 10002, 'data': {}, 'msg': '机房名称已存在，请勿重复添加！'}
            else:
                msg = {'code': 1003, 'data': {}, 'msg': '未查询到机房信息,请联系相关运维！'}
            PutAudit(request, msg)  # 审计
            return JsonResponse(msg)
        except:
            err = '%s [%s] happend on %s line at %s' % (
                sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

    auth("assets.basic.del")

    def delete(self, request, args=None):
        data = request.data
        if "id" not in data:
            return JsonResponse({
                'code': 404,
                'data': {},
                'msg': "id required."
            })
        not_found_idc = []
        id = data['id']
        del_idc = IDC.objects.filter(id=id, del_tag=0)
        if del_idc:
            del_idc.update(del_tag=1)
        else:
            not_found_idc.append(id)
        if not_found_idc:
            msg = {
                'code': '10003',
                'data': {},
                'msg': '%s不存在，删除失败' % not_found_idc
            }
        else:
            msg = {'code': 200, 'data': {}, 'msg': '删除成功'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)
