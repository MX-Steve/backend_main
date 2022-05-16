from django.db import models


class DeviceType(models.Model):
    """device type"""
    name = models.CharField(max_length=65,
                            help_text="设备名称",
                            unique=True,
                            default=None)
    del_tag = models.IntegerField(default=0, help_text="删除标识")


class DeviceStatus(models.Model):
    """device status"""
    name = models.CharField(max_length=125, help_text="设备状态", default=None)
    type_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="所属设备类型")
    description = models.CharField(max_length=250,
                                   help_text="描述信息",
                                   default=None)
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class ZoneInfo(models.Model):
    """zone info"""
    name = models.CharField(max_length=65,
                            help_text="区域名称",
                            unique=True,
                            default=None)
    description = models.CharField(max_length=250,
                                   help_text="区域描述信息",
                                   default=None)
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class Machine(models.Model):
    """
    服务器信息
    """
    sn_id = models.CharField(null=True,
                             blank=True,
                             max_length=50,
                             verbose_name="资产编号")
    instance_name = models.CharField(null=True,
                                     blank=True,
                                     max_length=200,
                                     verbose_name="主机名")
    zone_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="所属区域")
    idc_id = models.SmallIntegerField(null=True,
                                      blank=True,
                                      verbose_name="所属机房|可用区")
    status_id = models.SmallIntegerField(null=True,
                                         blank=True,
                                         verbose_name="设备状态")
    type_choices = ((1, '物理机'), (2, '云服务器'), (3, '虚拟机'))
    server_type = models.IntegerField(choices=type_choices,
                                      verbose_name="服务器类型")
    ip_address = models.CharField(null=True,
                                  blank=True,
                                  max_length=50,
                                  verbose_name="IP地址")
    os_type = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               verbose_name="系统类型")
    username = models.CharField(null=True,
                                blank=True,
                                max_length=50,
                                verbose_name="账户")
    authentication_choices = (
        (1, 'password'),
        (2, 'file'),
    )
    authentication_type = models.IntegerField(choices=authentication_choices,
                                              null=True,
                                              blank=True)
    port = models.IntegerField(null=True, blank=True, verbose_name="端口")
    password = models.CharField(null=True,
                                blank=True,
                                max_length=150,
                                verbose_name="密码")
    sudo_password = models.CharField(null=True,
                                     blank=True,
                                     max_length=50,
                                     verbose_name="sudo密码")
    optional = models.TextField(null=True, blank=True, verbose_name="可选信息")
    '''
    {'cloud_ecs': {'instance_name': '实例名称',
                  'charge_type': '付费类型',
                  'create_time':'创建时间',
                  'expiration_time':'到期时间',
                  },
     'physical_machine': {
                  'cabinet_id': '机柜id'
                  },
     'virtual_machine': {
                  'cabinet_id': '机柜id',
                  'machine_id': '机器id'
                  }
    }
    '''
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="入库更新时间")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    # add
    has_virt = models.BooleanField(default=False, verbose_name="有无虚拟机")
    rel_server_id = models.IntegerField(null=True,
                                        blank=True,
                                        verbose_name="关联IP")
    virt_cird = models.CharField(null=True,
                                 blank=True,
                                 max_length=255,
                                 verbose_name="虚拟IP段")


