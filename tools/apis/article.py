from django.http import JsonResponse
from utils.auth import auth
from utils import baseview
from utils.util import now
from tools.serializers import *
from tools.models import *
from users.models import User
from audit.apis.audit import PutAudit
from django.db.models import Count, Q
from django.utils.encoding import escape_uri_path
from django.http import StreamingHttpResponse
from rest_framework import status
import os
from shutil import copyfile


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
        user = User.objects.filter(username=request.user.username).first()
        id = request.GET.get('id', '')
        title = request.GET.get('title', '')
        type = request.GET.get('type', '')
        content = request.GET.get('content', '')
        details = request.GET.get('content', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        is_open = 1
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
        if details:
            q.children.append(("details__contains", details))
        # q.children.append(("created_by", user))
        q2 = Q()
        q2.children.append(("del_tag", 0))
        q2.children.append(("is_open", is_open))
        if id != "" or title != "" or content != "":
            serializer = ArticlesSerializer(Articles.objects.filter(q).order_by("-id"),
                                        many=True)
        else:
            q.children.append(("created_by", user))
            serializer = ArticlesSerializer(Articles.objects.filter(q|q2).order_by("-id"),
                                        many=True)
        # if not id:
        #     q.children.append(("is_open", is_open))
        #     # q.children.append(("created_by", user))
        # serializer = ArticlesSerializer(Articles.objects.filter(q).order_by("-created_at"),
        #                                 many=True)
        # if id:
        #     serializer = ArticlesSerializer(Articles.objects.filter(q).order_by("-created_at"),
        #                                 many=True)
        # else:
        #     q2 = Q()
        #     # q2.children.append(("created_by", user))
        #     q2.children.append(("del_tag", 0))
        #     # q2.children.append(("is_open", is_open))
        #     serializer = ArticlesSerializer(Articles.objects.filter(q|q2).order_by("-created_at"),
        #                                 many=True)
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
        user = User.objects.filter(username=request.user.username).first()
        data = request.data
        res = {"code": 200, "data": {}, "msg": "删除文章成功"}
        if "id" not in data:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id"}
        else:
            if Articles.objects.filter(id=data["id"], created_by=user).exists():
                Articles.objects.filter(id=data["id"]).update(del_tag=1)
            else:
                res = {"code": 10003, "data": {}, "msg": "只能删除属于自己的文件"}
        PutAudit(request, res)
        return JsonResponse(res)

    @auth("tools.articles.edit")
    def put(self, request, args=None):
        user = User.objects.filter(username=request.user.username).first()
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
                if Articles.objects.filter(id=data["id"], created_by=user).exists():
                    Articles.objects.filter(id=data["id"]).update(
                        title=data["title"],
                        content=data["content"],
                        details=data["details"],
                        type=data["type"],
                        is_open=data["is_open"],
                        created_at=now(),
                        created_by=request.user)
                else:
                    res = {"code": 10003, "data": {}, "msg": "只能更新属于自己的文件"}
        PutAudit(request, res)
        return JsonResponse(res)


def alter(file, old_str, new_str):
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with open(file, "w", encoding="utf-8") as f:
        f.write(file_data)


class ArticleDownView(baseview.BaseView):
    """
    post:
        下载文章
    """
    @auth("tools.articles.add")
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": "下载文章成功"}
        if Articles.objects.filter(title=data["title"], del_tag=0).exists():
            article = Articles.objects.filter(
                title=data["title"], del_tag=0).first()
            title = "%s.html" % (article.title)
            prePath = os.getcwd() + "/tools/apis/b.html"
            finPath = os.getcwd() + "/files/tmp.html"
            copyfile(prePath, finPath)
            alter(finPath, "question", article.details)
            alter(finPath, "resolve", article.content)
            response = self.big_file_download(finPath, title)
            if response:
                PutAudit(request, res)
                return response
        else:
            user = User.objects.filter(username=request.user.username).first()
            data["created_at"] = now()
            Articles.objects.create(created_by=user, **data)
            res = {"code": 10001, "data": {}, "msg": "文章不存在，无法下载"}
            PutAudit(request, res)
        return JsonResponse(res)

    def file_iterator(self, file_path, chunk_size=512):
        """
        文件生成器,防止文件过大，导致内存溢出
        :param file_path: 文件绝对路径
        :param chunk_size: 块大小
        :return: 生成器
        """
        with open(file_path, mode='rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    def big_file_download(self, download_file_path, filename):
        try:
            response = StreamingHttpResponse(
                self.file_iterator(download_file_path))
            # 增加headers
            response['Content-Type'] = 'application/octet-stream'
            response['Access-Control-Expose-Headers'] = "Content-Disposition, Content-Type"
            response['Content-Disposition'] = "attachment; filename={}".format(
                escape_uri_path(filename))
            return response
        except Exception:
            return JsonResponse({'status': status.HTTP_400_BAD_REQUEST, 'msg': 'Excel下载失败'},
                                status=status.HTTP_400_BAD_REQUEST)
