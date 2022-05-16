# pylint: disable=wildcard-import,unused-wildcard-import
# pylint: disable=redefined-builtin
import json
import logging
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import JsonResponse
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import jwt_decode_handler
from utils import baseview
from django.contrib.auth.hashers import check_password, make_password
from utils.auth import auth
from users.models import User
from users.serializers import UserSerializers
from manages.models import Role
from audit.apis.audit import PutAudit

logger = logging.getLogger("ttool.app")


class LoginView(baseview.AnyLogin):
    '''
    post:
        login post view
    get:
        login get view
    '''
    def post(self, request, args=None):
        data = request.data
        res = {"code": 403, "data": {}, "msg": '用户名或密码错误'}
        if "username" not in data or "password" not in data:
            res = {"code": 401, "data": {}, "msg": '需要传递用户名和密码'}
        else:
            username = data["username"]
            password = data["password"]
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            user = authenticate(request, username=username, password=password) 
            if user is not None and user.is_active:
                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                login(request, user)
                res = {
                    "code": 200,
                    "data": {
                        "username": user.get_username(),
                        "token": token
                    },
                    "msg": "登录成功."
                }
            else:
                if User.objects.filter(username=username).first():
                    user = User.objects.get(username=username)
                    last_login = str(user.last_login).split("+")[0]+".000000" 
                    if user is not None and user.is_active and last_login == "2022-01-01 00:00:00.000000":
                        if check_password(password, user.password):
                            payload = jwt_payload_handler(user)
                            token = jwt_encode_handler(payload)
                            login(request, user) 
                            res = {
                                "code": 200,
                                "data": {
                                    "username": user.get_username(),
                                    "token": token
                                },
                                "msg": "登录成功."
                            }
                        else:
                            user.password = make_password(password)
                            # user.last_login = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +".000000"
                            user.save()
                            payload = jwt_payload_handler(user)
                            token = jwt_encode_handler(payload)
                            login(request, user)
                            res = {
                                "code": 200,
                                "data": {
                                    "username": user.get_username(),
                                    "token": token
                                },
                                "msg": "登录成功."
                            }
        PutAudit(request, res)
        return JsonResponse(res)


class UserInfoView(baseview.BaseView):
    "user info view"

    def get(self, request, args=None):
        token = ""
        authorization = request.META.get('HTTP_AUTHORIZATION')
        if authorization is not None:
            token = authorization.split(' ')[1]
        if token == "":
            return JsonResponse({
                "code": 404,
                "data": {},
                "msg": 'need auth-key.'
            })
        user_dict = jwt_decode_handler(token=token)
        user_obj = User.objects.filter(username=user_dict["username"])
        if user_obj.exists():
            serializers = UserSerializers(user_obj, many=True)
            data = serializers.data
            page_perms = []
            if len(data[0]['roles']) == 2:
                role_name = "review"
                r = Role.objects.filter(name=role_name).first()
                user_obj.update(roles="[%d,]" % (r.id))
                user_obj = User.objects.filter(
                    username=user_dict["username"]).first()
                page_perms_ids = user_obj.roles.strip('[').strip(']').split(
                    ',')
            else:
                page_perms_ids = data[0]['roles'].strip('[').strip(']').split(
                    ',')
            for pid in page_perms_ids:
                if pid != "":
                    r = Role.objects.filter(id=int(pid)).first()
                    perms = r.page_perms.strip('[').strip(']').split(',')
                    for p in perms:
                        if p not in page_perms:
                            page_perms.append(p)
            data[0]["page_perms"] = page_perms
            return JsonResponse({
                "code": 200,
                "data": {
                    "user_info": data
                },
                "msg": "get user info success"
            })
        return JsonResponse({
            "code": 404,
            "data": {},
            "msg": 'user not exist.'
        })


class UsernamesView(baseview.AnyLogin):
    """只提供 id 和 username"""
    def get(self, request, args=None):
        users = User.objects.order_by("username").values("id", "username", "first_name", "last_name")
        total = len(users)
        data = []
        for user in users:
            un = user["last_name"].strip() + user["first_name"].strip()
            if un:
                data.append({"id": user['id'], "username":un})
            else:
                data.append({"id": user['id'], "username":user["username"]})
        return JsonResponse({
            "code": 200,
            "data": {
                "users": data,
                "total": total
            },
            "msg": "获取所有用户简要信息成功"
        })

