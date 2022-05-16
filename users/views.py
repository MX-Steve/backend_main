import json
import logging
from django.http import JsonResponse
from google.protobuf.json_format import MessageToJson
from backend.stubs import GetStub
from backend.proto.djentry_pb2 import UserInfoRequest

logger = logging.getLogger("ttool.app")


def test(req):
    logger.info(req)
    return JsonResponse({"code": 200})


def grpc_test(req):
    stub = GetStub()
    req = UserInfoRequest(user_id="abc-23a")
    r = stub.GetUserInfo(req)
    r = json.loads(MessageToJson(r))
    return JsonResponse({"code": 200, "data": {"user": r}, "msg": "grpc test"})
