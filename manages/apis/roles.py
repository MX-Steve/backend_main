# pylint: disable=wildcard-import,unused-wildcard-import
# pylint: disable=redefined-builtin
from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from manages.serializers import *
from manages.models import *
from users.models import User
from audit.apis.audit import PutAudit


def userCountByRole(role_id):
    count = 0
    users = User.objects.all()
    for user in users:
        page_perms_ids = user.roles.strip('[').strip(']').split(',')
        if str(role_id) in page_perms_ids:
            count += 1
    return count


class RoleView(baseview.BaseView):
    """
    get:
        获取角色
    put:
        更新角色
    post:
        新增角色
    delete:
        删除角色
    """
    @auth("manages.role.view|personal.user_center.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        name = request.GET.get('name', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        if id != "":
            serializer = RoleSerializer(Role.objects.filter(id=id, del_tag=0),
                                        many=True)
        elif name != "":
            serializer = RoleSerializer(Role.objects.filter(
                name__contains=name, del_tag=0),
                                        many=True)
        else:
            serializer = RoleSerializer(Role.objects.filter(del_tag=0),
                                        many=True)
        data = []
        total = len(serializer.data)
        for item in serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]:
            count = userCountByRole(item['id'])
            item["count"] = count
            data.append(item)
        return JsonResponse({
            "code": 200,
            "data": {
                "roles": data,
                "total": total
            },
            "msg": "获取角色成功"
        })

    @auth("manages.role.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增角色成功"}
        if Role.objects.filter(name=data["name"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "角色已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            if Role.objects.filter(name=data["name"]).exists():
                Role.objects.filter(name=data["name"]).update(
                    desc=data["desc"], del_tag=0)
            else:
                Role.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("manages.role.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除角色成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            Role.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("manages.role.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "角色更新成功"}
        needs = {"id", "name", "desc"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id, name, desc"}
        else:
            if not Role.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "角色不存在，无法更新"}
            else:
                Role.objects.filter(id=data["id"]).update(
                    name=data["name"],
                    desc=data["desc"],
                    page_perms=data["page_perms"],
                    created_at=now(),
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)
