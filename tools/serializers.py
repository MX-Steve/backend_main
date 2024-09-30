from rest_framework import serializers
from users.models import User
from .models import AlarmClock, MeatMenus, Articles, DataFlow, JobsProcess, PromoteClock, ResChange


class AlarmClockSerializer(serializers.ModelSerializer):
    """clock serializer"""
    class Meta:
        model = AlarmClock
        fields = "__all__"

class PromoteClockSerializer(serializers.ModelSerializer):
    """promote serializer"""
    class Meta:
        model = PromoteClock
        fields = "__all__"


class MeatMenusSerializer(serializers.ModelSerializer):
    """menus serializer"""
    class Meta:
        model = MeatMenus
        fields = "__all__"


class ArticlesSerializer(serializers.ModelSerializer):
    """articles serializer"""
    class Meta:
        model = Articles
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(id=data["created_by"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["created_by"] = un
        return data


class DataFlowSerializer(serializers.ModelSerializer):
    """data flow serializer"""
    class Meta:
        model = DataFlow
        fields = "__all__"


class JobsProcessSerializer(serializers.ModelSerializer):
    """jobs process serializer"""
    class Meta:
        model = JobsProcess
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(id=data["created_by"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["created_by"] = un
        return data

class ResChangeSerializer(serializers.ModelSerializer):
    """res change serializer"""
    class Meta:
        model = ResChange
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(id=data["created_by"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["created_by"] = un
        return data
