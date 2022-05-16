from rest_framework import serializers
from .models import User


class UserSerializers(serializers.ModelSerializer):
    """user serializers"""
    username = serializers.CharField(max_length=45)

    class Meta:
        model = User
        fields = "__all__"
    
    def to_representation(self, value):
        data = super().to_representation(value)
        zh_name = data["last_name"].strip() + data["first_name"].strip()
        data["zh_name"] = zh_name
        return data