class CDN(models.Model):
    """
    CDN
    """
    domain_name = models.CharField(null=True,
                                   blank=True,
                                   max_length=500,
                                   verbose_name="域名")
    cdn_name = models.CharField(null=True,
                                blank=True,
                                max_length=500,
                                verbose_name="加速域名")
    ssl_protocol = models.CharField(null=True,
                                    blank=True,
                                    max_length=10,
                                    verbose_name="https开关")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=1000,
                                   verbose_name="描述")
    coverage = models.CharField(null=True,
                                blank=True,
                                max_length=100,
                                verbose_name="加速区域")
    resource_group_id = models.CharField(null=True,
                                         blank=True,
                                         max_length=100,
                                         verbose_name="资源组ID")
    sandbox = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               verbose_name="沙盒")
    # domain_status_choices = (('online', '启用'), ('offline', '停用'),
    #                          ('configuring', '配置中'), ('configure_failed',
    #                                                   '配置失败'),
    #                          ('checking', '正在审核'), ('check_failed', '审核失败'),
    #                          ('stopping', '停用中'), ('deleting', '删除中'))
    domain_status = models.SmallIntegerField(null=True, blank=True,
                                             verbose_name="加速域名状态")
    cdn_type_choices = (('web', '图片小文件'), ('download', '大文件'), ('video',
                                                                '音视频点播'))
    cdn_type = models.CharField(choices=cdn_type_choices,
                                max_length=20,
                                verbose_name="业务类型")
    gmt_created = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="创建时间")
    gmt_modified = models.CharField(null=True,
                                    blank=True,
                                    max_length=50,
                                    verbose_name="修改时间")
    source = models.TextField(null=True, blank=True, verbose_name="源站信息")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class Domain(models.Model):
    """
    域名
    """
    domain_name = models.CharField(null=True,
                                   blank=True,
                                   max_length=200,
                                   verbose_name="域名")
    domain_id = models.CharField(null=True,
                                 blank=True,
                                 max_length=50,
                                 verbose_name="域名ID")
    registrant_type_choices = ((1, '个人'), (2, '企业'))
    registrant_type = models.CharField(null=True,
                                       blank=True,
                                       max_length=20,
                                       choices=registrant_type_choices,
                                       verbose_name="域名注册类型")
    domain_type = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="域名类型")
    email = models.CharField(null=True,
                             blank=True,
                             max_length=100,
                             verbose_name="注册邮箱")
    registration_date = models.CharField(null=True,
                                         blank=True,
                                         max_length=100,
                                         verbose_name="注册日期")
    expiration_date = models.CharField(null=True,
                                       blank=True,
                                       max_length=100,
                                       verbose_name="到期日期")
    domain_status_choices = ((1, '急需付费'), (2, '急需赎回'), (3, '正常'))
    domain_status = models.IntegerField(choices=domain_status_choices,
                                        verbose_name="域名状态")
    domain_owner = models.CharField(null=True,
                                    blank=True,
                                    max_length=200,
                                    verbose_name="域名持有者")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")
    belong_to = models.CharField(null=True,
                                 blank=True,
                                 max_length=100,
                                 verbose_name="域名注册归属")
    cf_zone_id = models.CharField(null=True,
                                  blank=True,
                                  max_length=100,
                                  verbose_name="cloudflare zone id")


