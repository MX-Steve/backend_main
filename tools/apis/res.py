from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class ResChangeView(baseview.BaseView):
    """
    get:
        获取变更信息
    put:
        更新变更信息
    post:
        新增变更信息
    delete:
        删除变更信息
    """
    @auth("tools.reschange.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        IP = request.GET.get('IP', '')
        DEP = request.GET.get('DEP', '')
        OP = request.GET.get('OP', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = request.GET.get("start", "")
        end = request.GET.get("end", "")
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(('id', id))
        if DEP:
            q.children.append(('DEP', DEP))
        if OP:
            q.children.append(('OP', OP))
        if IP:
            q.children.append(("IP__contains", IP))
        if start:
            q.children.append(("created_at__gt", start))
        if end:
            q.children.append(("created_at__lt", end))
        serializer = ResChangeSerializer(ResChange.objects.filter(q).order_by("-created_at"),
                                           many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "res": data,
                "total": total
            },
            "msg": "获取变更信息成功"
        })

    @auth("tools.reschange.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增变更信息成功"}
        if ResChange.objects.filter(IP=data["IP"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "变更信息已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            data["created_at"] = data["created_at"].replace("T", " ").split(".")[
                0]
            ResChange.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.reschange.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除变更信息成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            ResChange.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.reschange.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "变更信息更新成功"}
        needs = {"id", "OP", "DEP", "BCPU", "BMEM", "BDSIZE", "ACPU", "AMEM", "ADSIZE", "created_at"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, OP,DEP, BCPU, BMEM, BDSIZE, ACPU,AMEM, ADSIZE, created_at"}
        else:
            if not ResChange.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "流程不存在，无法更新"}
            else:
                data["created_at"] = data["created_at"].replace("T", " ").split(".")[
                    0]
                ResChange.objects.filter(id=data["id"]).update(
                    IP=data["IP"],
                    OP=data["OP"],
                    DEP=data["DEP"],
                    BCPU=data["BCPU"],
                    BMEM=data["BMEM"],
                    BDSIZE=data["BDSIZE"],
                    ACPU=data["ACPU"],
                    AMEM=data["AMEM"],
                    ADSIZE=data["ADSIZE"],
                    created_at=now(),
                    created_by=request.user,
                    del_tag=0)
        PutAudit(request, res)
        return JsonResponse(res)
