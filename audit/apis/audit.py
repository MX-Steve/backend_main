from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import timedelta, datetime
from utils import baseview
from audit.models import *
from audit.serializers import *
from utils.util import now
import json


class AuditHistoryView(baseview.BaseView):
    def get(self, request, args=None):
        id = request.GET.get("id", "")
        page_no = int(request.GET.get("page_no", 1))
        page_size = int(request.GET.get("page_size", 10))
        operater = request.GET.get("operater", "")
        req_url = request.GET.get("req_url", "")
        req_method = request.GET.get("req_method", "")
        req_data = request.GET.get("req_data", "")
        res_data = request.GET.get("res_data", "")
        start = request.GET.get("start", "")
        end = request.GET.get("end", "")
        if end == "":
            end = now()
        end = end.replace("T", " ").split(".")[0]
        if start == "":
            before = datetime.today() + timedelta(-3)
            start = before.strftime("%Y-%m-%d %H:%M:%S")
        start = start.replace("T", " ").split(".")[0]
        if id:
            serializer = AuditHistorySerializer(
                AuditHistory.objects.filter(id=id), many=True)
        else:
            q = Q()
            q.children.append(("del_tag", 0))
            q.children.append(("operate_time__range", [start, end]))
            if operater:
                q.children.append(("operater", operater))
            if req_url:
                q.children.append(("req_url__contains", req_url))
            if req_method:
                q.children.append(("req_method", req_method))
            # serializer = AuditHistorySerializer(AuditHistory.objects.filter(q).exclude(req_url="/users/v1/login").order_by("-operate_time"),
            #                                     many=True)
            serializer = AuditHistorySerializer(
                AuditHistory.objects.filter(q).order_by("-operate_time"),
                many=True)
        total = len(serializer.data)
        data = serializer.data[(page_no - 1) * page_size:page_no * page_size]
        return JsonResponse({
            "code": 200,
            "data": {
                "audit": data,
                "total": total
            },
            "msg": "获取审计数据成功"
        })


def PutAudit(request, res):
    req_method = request.method
    if req_method == "GET":
        return
    operater = request.user.username
    req_data = json.dumps(request.data)
    req_url = request.path
    res_data = json.dumps(res)
    AuditHistory.objects.create(operater=operater,
                                operate_time=now(),
                                req_url=req_url,
                                req_method=req_method,
                                req_data=req_data,
                                res_data=res_data)
