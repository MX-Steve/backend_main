from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class PromoteClockView(baseview.BaseView):
    """
    get:
        获取任务
    put:
        更新任务
    post:
        新增任务
    delete:
        删除任务
    """
    @auth("tools.promote.view")
    def get(self, request, args=None):
        user = User.objects.filter(username=request.user.username).first()
        start = request.GET.get("start", "")
        end = request.GET.get("end", "")
        id = request.GET.get('id', '')
        name = request.GET.get('name', '')
        parent_id = request.GET.get('parent_id', 0)
        op = request.GET.get('op', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(('id', id))
        if op:
            q.children.append(('op', op))
        if parent_id:
            q.children.append(('parent_id', parent_id))
        if name:
            q.children.append(("name__contains", name))
        if start:
            q.children.append(("created_at__gt", start))
        if end:
            q.children.append(("created_at__lt", end))
        q.children.append(("created_by", user))
        q.children.append(("del_tag", 0))
        serializer = PromoteClockSerializer(PromoteClock.objects.filter(q).order_by("-created_at"),
                                          many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "promotes": data,
                "total": total
            },
            "msg": "获取任务成功"
        })

    @auth("tools.promote.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增任务成功"}
        if PromoteClock.objects.filter(name=data["name"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "任务已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            PromoteClock.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.promote.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除任务成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            PromoteClock.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.promote.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "任务更新成功"}
        needs = {"id", "name", "desc", "lv", "finish", "op", "parent_id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, name, desc, lv, finish, op, parent_id"}
        else:
            if not PromoteClock.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "任务不存在，无法更新"}
            else:
                PromoteClock.objects.filter(id=data["id"]).update(
                    name=data["name"],
                    desc=data["desc"],
                    lv=data["lv"],
                    finish=data["finish"],
                    op=data["op"],
                    parent_id=data["parent_id"],
                    created_at=now(),
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)
