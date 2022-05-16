from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class AlarmClockView(baseview.BaseView):
    """
    get:
        获取闹钟
    put:
        更新闹钟
    post:
        新增闹钟
    delete:
        删除闹钟
    """
    @auth("tools.alarm.view")
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
            q.children.append(("name__contains", name))
        if start:
            q.children.append(("alarm_time__gt", start))
        if end:
            q.children.append(("alarm_time__lt", end))
        serializer = AlarmClockSerializer(AlarmClock.objects.filter(q).order_by("-alarm_time"),
                                          many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "alarms": data,
                "total": total
            },
            "msg": "获取闹钟成功"
        })

    @auth("tools.alarm.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增闹钟成功"}
        if AlarmClock.objects.filter(name=data["name"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "闹钟已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            data["alarm_time"] = data["alarm_time"].replace("T", " ").split(".")[
                0]
            AlarmClock.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.alarm.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除闹钟成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            AlarmClock.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.alarm.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "闹钟更新成功"}
        needs = {"id", "name", "desc", "alarm_time", "music"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, name, desc, alarm_time, music"}
        else:
            if not AlarmClock.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "闹钟不存在，无法更新"}
            else:
                data["alarm_time"] = data["alarm_time"].replace("T", " ").split(".")[
                    0]
                AlarmClock.objects.filter(id=data["id"]).update(
                    name=data["name"],
                    desc=data["desc"],
                    alarm_time=data["alarm_time"],
                    music=data["music"],
                    created_at=now(),
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)
