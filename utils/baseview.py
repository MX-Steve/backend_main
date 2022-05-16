# -*- coding:utf-8 -*-
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.views import APIView
from rest_framework import serializers
from users.models import User


class UserInfoSerializers(serializers.ModelSerializer):
    """"user info serializers"""
    class Meta:
        model = User
        fields = ('username', 'user_id', 'email')


class BaseView(APIView):
    "base view"
    permission_classes = (IsAuthenticated, )
    serializer_class = UserInfoSerializers

    def get(self, request, args):
        pass

    def post(self, request, args):
        pass

    def put(self, request, args):
        pass

    def delete(self, request, args):
        pass


class SuperUserpermissions(APIView):
    "super user permissions"
    permission_classes = (IsAdminUser, )

    def get(self, request, args):
        pass

    def post(self, request, args):
        pass

    def put(self, request, args):
        pass

    def delete(self, request, args):
        pass


class AnyLogin(APIView):
    "any login"
    permission_classes = ()
    authentication_classes = ()

    def get(self, request, args):
        pass

    def post(self, request, args):
        pass

    def put(self, request, args):
        pass

    def delete(self, request, args):
        pass