def is_Chinese(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False
class UsersView(baseview.BaseView):
    """user view"""
    @auth("manages.user.view")
    def get(self, request, args=None):
        username = request.GET.get('name', '')
        status = request.GET.get('status', '')
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        if username != "":
            if is_Chinese(username):
                if len(username) >= 4:
                    first_name = username[2:]
                    last_name = username[0:2]
                    serializer = UserSerializers(
                        User.objects.filter(first_name__contains=first_name, last_name=last_name), many=True)
                elif len(username) > 2:
                    first_name = username[1:]
                    last_name = username[0]
                    serializer = UserSerializers(
                        User.objects.filter(first_name__contains=first_name, last_name=last_name), many=True)
                elif len(username) == 2:
                    first_name = username[1:]
                    last_name = username[0]
                    serializer = UserSerializers(
                        User.objects.filter(first_name__contains=first_name, last_name=last_name), many=True)
                    if len(serializer.data) == 0:
                        serializer = UserSerializers(
                            User.objects.filter(first_name__contains=username), many=True)
                else:
                    serializer = UserSerializers(
                        User.objects.filter(Q(last_name=username)|Q(first_name__contains=username)), many=True)
            else:
                serializer = UserSerializers(
                    User.objects.filter(username__contains=username), many=True)
        elif status != "":
            if status == "on":
                serializer = UserSerializers(
                    User.objects.filter(is_active=True).order_by("username"), many=True)
            elif status == "off":
                serializer = UserSerializers(
                    User.objects.filter(is_active=False).order_by("username"), many=True)
            else:
                serializer = UserSerializers(User.objects.all().order_by("username"), many=True)
        else:
            serializer = UserSerializers(User.objects.all().order_by("username"), many=True)
        data = []
        total = len(serializer.data)
        for item in serializer.data[(pageNo - 1) * pageSize:pageNo * pageSize]:
            if item['is_active']:
                status = "on"
            else:
                status = "off"
            roleIds = item["roles"].strip('[').strip(']').split(',')
            roleNames = []
            for id in roleIds:
                if id != "":
                    r = Role.objects.filter(id=id).first()
                    roleNames.append(r.name)
            data.append({
                "id":
                item['id'],
                "username":
                item['username'],
                "zh_name":
                item['last_name'] + " " + item['first_name'],
                "last_login":
                item['last_login'].replace("T", " ").split(".")[0],
                "status":
                status,
                "roles":
                roleNames
            })
        return JsonResponse({
            "code": 200,
            "data": {
                "users": data,
                "total": total
            },
            "msg": "获取所有用户信息成功"
        })

    @auth(
        "manages.user.status_change|manages.user.roles_change|personal.user_center.config_robot"
    )
    def post(self, request, args=None):
        data = request.data
        res = {"code": 10003, "data": {}, "msg": "type 类型不存在"}
        needs = {"type", "value", "id"}
        if set(data.keys()).intersection(needs) != needs:
            res = {"code": 10003, "data": {}, "msg": "需要携带参数 id,type,value"}
        else:
            if data["type"] == "status":
                if data["value"] == "on":
                    User.objects.filter(id=data["id"]).update(is_active=True)
                else:
                    User.objects.filter(id=data["id"]).update(is_active=False)
                res = {"code": 200, "data": {}, "msg": "修改用户状态成功"}
            if data["type"] == "roles":
                if len(data["value"]) == 2:
                    ids = "[]"
                else:
                    names = data["value"].strip('[').strip(']').split(',')
                    ids = "["
                    for item in names:
                        r = Role.objects.filter(name=item).first()
                        ids += str(r.id) + ","
                    ids += "]"
                User.objects.filter(id=data["id"]).update(roles=ids)
                res = {"code": 200, "data": {}, "msg": "用户绑定角色成功"}
            if data["type"] == "robot":
                User.objects.filter(id=data["id"]).update(
                    robot_url=data["robot_url"],
                    robot_secret=data["robot_secret"])
                res = {"code": 200, "data": {}, "msg": "修改机器人信息成功"}
        PutAudit(request, res)
        return JsonResponse(res)


class LogoutView(baseview.BaseView):
    "logout view"
    def post(self, request, args=None):
        res = {"code": 200, "data": {}, "msg": '退出平台.'}
        PutAudit(request, res)
        logout(request)
        return JsonResponse(res)


class RegisterView(baseview.AnyLogin):
    "register user view"
    def post(self, request, args=None):
        data = request.data
        res = {"code": 200, "data": {}, "msg": '用户注册成功.'}
        if "username" not in data or "password" not in data:
            res = {"code": 10003, "data": {}, "msg": '需要参数 username,password'}
        else:
            username = data["username"]
            password = data["password"]
            user = User.objects.filter(username=username)
            if user.exists():
                res = {"code": 10001, "data": {}, "msg": '用户已经存在.'}
            User.objects.create_user(username=username, password=password)
        PutAudit(request, res)
        return JsonResponse(res)


class RefreshTokenView(baseview.BaseView):
    """refresh token view"""
    def post(self, request, args=None):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(request.user)
        token = jwt_encode_handler(payload)
        res = {"code": 200, "data": {'token': token}, "msg": "刷新 token 成功"}
        PutAudit(request, res)
        return JsonResponse(res)


class BtnCheckView(baseview.BaseView):
    def post(self, request, args=None):
        key = request.data["keys"]
        username = request.user.username
        role_ids = User.objects.filter(
            username=username).first().roles.strip('[').strip(']').split(',')
        perms = []
        obj = {
            "edit": 0,
            "add": 0,
            "del": 0,
            "down": 0,
            "conn": 0,
        }
        for role_id in role_ids:
            if role_id:
                r = Role.objects.filter(id=role_id).first()
                page_perms = r.page_perms.strip('[').strip(']').split(',')
                for perm in page_perms:
                    if perm not in perms:
                        perms.append(perm)
        for item in perms:
            if key in item:
                item = item.split('.')[-1]
                if "edit" in item:
                    obj["edit"] = 1
                elif "add" in item:
                    obj["add"] = 1
                elif "del" in item:
                    obj["del"] = 1
                elif "down" in item:
                    obj["down"] = 1
                elif "conn" in item:
                    obj["conn"] = 1
        return JsonResponse({"code": 200, "data": obj, "msg": "按钮鉴权数据"})