class RDS(models.Model):
    """
    数库
    """
    rds_id = models.CharField(null=True,
                              blank=True,
                              max_length=50,
                              verbose_name="实例ID")
    rds_name = models.CharField(null=True,
                                blank=True,
                                max_length=200,
                                verbose_name="实例名称")
    run_status = models.SmallIntegerField(null=True,
                                          blank=True,
                                          verbose_name="运行状态")
    create_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="创建时间")
    expiration_time = models.CharField(null=True,
                                       blank=True,
                                       max_length=50,
                                       verbose_name="到期时间")
    engine = models.CharField(null=True,
                              blank=True,
                              max_length=50,
                              verbose_name="引擎")
    engine_version = models.CharField(null=True,
                                      blank=True,
                                      max_length=50,
                                      verbose_name="引擎版本")
    port = models.IntegerField(null=True, blank=True, verbose_name="端口")
    conn_address = models.CharField(null=True,
                                    blank=True,
                                    max_length=50,
                                    verbose_name="IP地址")
    charge_type = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="付费类型")
    idc_id = models.SmallIntegerField(null=True,
                                      blank=True,
                                      verbose_name="可用区|机房")
    zone_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="区域")
    tags = models.TextField(null=True, blank=True, verbose_name="标签列表")
    remark = models.CharField(null=True,
                              blank=True,
                              max_length=500,
                              verbose_name="备注")
    specs = models.TextField(null=True, blank=True, verbose_name="规格")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class Oss(models.Model):
    """
    存储桶
    """
    oss_name = models.CharField(null=True,
                                blank=True,
                                max_length=200,
                                verbose_name="oss名称")
    location = models.CharField(null=True,
                                blank=True,
                                max_length=200,
                                verbose_name="地域")
    storage_class = models.CharField(null=True,
                                     blank=True,
                                     max_length=200,
                                     verbose_name="存储类型")
    extranet_endpoint = models.CharField(null=True,
                                         blank=True,
                                         max_length=200,
                                         verbose_name="外网域名")
    intranet_endpoint = models.CharField(null=True,
                                         blank=True,
                                         max_length=200,
                                         verbose_name="内网域名")
    create_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=100,
                                   verbose_name="创建时间")
    grant = models.CharField(null=True,
                             blank=True,
                             max_length=20,
                             verbose_name="ACL权限")
    data_redundancy_type = models.CharField(null=True,
                                            blank=True,
                                            max_length=50,
                                            verbose_name="数据容灾类型")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class Disk(models.Model):
    """
    磁盘
    """
    disk_name = models.CharField(null=True,
                                 blank=True,
                                 max_length=100,
                                 verbose_name="名称")
    disk_id = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               verbose_name="磁盘id")
    instance_id = models.CharField(null=True,
                                   blank=True,
                                   max_length=100,
                                   verbose_name="挂载云服务器ID")
    disk_type_choices = (('system', '系统盘'), ('data', '数据盘'))
    disk_type = models.CharField(choices=disk_type_choices,
                                 max_length=20,
                                 verbose_name="磁盘类型")
    category_choices = (('cloud', '普通云盘'), ('cloud_efficiency', '高效云盘'),
                        ('cloud_ssd', 'SSD盘'), ('cloud_essd', 'ESSD云盘'),
                        ('local_ssd_pro', 'I/O密集型本地盘'), ('local_hdd_pro',
                                                         '吞吐密集型本地盘'),
                        ('local_ssd', '本地固态盘'), ('local_hdd', '本地机械硬盘'))
    category = models.CharField(choices=category_choices,
                                max_length=100,
                                verbose_name="磁盘类别")
    disk_size = models.IntegerField(null=True, blank=True, verbose_name='磁盘大小')
    idc_id = models.SmallIntegerField(null=True,
                                      blank=True,
                                      verbose_name="可用区|机房")
    zone_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="区域")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=500,
                                   verbose_name="磁盘描述")
    create_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=100,
                                   verbose_name="创建时间")
    etached_time = models.CharField(null=True,
                                    blank=True,
                                    max_length=100,
                                    verbose_name="卸载时间")
    expired_time = models.CharField(null=True,
                                    blank=True,
                                    max_length=100,
                                    verbose_name="过期时间")
    run_status = models.SmallIntegerField(null=True,
                                          blank=True,
                                          verbose_name="运行状态")
    tags = models.TextField(null=True, blank=True, verbose_name="tag列表")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class Vpc(models.Model):
    """
    专有网络
    """
    vpc_id = models.CharField(null=True, blank=True, max_length=50)
    vpc_name = models.CharField(null=True,
                                blank=True,
                                max_length=200,
                                verbose_name="名称")
    cidr_block = models.CharField(null=True,
                                  blank=True,
                                  max_length=100,
                                  verbose_name="网段")
    secondary_cidr_blocks = models.CharField(null=True,
                                             blank=True,
                                             max_length=1000,
                                             verbose_name="第二网段")
    vswitch_ids = models.CharField(null=True,
                                   blank=True,
                                   max_length=1000,
                                   verbose_name="交换机ID")
    vrouter_id = models.CharField(null=True,
                                  blank=True,
                                  max_length=50,
                                  verbose_name="路由器ID")
    router_table_ids = models.CharField(null=True,
                                        blank=True,
                                        max_length=1000,
                                        verbose_name="路由表ID")
    nat_gateway_ids = models.CharField(null=True,
                                       blank=True,
                                       max_length=1000,
                                       verbose_name="nat网关")
    resource_group_id = models.CharField(null=True,
                                         blank=True,
                                         max_length=100,
                                         verbose_name="企业资源组ID")
    vpc_status = models.SmallIntegerField(null=True,
                                          blank=True,
                                          verbose_name="状态")  # Available:可用 , Pending:配置中
    creation_time = models.CharField(null=True,
                                     blank=True,
                                     max_length=100,
                                     verbose_name="创建时间")
    zone_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="所属区域")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=500,
                                   verbose_name="描述")
    cen_status = models.CharField(null=True,
                                  blank=True,
                                  max_length=20,
                                  verbose_name="绑定云企业网状态")
    tags = models.CharField(null=True,
                            blank=True,
                            max_length=500,
                            verbose_name="标签列表")
    is_default = models.IntegerField(null=True,
                                     blank=True,
                                     verbose_name="该地域默认VPC")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class Slb(models.Model):
    """
    负责均衡
    """
    vpc_id = models.CharField(null=True,
                              blank=True,
                              max_length=50,
                              verbose_name="所挂vpcid")
    lb_name = models.CharField(null=True,
                               blank=True,
                               max_length=200,
                               verbose_name="负载均衡实例名")
    lb_id = models.CharField(null=True,
                             blank=True,
                             max_length=50,
                             verbose_name="负载均衡实例ID")
    create_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="创建时间")
    pay_type = models.CharField(null=True,
                                blank=True,
                                max_length=50,
                                verbose_name="付费类型")
    address_type = models.CharField(null=True,
                                    blank=True,
                                    max_length=50,
                                    verbose_name="负载均衡实例网络类型")
    network_type = models.CharField(null=True,
                                    blank=True,
                                    max_length=20,
                                    verbose_name="私网负载均衡实例网络类型")
    address_ip_version = models.CharField(null=True,
                                          blank=True,
                                          max_length=50,
                                          verbose_name="IP版本")
    bandwidth = models.CharField(null=True,
                                 blank=True,
                                 max_length=20,
                                 verbose_name="带宽")
    address = models.CharField(null=True,
                               blank=True,
                               max_length=20,
                               verbose_name="负载均衡实例地址")
    master_zone_id = models.SmallIntegerField(null=True,
                                              blank=True,
                                              verbose_name="实例的主可用区ID")
    slave_zone_id = models.SmallIntegerField(null=True,
                                             blank=True,
                                             verbose_name="实例的备可用区ID")
    internet_charge_type = models.CharField(null=True,
                                            blank=True,
                                            max_length=50,
                                            verbose_name="公网类型实例付费方式")
    lb_spec = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               verbose_name="实例规格")

    zone_id = models.SmallIntegerField(null=True,
                                       blank=True,
                                       verbose_name="所属地域")
    vswitch_id = models.CharField(null=True,
                                  blank=True,
                                  max_length=50,
                                  verbose_name="私网交换机ID")
    lb_status = models.SmallIntegerField(null=True,
                                         blank=True,
                                         verbose_name="状态")
    resource_group_id = models.CharField(null=True,
                                         blank=True,
                                         max_length=50,
                                         verbose_name="企业资源组ID")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class IDC(models.Model):
    """idc 信息"""
    zone_id = models.SmallIntegerField(null=True, blank=True, help_text="区域id")
    name = models.CharField(null=True,
                            blank=True,
                            max_length=50,
                            verbose_name="机房名称")
    provider = models.CharField(null=True,
                                blank=True,
                                max_length=50,
                                verbose_name="运营商")
    bandwidth = models.IntegerField(null=True, blank=True, help_text="机房带宽")
    manager = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               help_text="联系人")
    phone = models.CharField(null=True,
                             blank=True,
                             max_length=50,
                             help_text="联系电话")
    address = models.CharField(null=True,
                               blank=True,
                               max_length=50,
                               help_text="机房地址")
    ip_range = models.CharField(null=True,
                                blank=True,
                                max_length=50,
                                help_text="IP地址段")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   help_text="描述信息")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class IdleAssets(models.Model):
    """idle assets"""
    idc = models.SmallIntegerField(null=True, blank=True, help_text="idc id")
    name = models.CharField(null=True,
                            blank=True,
                            max_length=50,
                            verbose_name="资产名称")
    count = models.IntegerField(null=True, blank=True, help_text="闲置资产数量")
    recorder = models.CharField(null=True,
                                blank=True,
                                max_length=50,
                                verbose_name="登记员")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="备注")
    update_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=50,
                                   verbose_name="记录时间")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class CabinetInfo(models.Model):
    """cabinet info"""
    name = models.CharField(null=True,
                            blank=True,
                            max_length=50,
                            verbose_name="机柜名称")
    idc_id = models.SmallIntegerField(null=True,
                                      blank=True,
                                      verbose_name="可用区|机房")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")


