from django.http import JsonResponse
from django.db.models import Count, Q
from utils import baseview
from chat.models import *
from chat.serializers import *
from chat.utils import restart_beat
from utils.util import now
from audit.apis.audit import PutAudit
from utils.auth import auth


class CeleryBeatView(baseview.BaseView):
    @auth("jobs.list.edit")
    def put(self, request, args=None):
        code, out = restart_beat()
        res = {"code": 200, "data": {}, "msg": "beat重启成功"}
        if code != 0:
            res = {"code": 500, "data": {}, "msg": "beat重启失败"}
        PutAudit(request, res)
        return JsonResponse(res)


class IntervalScheduleView(baseview.BaseView):
    """[interval schedule view]
    get: 
        获取所有周期时间
    """
    @auth("jobs.list.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        if id != "":
            serializer = IntervalScheduleSerializers(
                IntervalSchedule.objects.filter(id=id), many=True)
        else:
            serializer = IntervalScheduleSerializers(
                IntervalSchedule.objects.all(), many=True)
        data = serializer.data
        for item in data:
            item["table"] = "interval"
        return JsonResponse({"code": 200, "data": data, "msg": "获取所有周期时间"})

    @auth("jobs.list.add")
    def post(self, request, args=None):
        data = request.data
        IntervalSchedule.objects.create(every=int(data["every"]),
                                        period="seconds",
                                        creater=request.user.username)
        res = {"code": 200, "data": {}, "msg": "新增周期时间成功"}
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.list.edit")
    def put(self, request, args=None):
        data = request.data
        IntervalSchedule.objects.filter(id=int(data["id"])).update(**data)
        res = {"code": 200, "data": {}, "msg": "更新周期时间成功"}
        PutAudit(request, res)
        return JsonResponse(res)


class PeriodicTaskView(baseview.BaseView):
    @auth("jobs.list.view")
    def get(self, request, args=None):
        q = Q()
        id = request.GET.get("id", "")
        page_no = int(request.GET.get("page_no", 1))
        page_size = int(request.GET.get("page_size", 10))
        enabled = request.GET.get("enabled", "")
        interval_id = request.GET.get("interval_id", "")
        name = request.GET.get("name", "")
        crontab_id = request.GET.get("crontab_id", "")
        if id != "":
            serializer = PeriodicTaskSerializers(
                PeriodicTask.objects.filter(id=id), many=True)
        else:
            if enabled:
                q.children.append(("enabled", int(enabled)))
            if interval_id:
                q.children.append(("interval_id", int(interval_id)))
            if name:
                q.children.append(("name__contains", name))
            if crontab_id:
                q.children.append(("crontab_id", int(crontab_id)))
            serializer = PeriodicTaskSerializers(
                PeriodicTask.objects.filter(q), many=True)
        total = len(serializer.data)
        data = serializer.data[(page_no - 1) * page_size:page_size * page_no]
        return JsonResponse({
            "code": 200,
            "data": {
                "tasks": data,
                "total": total
            },
            "msg": "任务列表获取成功"
        })

    @auth("jobs.list.add")
    def post(self, request, args=None):
        data = request.data
        if "id" in data:
            data.pop("id")
        data["last_run_at"] = now()
        data["date_changed"] = now()
        if "type_id" in data:
            data.pop("type_id")
        PeriodicTask.objects.create(creater=request.user.username, **data)
        res = {"code": 200, "data": [], "msg": "新增任务成功"}
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.list.edit")
    def put(self, request, args=None):
        data = request.data
        if "type_id" in data:
            data.pop("type_id")
        needs = {"type", "id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要参数不对."}
            PutAudit(request, res)
            return JsonResponse(res)
        type = data["type"]
        if type == "enabled":
            PeriodicTask.objects.filter(id=int(data["id"])).update(
                enabled=int(data["enabled"]), updater=request.user.username)
            # code, out = restart_beat()
            res = {"code": 200, "data": {}, "msg": "开关更新成功"}
            # if code != 0:
            #     res = {"code": 500, "data": {}, "msg": "beat重启失败"}
            PutAudit(request, res)
            return JsonResponse(res)
        if type == "one_off":
            PeriodicTask.objects.filter(id=int(data["id"])).update(
                one_off=int(data["one_off"]), updater=request.user.username)
            # code, out = restart_beat()
            res = {"code": 200, "data": {}, "msg": "一次性任务更新成功"}
            # if code != 0:
            #     res = {"code": 500, "data": {}, "msg": "beat重启失败"}
            PutAudit(request, res)
            return JsonResponse(res)
        if type == "modify":
            data.pop("type")
            if data["interval_id"] == "":
                data["interval_id"] = None
            if data["crontab_id"] == "":
                data["crontab_id"] = None
            if data["updater"] == "":
                data["updater"] = request.user.username
            PeriodicTask.objects.filter(id=int(data["id"])).update(**data)
            # code, out = restart_beat()
            res = {"code": 200, "data": [], "msg": "更新任务成功"}
            # if code != 0:
            #     res = {"code": 500, "data": {}, "msg": "beat重启失败"}
            PutAudit(request, res)
            return JsonResponse(res)
        res = {"code": 10003, "data": [], "msg": "type 值不对"}
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.list.del")
    def delete(self, request, args=None):
        data = request.data
        needs = {"id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要参数不对."}
        else:
            PeriodicTask.objects.filter(id=int(data["id"])).delete()
            res = {"code": 200, "data": {}, "msg": "删除任务成功"}
        return JsonResponse(res)


class ResultsTasksView(baseview.BaseView):
    @auth("jobs.list.view")
    def get(self, request, args=None):
        id = request.GET.get("id", "")
        task_name = request.GET.get("task_name", "")
        if id != "":
            serializer = ResultsTasksSerializers(
                ResultsTasks.objects.filter(id=id), many=True)
        else:
            q = Q()
            if task_name:
                q.children.append(("task_name", task_name))
            print(q)
            serializer = ResultsTasksSerializers(
                ResultsTasks.objects.filter(q).order_by("-date_created"),
                many=True)
        return JsonResponse({
            "code": 200,
            "data": serializer.data[0:50],
            "msg": "任务运行结果获取成功"
        })


class CrontabScheduleView(baseview.BaseView):
    @auth("jobs.list.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        if id:
            serializer = CrontabScheduleSerializers(
                CrontabSchedule.objects.filter(id=id), many=True)
        else:
            serializer = CrontabScheduleSerializers(
                CrontabSchedule.objects.all(), many=True)
        data = serializer.data
        for item in data:
            item["table"] = "crontab"
        return JsonResponse({
            "code": 200,
            "data": data,
            "msg": "获取 crontab 成功"
        })

    @auth("jobs.list.add")
    def post(self, request, args=None):
        data = request.data
        CrontabSchedule.objects.create(minute=data["minute"],
                                       hour=data["hour"],
                                       day_of_week=data["day_of_week"],
                                       day_of_month=data["day_of_month"],
                                       month_of_year=data["month_of_year"],
                                       creater=request.user.username)
        res = {"code": 200, "data": {}, "msg": "新增 crontab 成功"}
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("jobs.list.edit")
    def put(self, request, args=None):
        data = request.data
        CrontabSchedule.objects.filter(id=int(data["id"])).update(**data)
        res = {"code": 200, "data": {}, "msg": "更新 crontab 成功"}
        PutAudit(request, res)
        return JsonResponse(res)
