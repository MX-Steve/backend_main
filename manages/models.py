import json
from django.db import models
from users.models import User
from utils.mixins import ModelMixin


class Role(models.Model, ModelMixin):
    "role"
    name = models.CharField(max_length=50)
    desc = models.CharField(max_length=255, null=True)
    page_perms = models.TextField(null=True)
    created_at = models.CharField(max_length=20, default="")
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")

    def to_dict(self, *args, **kwargs):
        tmp = super().to_dict(*args, **kwargs)
        tmp['page_perms'] = json.loads(
            self.page_perms) if self.page_perms else {}
        return tmp