class Switch(models.Model):
    switch_id = models.CharField(null=True,
                                 blank=True,
                                 max_length=100,
                                 verbose_name="交换机id")
    name = models.CharField(null=True,
                            blank=True,
                            max_length=100,
                            verbose_name="交换机名称")
    status = models.IntegerField(null=True, blank=True, verbose_name="交换机状态")
    description = models.CharField(null=True,
                                   blank=True,
                                   max_length=800,
                                   verbose_name="交换机描述")
    resource_group_id = models.CharField(null=True,
                                         blank=True,
                                         max_length=50,
                                         verbose_name="企业资源组ID")
    route_table = models.TextField(null=True, blank=True, verbose_name="路由表信息")
    is_default = models.CharField(null=True,
                                  blank=True,
                                  max_length=20,
                                  verbose_name="是否是默认交换机")
    network_acl_id = models.CharField(null=True,
                                      blank=True,
                                      max_length=100,
                                      verbose_name="")
    create_time = models.CharField(null=True,
                                   blank=True,
                                   max_length=100,
                                   verbose_name="创建时间")
    ipv6_cidr_block = models.CharField(null=True,
                                       blank=True,
                                       max_length=100,
                                       verbose_name="ipv6网段")
    cidr_block = models.CharField(null=True,
                                  blank=True,
                                  max_length=100,
                                  verbose_name="ipv4网段")
    idc_id = models.SmallIntegerField(null=True,
                                      blank=True,
                                      verbose_name="可用区|机房")
    ip_address_no = models.IntegerField(null=True,
                                        blank=True,
                                        verbose_name="可用ip数量")
    vpc_id = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="VPCID")
    cloud_resources = models.TextField(null=True, blank=True, verbose_name="")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class BusinessEnvironment(models.Model):
    name = models.CharField(null=True,
                            blank=True,
                            max_length=200,
                            verbose_name="环境名")
    remark = models.CharField(null=True,
                              blank=True,
                              max_length=500,
                              verbose_name="备注")
    job_name = models.CharField(null=True,
                                blank=True,
                                max_length=500,
                                verbose_name="job name")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    c_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="创建时间")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class BusinessProject(models.Model):
    name = models.CharField(null=True,
                            blank=True,
                            max_length=200,
                            verbose_name="项目名")
    remark = models.CharField(null=True,
                              blank=True,
                              max_length=500,
                              verbose_name="备注")
    manager = models.CharField(null=True,
                               blank=True,
                               max_length=100,
                               verbose_name="项目负责人")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    c_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="创建时间")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class BusinessServices(models.Model):
    name = models.CharField(null=True,
                            blank=True,
                            max_length=200,
                            verbose_name="服务名")
    remark = models.CharField(null=True,
                              blank=True,
                              max_length=500,
                              verbose_name="备注")
    manager = models.CharField(null=True,
                               blank=True,
                               max_length=100,
                               verbose_name="服务负责人")
    rel_project = models.IntegerField(null=True,
                                      blank=True,
                                      verbose_name="关联项目")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    c_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="创建时间")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")
    type_choices = ((1, 'apis'), (2, 'services'), (3, 'web'))
    service_type = models.IntegerField(choices=type_choices,
                                       verbose_name="服务类型",
                                       default=1)


