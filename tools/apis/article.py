from certifi import contents
from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q


class ArticlesView(baseview.BaseView):
    """
    get:
        获取文章
    put:
        更新文章
    post:
        新增文章
    delete:
        删除文章
    """
    @auth("tools.articles.view")
    def get(self, request, args=None):
        id = request.GET.get('id', '')
        title = request.GET.get('title', '')
        type = request.GET.get('type', '')
        content = request.GET.get('content', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        q = Q()
        q.children.append(("del_tag", 0))
        if id:
            q.children.append(('id', id))
        if type:
            q.children.append(('type', type))
        if title:
            q.children.append(("title__contains", title))
        if content:
            q.children.append(("content__contains", content))
        serializer = ArticlesSerializer(Articles.objects.filter(q).order_by("-created_at"),
                                          many=True)
        data = []
        total = len(serializer.data)
        data = serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]
        return JsonResponse({
            "code": 200,
            "data": {
                "articles": data,
                "total": total
            },
            "msg": "获取文章成功"
        })

    @auth("tools.articles.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "新增文章成功"}
        if Articles.objects.filter(title=data["title"], del_tag=0).exists():
            res = {"code": 10001, "data": {}, "msg": "文章已经存在，无法新增"}
        else:
            user = User.objects.filter(username=request.user.username).first()
            data["created_at"] = now()
            Articles.objects.create(created_by=user, **data)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.articles.del")
    def delete(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除文章成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            Articles.objects.filter(id=data["id"]).update(del_tag=1)
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.articles.edit")
    def put(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "文章更新成功"}
        needs = {"id", "title", "type", "content"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {},
                   "msg": "需要携带参数 id, title, type, content"}
        else:
            if not Articles.objects.filter(id=data["id"]).exists():
                res = {"code": 10002, "data": {}, "msg": "文章不存在，无法更新"}
            else:
                Articles.objects.filter(id=data["id"]).update(
                    title=data["title"],
                    content=data["content"],
                    type=data["type"],
                    created_at=now(),
                    created_by=request.user)
        PutAudit(request, res)
        return JsonResponse(res)
