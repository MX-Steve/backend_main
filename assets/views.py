import json
from django.http import JsonResponse
from utils import baseview

class TestView(baseview.AnyLogin):
    def get(self, request, args=None):
        return JsonResponse({"code": 200})