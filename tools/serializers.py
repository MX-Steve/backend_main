from rest_framework import serializers
from .models import AlarmClock, MeatMenus, Articles


class AlarmClockSerializer(serializers.ModelSerializer):
    """clock serializer"""
    class Meta:
        model = AlarmClock
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
