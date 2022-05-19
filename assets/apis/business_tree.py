from assets.models import Machine, BusinessEnvironment, BusinessProject, BusinessServices, ServiceToEnv
from assets.serializers import MachineSerializers
from utils import baseview
from django.http import JsonResponse
from utils.auth import auth


def spec_str_format(data: list):  # [1,2] TO ",1,2,"
    str_trans = ","
    for item in data:
        str_trans += str(item) + ","
    return str_trans


def spec_list_format(data: str):  # ",1,2," TO [1,2]
    trans = list(filter(None, data.split(',')))
    return trans


def machine_band_env(machine_id: int, env_id: int):  # 服务器绑定环境ID
    query_env = Machine.objects.filter(id=machine_id).values('env_id')
    str_env_id = query_env[0]['env_id'] if query_env else None
    query_env_id = Machine.objects.filter(id=machine_id,
                                          env_id__contains=",%s," % env_id)
    if not str_env_id:
        u_env_id = "," + str(env_id) + ","
        Machine.objects.filter(id=machine_id).update(env_id=u_env_id)
    elif str_env_id and not query_env_id:
        u_env_id = query_env[0]['env_id'] + str(env_id) + ","
        Machine.objects.filter(id=machine_id).update(env_id=u_env_id)


def business_tree():
    tree_list = []
    env_dict = {}
    query_project = BusinessProject.objects.filter(del_tag=0).values(
        'id', 'name')
    query_env = BusinessEnvironment.objects.filter(del_tag=0).values(
        'id', 'name')
    for env in query_env:
        env_dict.update({env['id']: env['name']})
    for proj_item in query_project:
        srv_list = []
        proj_id = proj_item['id']
        proj_name = proj_item['name']
        if proj_id:
            query_service = BusinessServices.objects.filter(
                del_tag=0, rel_project=proj_id).values('id', 'name')
            for service_item in query_service:
                env_list = []
                query_env = ServiceToEnv.objects.filter(
                    service_id=service_item['id'], del_tag=0).values('env_id')
                env_ids = list(
                    filter(None, [env_id['env_id'] for env_id in query_env]))
                if env_ids:
                    for env_item in env_ids:
                        env_list.append({
                            'id': env_item,
                            'label': env_dict[env_item]
                        })
                srv_list.append({
                    'id': service_item['id'],
                    'label': service_item['name'],
                    'children': env_list
                })
            tree_list.append({
                'id': proj_id,
                'label': proj_name,
                'children': srv_list
            })
    return tree_list


class BusinessTreeListView(baseview.BaseView):
    @auth("projects.tree.view")
    def get(self, request, args=None):
        # 项目
        data = business_tree()
        msg = {'code': 200, 'data': data, 'msg': 'success'}
        return JsonResponse(msg)


class MachineTreeListView(baseview.BaseView):
    @auth("projects.tree.view")
    def get(self, request, args=None):
        tree_list = business_tree()
        service_id_list = []
        machine_id_list = []
        machine_list = []
        if tree_list:
            env_id = int(request.GET.get('env_id')) if request.GET.get(
                'env_id') else None
            service_id = int(request.GET.get('service_id')) if request.GET.get(
                'service_id') else None
            project_id = int(request.GET.get('project_id')) if request.GET.get(
                'project_id') else None
            if not project_id and not service_id and not env_id:  # 初始页
                proj_id = tree_list[0]['id']
                query_service = BusinessServices.objects.filter(
                    del_tag=0, rel_project=int(proj_id)).values('id')
                for service_id in query_service:
                    service_id_list.append(service_id['id'])
            elif project_id and not env_id and not service_id:
                query_service = BusinessServices.objects.filter(
                    del_tag=0, rel_project=int(project_id)).values('id')
                for service_id in query_service:
                    service_id_list.append(service_id['id'])
            elif service_id:
                service_id_list.append(service_id)
            else:
                msg = {'code': 10003, 'data': {}, 'msg': 'service_id参数缺失'}
                return JsonResponse(msg)
        for srv_id in service_id_list:
            if env_id:
                query_machine = ServiceToEnv.objects.filter(del_tag=0,
                                                            service_id=srv_id,
                                                            env_id=env_id)
                if query_machine:
                    if query_machine[0].rel_ips:
                        machine_id_list = spec_list_format(
                            query_machine[0].rel_ips)
            else:
                query_machine = ServiceToEnv.objects.filter(
                    del_tag=0, service_id=srv_id).values('rel_ips')
                for rel_ip in query_machine:
                    if rel_ip['rel_ips']:
                        machine_id_list.extend(
                            spec_list_format(rel_ip['rel_ips']))
        for machine_id in list(set(filter(None, machine_id_list))):
            machine_info = MachineSerializers(Machine.objects.filter(
                id=machine_id, del_tag=0),
                many=True)
            machine_list.extend(machine_info.data)
        msg = {
            'code': 200,
            'data': list(filter(None, machine_list)),
            'msg': 'success'
        }
        return JsonResponse(msg)
