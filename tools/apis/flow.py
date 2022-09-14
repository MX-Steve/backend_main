from django.http import JsonResponse
from pymysql.converters import escape_string
from utils import baseview
from tools.serializers import *
from tools.models import *


class FlowView(baseview.AnyLogin):
    """
    get:
        获取数据流
    put:
        更新数据流
    post:
        新增数据流
    delete:
        删除数据流
    """

    def get(self, request, args=None):
        id = request.GET.get("id", 1)
        type = request.GET.get("type", "")
        if type == "names":
            data =  DataFlow.objects.values("id","name")
            result = []
            for item in data:
                result.append({"id":item["id"],"name":item["name"]})
            return JsonResponse({
                "code": 200,
                "msg": "获取 flowNames 成功",
                "data": result 
            })
        else:
            serializer = DataFlowSerializer(DataFlow.objects.filter(id=id), many=True)
            result = serializer.data
            return JsonResponse({
                "code": 200,
                "msg": "获取 flow 成功",
                "data": {
                    "id": id,
                    "name": result[0]["name"],
                    "job": result[0]["job"]
                }
            })

    def put(self, request, args=None):
        name = request.data.get('name','')
        job = request.data.get('job','')
        if name == "" or job == "":
            return JsonResponse({
                "code": 10001,
                "msg": "必须传递 name 和 job",
                "data": []
            })
        if job == "UseDemo":
            job = '{"origin":[1000,465],"nodeList":[{"id":"nodeS3WgFnzCI15X58Qw","width":100,"height":80,"coordinate":[-926,-307],"meta":{"prop":"start","name":"开始节点","desc":"流程开始"}}],"linkList":[]}'
            job = escape_string(job)
            DataFlow.objects.create(name=name, job=job)
            return JsonResponse({
                "code": 200,
                "msg": "存入 flow 成功",
                "data": []
            })
        else:
            job = escape_string(job)
        f = DataFlow.objects.filter(name=name).first()
        if f:
            DataFlow.objects.filter(name=name).update(job=job)
        else:
            DataFlow.objects.create(name=name, job=job)
        return JsonResponse({
            "code": 200,
            "msg": "存入 flow 成功",
            "data": []
        })

    def delete(self, request, args):
        fid = request.data.get('id','')
        print(fid)
        if fid == "":
            return JsonResponse({
                "code": 100010,
                "msg": "必须传递 id 参数",
                "data": [] 
            })
        DataFlow.objects.filter(id=fid).delete()
        return JsonResponse({
            "code": 200,
            "msg": "移除 flow name 成功",
            "data": [] 
        })

