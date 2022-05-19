from django.http import JsonResponse
from utils import baseview
from assets.models import BusinessServices


class ChoicesView(baseview.AnyLogin):
    def get(self, request, args=None):
        """models choices value"""
        table_name = request.GET.get("table_name", "")
        column = request.GET.get("column", "")
        if table_name == "" or column == "":
            msg = {"code": 10002, "data": {}, "msg": "必须传递表名和choice 列"}
        else:
            choices = []
            if table_name == "BusinessServices":
                for k, v in BusinessServices.type_choices:
                    choices.append(v)
            msg = {"code": 200, "data": choices, "msg": "获取选项成功"}
        return JsonResponse(msg)
