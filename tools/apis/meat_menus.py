from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class MeatMenusView(baseview.BaseView):
    """
    get:
        获取食谱
    put:
        更新食谱
    post:
        新增食谱
    delete:
        删除食谱
    """
    @auth("tools.meat-menus.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        type = request.GET.get('type', '')
        content = request.GET.get('content', '')
        meat_day = request.GET.get('meat_day', '')
        meat_date = request.GET.get('meat_date', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = request.GET.get("start", "")
        end = request.GET.get("end", "")
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(('id', id))
        if type:
            q.children.append(("type", type))
        if content:
            q.children.append(("content__contains", content))
        if meat_day:
            q.children.append(("meat_day", meat_day))
        if meat_date:
            q.children.append(("meat_date", meat_date))
        if start:
            q.children.append(("meat_date__gt", start))
        if end:
            q.children.append(("meat_date__lt", end))
        serializer = MeatMenusSerializer(MeatMenus.objects.filter(q).order_by("-meat_date"),
                                         many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "menus": data,
                "total": total
            },
            "msg": "获取食谱成功"
        })

    @auth("tools.meat-menus.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增食谱成功"}
        if MeatMenus.objects.filter(meat_date=data["meat_date"], type=data["type"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "食谱已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            MeatMenus.objects.create(created_by=user, created_at=now(), **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.meat-menus.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除食谱成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            MeatMenus.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.meat-menus.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "食谱更新成功"}
        needs = {"id", "content", "type", "meat_day", "meat_date"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, content, type, meat_day, meat_date"}
        else:
            if not MeatMenus.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "食谱不存在，无法更新"}
            else:
                MeatMenus.objects.filter(id=data["id"]).update(
                    content=data["content"],
                    type=data["type"],
                    meat_day=data["meat_day"],
                    meat_date=data["meat_date"],
                    created_at=now(),
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)
