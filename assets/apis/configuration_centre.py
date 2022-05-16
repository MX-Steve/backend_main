from django.http import JsonResponse
from utils import baseview
from assets.models import BusinessServices, BusinessEnvironment, BusinessProject, ServiceToEnv
from assets.serializers import EnvironmentSerializers, ServicesSerializers, ProjectSerializers
from utils.util import now
from audit.apis.audit import PutAudit
from utils.auth import auth
from django.db.models import Count, Q


def spec_str_format(data: list):  # [1,2] TO ",1,2,"
    str_trans = ","
    for item in data:
        str_trans += str(item) + ","
    return str_trans


def spec_list_format(data: str):  # ",1,2," TO [1,2]
    trans = [int(item) for item in list(filter(None, data.split(',')))]
    return trans


def service_band_env_machine(machine_ids: list, env_id: int,
                             service_id: int):  # 服务器绑定环境ID
    machine_ids_str = ''
    if machine_ids:
        machine_ids_str = spec_str_format(machine_ids)
    query_service = ServiceToEnv.objects.filter(env_id=env_id,
                                                service_id=service_id)
    if not query_service:
        ServiceToEnv.objects.create(env_id=env_id,
                                    service_id=service_id,
                                    rel_ips=machine_ids_str,
                                    c_time=now(),
                                    u_time=now())
    else:
        query_service.update(rel_ips=machine_ids_str, u_time=now(), del_tag=0)


class EnvironmentListView(baseview.BaseView):
    @auth("projects.edit.view")
    def get(self, request, args=None):
        serializer = EnvironmentSerializers(
            BusinessEnvironment.objects.filter(del_tag=0), many=True)
        msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
        return JsonResponse(msg)

    @auth("projects.edit.add")
    def post(self, request, args=None):
        data = request.data
        name = data['name'].strip() if data.get('name', None) else None
        if not name:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "name required."
            })
        query_env = BusinessEnvironment.objects.filter(name=name, del_tag=0)
        data.pop("id")
        data["c_time"] = now()
        data["u_time"] = now()
        if not query_env:
            BusinessEnvironment.objects.create(**data)
            msg = {'code': 200, 'data': {}, 'msg': '新增环境成功'}
        else:
            msg = {'code': 10005, 'data': {}, 'msg': '环境名已存在，请勿重复添加'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.edit")
    def put(self, request, args=None):
        data = request.data
        if "id" not in data:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id required."
            })
        id = data.get('id')
        data_name = data['name'].strip()
        data['u_time'] = now()
        query_env = BusinessEnvironment.objects.filter(del_tag=0, id=id)
        if query_env:
            query_env_name = BusinessEnvironment.objects.filter(del_tag=0,
                                                                name=data_name)
            env_id = query_env_name[0].id if query_env_name else None
            if not env_id:
                query_env.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '环境信息修改成功'}
            elif env_id == id:
                query_env.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '环境信息修改成功'}
            else:
                msg = {'code': 10002, 'data': {}, 'msg': '环境名称已存在，请勿重复添加'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未找到此环境信息'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.del")
    def delete(self, request, args=None):
        data = request.data
        id = data.get('id', None)
        if not id:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id required."
            })
        query_env = BusinessEnvironment.objects.filter(del_tag=0, id=int(id))
        if query_env:
            query_rel = ServiceToEnv.objects.filter(
                del_tag=0, env_id=id).values('service_id')
            query_service = list(
                filter(None, [item['service_id'] for item in query_rel]))
            if query_service:
                msg = {'code': 10004, 'data': {}, 'msg': '此环境已绑项目，请先解绑'}
            else:
                query_env.update(del_tag=1)
                msg = {'code': 200, 'data': {}, 'msg': '环境信息删除成功'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未找到此环境信息,删除失败'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)


class ProjectListView(baseview.BaseView):
    @auth("projects.edit.view")
    def get(self, request, args=None):
        q = Q()
        q.children.append(("del_tag", 0))
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        query_projects = BusinessProject.objects.filter(q)
        total = query_projects.count()
        start = (pageNo - 1) * pageSize
        end = pageNo * pageSize
        serializer = ProjectSerializers(query_projects[start:end], many=True)
        msg = {
            'code': 200,
            'data': {
                'project_infos': serializer.data,
                'total': total
            },
            'msg': 'success'
        }
        return JsonResponse(msg)

    @auth("projects.edit.add")
    def post(self, request, args=None):
        data = request.data
        name = data['name'].strip() if data.get('name', None) else None
        if not name:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "name required."
            })
        if data['manager']:
            data['manager'] = spec_str_format(data['manager'])
        query_proj = BusinessProject.objects.filter(name=name, del_tag=0)
        data.pop("id")
        data["c_time"] = now()
        data["u_time"] = now()
        if not query_proj:
            BusinessProject.objects.create(**data)
            msg = {'code': 200, 'data': {}, 'msg': '新增项目成功'}
        else:
            msg = {'code': 10002, 'data': {}, 'msg': '项目名已存在,请勿重复添加'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.edit")
    def put(self, request, args=None):
        data = request.data
        id = data.get('id', None)
        name = data.get('name', None)
        if not all([id, name]):
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id&name required."
            })
        if data['manager']:
            data['manager'] = spec_str_format(data['manager'])
        data["u_time"] = now()
        query_proj = BusinessProject.objects.filter(del_tag=0, id=int(id))
        if query_proj:
            query_proj_id = BusinessProject.objects.filter(name=name.strip(),
                                                           del_tag=0)
            proj_id = query_proj_id[0].id if query_proj_id else None
            if not proj_id:
                query_proj.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '项目更新成功'}
            elif proj_id == int(id):
                query_proj.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '项目更新成功'}
            else:
                msg = {'code': 10002, 'data': {}, 'msg': '项目名已存在,请勿重复添加'}
        else:
            msg = {'code': 10002, 'data': {}, 'msg': '未找到相关项目信息'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.del")
    def delete(self, request, args=None):
        data = request.data
        id = data.get('id', None)
        if not id:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id required."
            })
        query_proj = BusinessProject.objects.filter(del_tag=0, id=int(id))
        if query_proj:
            query_service = BusinessServices.objects.filter(
                del_tag=0, rel_project=int(id))
            if not query_service:
                query_proj.update(del_tag=1)
                msg = {'code': 200, 'data': {}, 'msg': '项目删除成功'}
            else:
                msg = {'code': 10004, 'data': {}, 'msg': '此项目已绑定服务,请先解绑'}
        else:
            msg = {'code': 10002, 'data': {}, 'msg': '未找到相关项目信息,删除失败'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)


