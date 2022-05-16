from django.db import models


class AuditHistory(models.Model):
    """audit history"""
    operater = models.CharField(max_length=24,
                                null=True,
                                blank=True,
                                default="",
                                verbose_name="操作者")
    operate_time = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="操作时间")
    req_url = models.CharField(max_length=255,
                               null=True,
                               blank=True,
                               default="",
                               verbose_name="请求url")
    req_method = models.CharField(max_length=25,
                                  null=True,
                                  default="",
                                  verbose_name='请求方法')
    req_data = models.TextField(null=True, default="", verbose_name="请求数据")
    res_data = models.TextField(null=True, default="", verbose_name="相应数据")
    del_tag = models.IntegerField(null=True,
                                  blank=True,
                                  default=0,
                                  verbose_name="删除标识")
