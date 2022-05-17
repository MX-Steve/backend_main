import json
import os
import django
from django.http import JsonResponse


def chat_view(request):
    return JsonResponse({"code": 200, "data": {}, "msg": "测试 chat 功能"})