class ServiceListView(baseview.BaseView):
    @auth("projects.edit.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type', None)
        if op_type == "get_machine_env":
            srv_id = request.GET.get('id', None)
            if not srv_id:
                msg = {'code': 10003, 'data': {}, 'msg': 'id required'}
                return JsonResponse(msg)
            else:
                srv_id = int(srv_id)
            query_env = ServiceToEnv.objects.filter(
                del_tag=0, service_id=srv_id).values('env_id')
            query_env_ids = list(
                filter(None, [env_id['env_id'] for env_id in query_env]))
            env_to_machine_list = []
            if query_env_ids:
                for env_item in query_env_ids:
                    query_machine = ServiceToEnv.objects.filter(
                        del_tag=0, service_id=srv_id,
                        env_id=env_item).values('rel_ips')
                    if query_machine[0]['rel_ips']:
                        machine_ids_str = query_machine[0]['rel_ips']
                        machine_ids_list = spec_list_format(machine_ids_str)
                        env_to_machine_list.append({
                            'env_id':
                            env_item,
                            'machine_id':
                            machine_ids_list
                        })
            msg = {'code': 200, 'data': env_to_machine_list, 'msg': 'success'}
        else:
            q = Q()
            q.children.append(("del_tag", 0))
            service_type = request.GET.get('service_type', None)
            project = request.GET.get('project', None)
            if service_type:
                for i in BusinessServices.type_choices:
                    if i[1] == service_type:
                        service_type = i[0]
                        break
                q.children.append(("service_type", service_type))
            if project:
                p = BusinessProject.objects.filter(name=project).first()
                q.children.append(("rel_project", p.id))
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            query_services = BusinessServices.objects.filter(q)
            total = query_services.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            serializer = ServicesSerializers(query_services[start:end],
                                             many=True)
            msg = {
                'code': 200,
                'data': {
                    'service_infos': serializer.data,
                    'total': total
                },
                'msg': 'success'
            }
        return JsonResponse(msg)

    @auth("projects.edit.add")
    def post(self, request, args=None):
        data = request.data
        name = data.get('name', None)
        env_machines = data.get('env_machines', None)
        data.pop('env_machines')
        data.pop("env_id")
        data.pop("rel_machine")
        rel_project = data.get('rel_project')
        service_type = data.get('service_type')
        # 处理choices映射
        type_choices = BusinessServices.type_choices
        for item in type_choices:
            if item[1] == service_type:
                service_type = item[0]
                break
        if not name:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "name required."
            })
        if data['manager']:
            data['manager'] = spec_str_format(data['manager'])
        query_service = BusinessServices.objects.filter(
            name=name.strip(),
            del_tag=0,
            rel_project=rel_project,
            service_type=service_type)
        if not query_service:
            data.pop('id')
            data["c_time"] = now()
            data["u_time"] = now()
            data["service_type"] = service_type
            BusinessServices.objects.create(**data)
            srv_id = BusinessServices.objects.filter(name=name.strip(),
                                                     del_tag=0)[0].id
            for i in env_machines:
                env_id = i['env_id']
                if srv_id and env_id:
                    service_band_env_machine(service_id=int(srv_id),
                                             env_id=int(env_id),
                                             machine_ids=i['machine_id'])
            msg = {'code': 200, 'data': {}, 'msg': '服务新增成功'}
        else:
            msg = {'code': 10002, 'data': {}, 'msg': '服务名已存在,请勿重复添加'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.edit")
    def put(self, request, args=None):
        data = request.data
        name = data.get('name', None)
        id = data.get('id', None)
        env_machines = data.get('env_machines')
        data.pop('env_machines')
        rel_project = data.get('rel_project', None)
        # 处理choices映射
        service_type = data.get('service_type', None)
        if service_type:
            for i in BusinessServices.type_choices:
                if i[1] == service_type:
                    service_type = i[0]
                    break
        data['service_type'] = service_type
        if not all([name, id]):
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id & name required."
            })
        if data['manager']:
            data['manager'] = spec_str_format(data['manager'])
        data["u_time"] = now()
        query_service = BusinessServices.objects.filter(del_tag=0, id=int(id))
        if query_service:
            query_service_id = BusinessServices.objects.filter(
                del_tag=0,
                name=name.strip(),
                rel_project=rel_project,
                service_type=service_type)
            service_id = query_service_id[0].id if query_service_id else None
            if not service_id or service_id == int(id):
                data.pop("env_id")
                data.pop("rel_machine")
                query_service.update(**data)
                # 环境与机器落库
                for item in env_machines:
                    env_id = item['env_id']
                    if env_id:
                        service_band_env_machine(service_id=int(id),
                                                 env_id=int(env_id),
                                                 machine_ids=item["machine_id"])
                msg = {'code': 200, 'data': {}, 'msg': '服务更新成功'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '服务名已存在,请勿重复添加'}
        else:
            msg = {'code': 200, 'data': {}, 'msg': '未找到相关项目信息,更新失败'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("projects.edit.del")
    def delete(self, request, args=None):
        data = request.data
        id = data.get('id', None)
        if not id:
            return JsonResponse({
                "code": 10003,
                "data": {},
                "msg": "id required."
            })
        query_service = BusinessServices.objects.filter(del_tag=0, id=int(id))
        if query_service:
            query_machine = ServiceToEnv.objects.filter(
                del_tag=0, service_id=int(id)).values('rel_ips')
            machine_ids = list(
                filter(None,
                       [rel_ips['rel_ips'] for rel_ips in query_machine]))
            if machine_ids:
                msg = {'code': 10004, 'data': {}, 'msg': '此服务已绑定服务器,请先解绑'}
            else:
                query_service.update(del_tag=1)
                ServiceToEnv.objects.filter(del_tag=0,
                                            service_id=int(id)).update(
                                                del_tag=1)  # 删除服务,删除关系
                msg = {'code': 200, 'data': {}, 'msg': '服务删除成功'}
        else:
            msg = {'code': 10002, 'data': {}, 'msg': '未找到相关服务信息,删除失败'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)
