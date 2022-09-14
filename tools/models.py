from django.db import models
from users.models import User


class AlarmClock(models.Model):
    "alarm clock"
    name = models.CharField(max_length=50)
    desc = models.CharField(max_length=255, null=True)
    music = models.SmallIntegerField(default=0, help_text="是否启用音乐")
    alarm_time = models.CharField(max_length=20, default="")
    created_at = models.CharField(max_length=20, default="")
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class MeatMenus(models.Model):
    "meat menus"
    content = models.CharField(max_length=250)
    type = models.CharField(max_length=50, null=True)
    meat_date = models.CharField(max_length=20, default="")
    meat_day = models.CharField(max_length=20, default="")
    created_at = models.CharField(max_length=20, default="")
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class Articles(models.Model):
    "articles"
    content = models.TextField(max_length=65535, help_text="文章内容")
    title = models.CharField(max_length=250, null=True, help_text="文章标题")
    # frontend/backend/db/structure/other/shell/python/security/network
    type = models.CharField(max_length=50, null=True, help_text="文章类型")
    created_at = models.CharField(max_length=20, default="")
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class DataFlow(models.Model):
    name = models.CharField(max_length=500, help_text="流程名称")
    job = models.TextField(max_length=65535, help_text="流程内容")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")

    class Meta:
        managed = False
        db_table = 'flow_job'