class ServiceToEnv(models.Model):
    service_id = models.IntegerField(null=True,
                                     blank=True,
                                     verbose_name="服务id")
    env_id = models.IntegerField(null=True, blank=True, verbose_name="环境id")
    rel_ips = models.CharField(null=True,
                               blank=True,
                               max_length=500,
                               verbose_name="关联服务器id")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    c_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="创建时间")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")


class DnsRecords(models.Model):  # 域名解析记录
    domain_id = models.IntegerField(null=True, blank=True, verbose_name="域名id")
    line_choices = (('default', '默认'), ('telecom', '电信'), ('unicom', '联通'),
                    ('mobile', '移动'), ('oversea', '境外'), ('edu', '教育网'),
                    ('drpeng', '鹏博士'), ('btvn', '广电网'))
    line = models.CharField(choices=line_choices,
                            max_length=20,
                            verbose_name="解析线路")
    locked = models.CharField(null=True,
                              blank=True,
                              max_length=20,
                              verbose_name="解析记录锁定状态")
    priority = models.IntegerField(null=True,
                                   blank=True,
                                   verbose_name="MX记录优先级")  # 仅MX,SRV,URI
    RR = models.CharField(null=True,
                          blank=True,
                          max_length=100,
                          verbose_name="主机记录")
    record_id = models.CharField(null=True,
                                 blank=True,
                                 max_length=50,
                                 verbose_name="解析记录ID")
    remark = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="备注")
    status_id = models.IntegerField(null=True, blank=True,
                                    verbose_name="状态")  # ENABLE
    ttl = models.IntegerField(null=True, blank=True, verbose_name="生存时间")
    type = models.CharField(null=True,
                            blank=True,
                            max_length=20,
                            verbose_name="记录类型")
    value = models.CharField(null=True,
                             blank=True,
                             max_length=100,
                             verbose_name="记录值")
    weight = models.CharField(null=True,
                              blank=True,
                              max_length=20,
                              verbose_name="均衡权重")
    u_time = models.CharField(null=True,
                              blank=True,
                              max_length=100,
                              verbose_name="更新入库时间")
    del_tag = models.SmallIntegerField(default=0, help_text="删除标识")
    belong_to = models.CharField(null=True,
                                 blank=True,
                                 max_length=100,
                                 verbose_name="域名解析归属")
    proxy_choices = ((True, '已代理'), (False, '仅DNS'))
    proxied = models.BooleanField(choices=proxy_choices,
                                  null=True,
                                  blank=True,
                                  verbose_name='代理状态')  # cloudflare
