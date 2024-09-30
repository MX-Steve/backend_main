from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class JobsProcessView(baseview.BaseView):
    """
    get:
        获取流程
    put:
        更新流程
    post:
        新增流程
    delete:
        删除流程
    """
    @auth("jobs.process.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        name = request.GET.get('name', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = request.GET.get("start", "")
        end = request.GET.get("end", "")
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(('id', id))
        if name:
            q.children.append(("name", name))
        if start:
            q.children.append(("created_at__gt", start))
        if end:
            q.children.append(("created_at__lt", end))
        serializer = JobsProcessSerializer(JobsProcess.objects.filter(q).order_by("-created_at"),
                                           many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "process": data,
                "total": total
            },
            "msg": "获取流程成功"
        })

    @auth("jobs.process.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增流程成功"}
        if JobsProcess.objects.filter(name=data["name"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "流程已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            data["created_at"] = data["created_at"].replace("T", " ").split(".")[
                0]
            JobsProcess.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.process.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除流程成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            JobsProcess.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.process.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "流程更新成功"}
        needs = {"id", "name", "description", "created_at", "ip_file", "ws_server"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, name, description, created_at, ip_file, ws_server"}
        else:
            if not JobsProcess.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "流程不存在，无法更新"}
            else:
                data["created_at"] = data["created_at"].replace("T", " ").split(".")[
                    0]
                JobsProcess.objects.filter(id=data["id"]).update(
                    name=data["name"],
                    description=data["description"],
                    scripts=data["scripts"],
                    created_at=now(),
                    ip_file=data["ip_file"],
                    ws_server=data["ws_server"],
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)


class JobsProcessHistoryView(baseview.BaseView):
    """
    post:
        新增流程历史
    """
    @auth("jobs.phistory.add")
    def post(self, request, args=None):
        data = request.data
        res0 = data["res"]
        res = {"code": 200, "data": {}, "msg": "新增流程历史记录成功"}
        PutAudit(request, res0)
        return JsonResponse(res)
