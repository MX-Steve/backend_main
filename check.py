# -*- coding:utf-8 -*-
from django.http import JsonResponse
from django.db import connection
from utils import baseview


class check(baseview.AnyLogin):
    """[check]

    get:
       check the app status
    """
    def get(self, request, args=None):
        try:
            sql = "show tables;"
            cursor = connection.cursor()
            cursor.execute(sql)
            cursor.fetchone()
            return JsonResponse({"code": 200, "data": {}, "msg": "online"})
        except Exception as e:  # pylint: disable=broad-except
            return JsonResponse({"code": 500, "data": {}, "msg": e})
