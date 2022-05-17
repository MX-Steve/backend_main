from django.db import models


class IntervalSchedule(models.Model):
    """interval schedule"""
    every = models.IntegerField(null=True, blank=True, verbose_name="间隔长度")
    period = models.CharField(max_length=24,
                              null=True,
                              blank=True,
                              verbose_name="单位")
    del_tag = models.IntegerField(null=True,
                                  blank=True,
                                  default=0,
                                  verbose_name="删除标识")
    creater = models.CharField(max_length=24,
                               null=True,
                               blank=True,
                               default="",
                               verbose_name="创建者")

    class Meta:
        db_table = "django_celery_beat_intervalschedule"
        managed = False

    def __str__(self):
        return self.every + " " + self.period


class PeriodicTask(models.Model):
    """periodic task"""
    name = models.CharField(max_length=200,
                            null=True,
                            blank=True,
                            verbose_name="任务名称")
    task = models.CharField(max_length=200,
                            null=True,
                            blank=True,
                            verbose_name="任务位置")
    args = models.TextField(null=True, verbose_name="args参数")
    kwargs = models.TextField(null=True, verbose_name="kwargs参数")
    queue = models.CharField(max_length=200,
                             null=True,
                             blank=True,
                             verbose_name="queue")
    exchange = models.CharField(max_length=200,
                                null=True,
                                blank=True,
                                verbose_name="exchange")
    routing_key = models.CharField(max_length=200,
                                   null=True,
                                   blank=True,
                                   verbose_name="routing_key")
    expires = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    enabled = models.IntegerField(null=True, blank=True, verbose_name="是否启用")
    last_run_at = models.DateTimeField(null=True,
                                       blank=True,
                                       verbose_name="上次运行时间")
    total_run_count = models.IntegerField(null=True,
                                          blank=True,
                                          verbose_name="总运行数")
    date_changed = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="时间更新")
    description = models.TextField(null=True, blank=True, verbose_name="描述信息")
    crontab_id = models.IntegerField(null=True,
                                     blank=True,
                                     verbose_name="crontab id")
    interval_id = models.IntegerField(null=True,
                                      blank=True,
                                      verbose_name="间隔时间表 id")
    solar_id = models.IntegerField(null=True,
                                   blank=True,
                                   verbose_name="solar id")
    one_off = models.IntegerField(null=True, blank=True, verbose_name="一次运行开关")
    start_time = models.IntegerField(null=True,
                                     blank=True,
                                     verbose_name="开始时间")
    priority = models.IntegerField(null=True, blank=True, verbose_name="优先级")
    headers = models.TextField(null=True, verbose_name="headers")
    clocked_id = models.IntegerField(null=True,
                                     blank=True,
                                     verbose_name="clocked id")
    expire_seconds = models.IntegerField(null=True,
                                         blank=True,
                                         verbose_name="过期秒数")
    del_tag = models.IntegerField(null=True,
                                  blank=True,
                                  default=0,
                                  verbose_name="删除标识")
    creater = models.CharField(max_length=24,
                               null=True,
                               blank=True,
                               default="",
                               verbose_name="创建者")
    updater = models.CharField(max_length=24,
                               null=True,
                               blank=True,
                               default="",
                               verbose_name="更新者")

    class Meta:
        db_table = "django_celery_beat_periodictask"
        managed = False


class ResultsTasks(models.Model):
    task_id = models.CharField(max_length=255,
                               null=True,
                               blank=True,
                               verbose_name="任务ID")
    task_name = models.CharField(max_length=255,
                                 null=True,
                                 blank=True,
                                 verbose_name="任务名称")
    task_args = models.TextField(null=True, verbose_name="task_args参数")
    task_kwargs = models.TextField(null=True, verbose_name="task_kwargs参数")
    status = models.CharField(max_length=50,
                              null=True,
                              blank=True,
                              verbose_name="运行状态")
    worker = models.CharField(max_length=100,
                              null=True,
                              blank=True,
                              verbose_name="工作节点")
    content_type = models.CharField(max_length=128,
                                    null=True,
                                    blank=True,
                                    verbose_name="内容类型")
    content_encoding = models.CharField(max_length=64,
                                        null=True,
                                        blank=True,
                                        verbose_name="编码类型")
    result = models.TextField(null=True, verbose_name="运行结果")
    date_created = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="开始时间")
    date_done = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="结束时间")
    traceback = models.TextField(null=True, verbose_name="报错跟踪")
    meta = models.TextField(null=True, verbose_name="meta信息")

    class Meta:
        db_table = "django_celery_results_taskresult"
        managed = False


class CrontabSchedule(models.Model):
    """crontab schedule"""
    minute = models.CharField(max_length=24,
                              null=True,
                              blank=True,
                              default="*",
                              verbose_name="分钟")
    hour = models.CharField(max_length=24,
                            null=True,
                            blank=True,
                            default="*",
                            verbose_name="小时")
    day_of_week = models.CharField(max_length=24,
                                   null=True,
                                   blank=True,
                                   default="*",
                                   verbose_name="星期几")
    day_of_month = models.CharField(max_length=24,
                                    null=True,
                                    blank=True,
                                    default="*",
                                    verbose_name="几号")
    month_of_year = models.CharField(max_length=24,
                                     null=True,
                                     blank=True,
                                     default="*",
                                     verbose_name="月份")
    timezone = models.CharField(max_length=24,
                                null=True,
                                blank=True,
                                default="Asia/Shanghai",
                                verbose_name="时区")
    del_tag = models.IntegerField(null=True,
                                  blank=True,
                                  default=0,
                                  verbose_name="删除标识")
    creater = models.CharField(max_length=24,
                               null=True,
                               blank=True,
                               default="",
                               verbose_name="创建者")

    class Meta:
        db_table = "django_celery_beat_crontabschedule"
        managed = False
