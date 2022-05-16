import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """The basic user model"""
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False,
                          help_text="用户唯一标识ID")
    roles = models.CharField(default='[]', max_length=50, help_text="用户角色id列表")
    robot_url = models.CharField(max_length=450,
                                 null=True,
                                 blank=True,
                                 verbose_name="机器人地址")
    robot_secret = models.CharField(max_length=200,
                                    null=True,
                                    blank=True,
                                    verbose_name="机器人密钥")
    user_id = models.CharField(max_length=150, null=True, blank=True, verbose_name="飞书user_id")
