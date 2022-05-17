from rest_framework import serializers
from .models import IntervalSchedule, PeriodicTask, ResultsTasks, CrontabSchedule
from users.models import User


class IntervalScheduleSerializers(serializers.ModelSerializer):
    """interval schedule serializers"""
    class Meta:
        model = IntervalSchedule
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(username=data["creater"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["creater"] = un
        return data


class PeriodicTaskSerializers(serializers.ModelSerializer):
    """periodic task serializers"""
    class Meta:
        model = PeriodicTask
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(username=data["creater"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["creater"] = un
        user2 = User.objects.filter(username=data["updater"]).first()
        if user2:
            un2 = user2.last_name.strip() + user2.first_name.strip()
            if un2:
                data["updater"] = un2
        return data


class ResultsTasksSerializers(serializers.ModelSerializer):
    """results tasks serializers"""
    class Meta:
        model = ResultsTasks
        fields = "__all__"


class CrontabScheduleSerializers(serializers.ModelSerializer):
    """crontab schedule serializers"""
    class Meta:
        model = CrontabSchedule
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        user = User.objects.filter(username=data["creater"]).first()
        if user:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data["creater"] = un
        if data["args"]:
            data["task"] = data["task"] + \
                "("+data["args"].replace("[", "").replace("]", "")+")"
        if data["kwargs"]:
            data["task"] = data["task"] + \
                "("+data["kwargs"].replace("{",
                                           "").replace("}", "").replace(":", "=") + ")"
        return data
