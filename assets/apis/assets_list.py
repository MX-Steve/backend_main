import logging
import os
import sys
from django.http import JsonResponse
from assets import models
from utils import aliyun
from assets.serializers import *
from utils import baseview
from django.db.models import Count, Q
import paramiko
from utils.util import now, time_trans, gen_shortuuid, LinuxRemoteConn
from audit.apis.audit import PutAudit
from utils.auth import auth
from utils.cloudflare import CloudFlareApi
from django.conf import settings

logger = logging.getLogger("ttool.app")

SHELL_CMD_DICT = {
    'hostname':
    'hostname',
    'cpu':
    'cat /proc/cpuinfo| grep "processor"| wc -l',
    'memory':
    "free -m|head -2|tr -s ' ' | tail -l|cut -d' ' -f2 | awk 'NR==2{print}'"
}

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')
ClOUDFLARE_TOKEN = settings.ALICLOUD_TOKEN


# Function
def remote_do_cmd(**kwargs):
    cmd_ret_dict = {}
    host_ip = kwargs.get('ip_address', None)
    username = kwargs.get('username', 'root')
    passwd = kwargs.get('password', None)
    port = kwargs.get('port', 22)
    private_key = kwargs.get('authentication_type', None)
    shell_cmd = kwargs.get('shell_command',
                           None)  # dict{'hostname':'echo $(hostname)'}
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if private_key:
            private = paramiko.RSAKey.from_private_key_file(passwd)
            ssh_client.connect(hostname=host_ip,
                               port=port,
                               username=username,
                               pkey=private)
        else:
            ssh_client.connect(hostname=host_ip,
                               port=port,
                               username=username,
                               password=passwd)
        shell_command = {shell_cmd} if shell_cmd else SHELL_CMD_DICT
        for cmd_item in shell_command:
            stdin, stdout, stderr = ssh_client.exec_command(
                shell_command[cmd_item])
            stderr_info = stderr.read().decode('utf8')
            if stderr_info == '':
                stdout_info = stdout.read().decode('utf8').split('\n')[0]
                cmd_ret_dict.update({cmd_item: stdout_info})
            else:
                logger.error(stderr_info)
                return False
        ssh_client.close()
        return cmd_ret_dict
    except:
        err = '%s [%s] happend on %s line at %s' % (
            sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno,
            os.path.basename(__file__))
        logger.error(err)


def query_device_type_id(name: str):
    name = name.strip()
    query_device_type = models.DeviceType.objects.filter(del_tag=0, name=name)
    if query_device_type:
        device_type_id = query_device_type[0].id
    else:
        msg = {'未找到此%s的设备ID，请联系运维'}
        return False, msg
    return device_type_id


def op_common_sql(**kwargs):
    region = kwargs.get('region', None)
    zone = kwargs.get('zone', None)
    run_status = kwargs.get('run_status', None)
    device_id = kwargs.get('device_id', None)
    provider = kwargs.get('provider', None)
    region_id = ''
    zone_id = ''
    status_id = ''
    # 区域
    if region:
        query_zone = models.ZoneInfo.objects.filter(name=region,
                                                    del_tag=0).exists()
        if not query_zone:
            models.ZoneInfo.objects.create(name=region,
                                           description='ali regions')
        region_id = models.ZoneInfo.objects.filter(name=region,
                                                   del_tag=0)[0].id

    # 机房|可用区
    if region and zone and provider:
        query_idc = models.IDC.objects.filter(name=zone,
                                              del_tag=0,
                                              provider=provider).exists()
        if not query_idc:
            models.IDC.objects.create(zone_id=region_id,
                                      name=zone,
                                      provider=provider)
        zone_id = models.IDC.objects.filter(name=zone,
                                            del_tag=0,
                                            provider=provider)[0].id
    # 状态
    if run_status and device_id:
        query_status = models.DeviceStatus.objects.filter(
            description__contains=',' + run_status + ',',
            del_tag=0,
            type_id=device_id)
        if not query_status:
            msg = {'未查询到此%s的状态信息，请联系运维'}
            return False, msg
        status_id = query_status[0].id
    msg = {'idc_id': zone_id, 'zone_id': region_id, 'status_id': status_id}
    logger.info(msg)
    return msg


def cron_sync_ali_ecs():  # 阿里云服务器
    ecs_infos = aliyun.ECS().get_ecs()
    sn_list = []
    server_info = {}
    server_type = models.DeviceType.objects.filter(
        del_tag=0, name='云服务器').first().id  # 设备类型ID
    for ecs in ecs_infos:
        sn_id = ecs.get('sn', None)
        sn_list.append(sn_id)
        ostype = ecs.get('ostype', None).lower() if ecs.get('ostype',
                                                            None) else None
        # 数库optional字段
        hostname = ecs.get('hostname', None)
        instance_id = ecs.get('instance_id', None)
        os_name = ecs.get('os', None)
        specs = ecs.get('specs', None)
        public_ip = ecs.get('public_ip', None)
        mac_address = ecs.get('mac', None)
        cpu = ecs.get('cpu', None)
        memory = ecs.get('memory', None)
        create_time = time_trans(ecs.get('create_time', None))
        expiration_time = time_trans(ecs.get('expiration_time', None))
        charge_type = ecs.get('charge_type', None)
        net_charge_type = ecs.get('net_charge_type', None)
        description = ecs.get('comment', None)
        ext = {
            'hostname': hostname,
            'instance_id': instance_id,
            'os_name': os_name,
            'specs': specs,
            'public_ip': public_ip,
            'mac_address': mac_address,
            'cpu': cpu,
            'memory': memory,
            'create_time': create_time,
            'expiration_time': expiration_time,
            'charge_type': charge_type,
            'net_charge_type': net_charge_type,
            'description': description
        }
        # 查询映射表
        zone = ecs.get('zone', None)
        region = ecs.get('region', None)
        status = ecs.get('status', None)
        query_ret = op_common_sql(region=region,
                                  zone=zone,
                                  run_status=status,
                                  device_id=server_type,
                                  provider='alicloud')
        # 落库参数
        server_info['status_id'] = query_ret['status_id']
        server_info['zone_id'] = query_ret['zone_id']
        server_info['idc_id'] = query_ret['idc_id']
        server_info['optional'] = json.dumps(ext) if ext else {}
        server_info['instance_name'] = ecs.get('instance_name', None)
        server_info['ip_address'] = ecs.get('host_ip', None)
        server_info['os_type'] = 1 if 'linux' in ostype else 2
        server_info['u_time'] = now()
        # CLOUD ECS落库
        models.Machine.objects.update_or_create(server_type=server_type,
                                                sn_id=sn_id,
                                                del_tag=0,
                                                defaults=server_info)
    models.Machine.objects.filter(
        server_type=server_type,
        del_tag=0).exclude(sn_id__in=sn_list).update(del_tag=1)


def cron_sync_local_machine():  # 本地物理服务器
    device_type = models.DeviceType.objects.filter(del_tag=0,
                                                   name='物理机').first()
    query_phy_server = models.Machine.objects.filter(
        del_tag=0,
        device_type=device_type.id).values('ip_address', 'authentication_type',
                                           'username', 'password', 'port')

    update_failed_ips = []
    for server_item in query_phy_server:
        try:
            if server_item['authentication_type'] == 1:  # 密码
                do_cmd = LinuxRemoteConn(
                    host_ip=server_item['ip_address'],
                    username=server_item['username'],
                    port=server_item['port'],
                    password=server_item['password'],
                )
            else:
                do_cmd = LinuxRemoteConn(
                    host_ip=server_item['ip_address'],
                    username=server_item['username'],
                    port=server_item['port'],
                    password=server_item['password'],
                    auth_type=server_item['authentication_type'])
            cmd_ret_dict = {}
            for x, y in SHELL_CMD_DICT.items():
                cmd_rps = do_cmd.run_cmd(y)
                cmd_ret = list(filter(None, cmd_rps))
                if cmd_ret:
                    if len(cmd_ret) == 1:
                        cmd_ret = cmd_ret[0]
                    cmd_ret_dict.update({x: cmd_ret})
            if cmd_ret_dict:  # 落库
                query_machine = models.Machine.objects.filter(
                    ip_address=server_item['ip_address'],
                    server_type=device_type,
                    del_tag=0)
                ext = json.loads(query_machine[0].optional
                                 ) if query_machine[0].optional else None
                optional = json.dumps(ext.update(cmd_ret_dict))
                query_machine.update(optional=optional)
        except:
            update_failed_ips.append(server_item['ip_address'])
            pass


def cron_sync_ali_rds():
    rds_infos = aliyun.RDS().get_rds()
    rds_id_list = []
    new_rds_list = []
    device_id = query_device_type_id('数据库')
    for rds in rds_infos:
        rds_id_list.append(rds['instance_id'])
        run_status = rds['status']
        region = rds['region']
        zone = rds['zone']
        specs = json.dumps(rds['specs']) if rds['specs'] else None
        # 查询映射表
        query_ret = op_common_sql(region=region,
                                  zone=zone,
                                  run_status=run_status,
                                  provider='alicloud',
                                  device_id=device_id)
        zone_id = query_ret['zone_id']
        idc_id = query_ret['idc_id']
        status_id = query_ret['status_id']
        # rds
        post_query_rds = models.RDS.objects.filter(rds_id=rds['instance_id'],
                                                   del_tag=0)
        if post_query_rds:
            post_query_rds.update(rds_name=rds['instance_name'],
                                  run_status=status_id,
                                  expiration_time=time_trans(
                                      rds['expiration_time']),
                                  engine=rds['engine'],
                                  engine_version=rds['engine_version'],
                                  conn_address=rds['host_address'],
                                  port=rds['port'],
                                  charge_type=rds['charge_type'],
                                  idc_id=idc_id,
                                  zone_id=zone_id,
                                  remark=rds['comment'],
                                  specs=specs,
                                  u_time=now())
        else:
            new_rds_list.append(
                models.RDS(rds_id=rds['instance_id'],
                           rds_name=rds['instance_name'],
                           run_status=status_id,
                           create_time=time_trans(rds['create_time']),
                           expiration_time=time_trans(rds['expiration_time']),
                           engine=rds['engine'],
                           engine_version=rds['engine_version'],
                           conn_address=rds['host_address'],
                           port=rds['port'],
                           charge_type=rds['charge_type'],
                           idc_id=idc_id,
                           zone_id=zone_id,
                           remark=rds['comment'],
                           specs=specs,
                           u_time=now()))
    if new_rds_list:
        models.RDS.objects.bulk_create(new_rds_list)
    models.RDS.objects.filter(del_tag=0).exclude(
        rds_id__in=rds_id_list).update(del_tag=1)


def cron_sync_ali_disk():
    # aliyun
    disk_infos = aliyun.ECS().get_disk()
    disk_id_list = []
    new_disk_list = []
    device_id = query_device_type_id('磁盘')
    for disk in disk_infos:
        disk_id_list.append(disk['DiskId'])
        # 查询映射
        query_ret = op_common_sql(zone=disk['ZoneId'],
                                  region=disk['RegionId'],
                                  run_status=disk['Status'],
                                  device_id=device_id,
                                  provider='alicloud')
        idc_id = query_ret['idc_id']
        zone_id = query_ret['zone_id']
        status_id = query_ret['status_id']
        # disk
        tags = json.dumps(disk['Tags']['Tag']) if disk['Tags']['Tag'] else None
        post_query_disk = models.Disk.objects.filter(disk_id=disk['DiskId'],
                                                     del_tag=0)
        if not post_query_disk:
            new_disk_list.append(
                models.Disk(disk_id=disk['DiskId'],
                            disk_name=disk['DiskName'],
                            instance_id=disk['InstanceId'],
                            disk_type=disk['Type'],
                            category=disk['Category'],
                            disk_size=disk['Size'],
                            idc_id=idc_id,
                            zone_id=zone_id,
                            description=disk['Description'],
                            create_time=time_trans(disk['CreationTime']),
                            expired_time=time_trans(disk['ExpiredTime']),
                            run_status=status_id,
                            tags=tags,
                            u_time=now()))
        else:
            post_query_disk.update(disk_name=disk['DiskName'],
                                   instance_id=disk['InstanceId'],
                                   disk_type=disk['Type'],
                                   category=disk['Category'],
                                   disk_size=disk['Size'],
                                   idc_id=idc_id,
                                   zone_id=zone_id,
                                   description=disk['Description'],
                                   expired_time=time_trans(
                                       disk['ExpiredTime']),
                                   run_status=status_id,
                                   tags=tags,
                                   u_time=now())
    if new_disk_list:
        models.Disk.objects.bulk_create(new_disk_list)
    models.Disk.objects.filter(del_tag=0).exclude(
        disk_id__in=disk_id_list).update(del_tag=1)
    return JsonResponse({'code': 200, 'data': {}, 'msg': 'success'})


def cron_sync_ali_domain():
    domain_infos = aliyun.Domain().get_domainListInfo()
    domain_dict = {}
    domain_name_list = []
    device_id = query_device_type_id('域名')
    belong_to = 'alibaba cloud computing'
    # 域名
    for domain in domain_infos:
        # domain_id_list.append(domain['domain_id'])
        domain_name_list.append(domain['name'])
        status_id = op_common_sql(run_status=str(domain['domain_status']),
                                  device_id=device_id)['status_id']
        domain_dict['domain_id'] = domain['domain_id']
        domain_dict['domain_name'] = domain['name']
        domain_dict['registrant_type'] = domain['registrant_type']
        domain_dict['domain_type'] = domain['domain_type']
        domain_dict['email'] = domain['email']
        domain_dict['registration_date'] = domain['registration_date']
        domain_dict['expiration_date'] = domain['expiration_date']
        domain_dict['domain_status'] = status_id
        domain_dict['domain_owner'] = domain['owner']
        domain_dict['belong_to'] = belong_to
        domain_dict['u_time'] = now()
        # query_domain = models.Domain.objects.filter(
        #     domain_name=domain['name'], del_tag=0)
        # if not query_domain:
        #     new_domain_list.append(
        #         models.Domain(**domain_dict))
        # else:
        #     domain_dict.pop('domain_name')
        #     query_domain.update(**domain_dict)
        # if new_domain_list:
        #     models.Domain.objects.bulk_create(new_domain_list)
        models.Domain.objects.update_or_create(defaults=domain_dict,
                                               del_tag=0,
                                               domain_name=domain['name'],
                                               belong_to=belong_to)
    models.Domain.objects.filter(del_tag=0, belong_to=belong_to).exclude(
        domain_name__in=domain_name_list).update(del_tag=1)


def cron_sync_ali_oss():
    oss_infos = aliyun.OSS().get_bucket()
    oss_name_list = []
    new_oss_list = []
    for oss in oss_infos:
        oss_name_list.append(oss['name'])
        query_oss = models.Oss.objects.filter(oss_name=oss['name'], del_tag=0)
        if not query_oss:
            new_oss_list.append(
                models.Oss(oss_name=oss['name'],
                           location=oss['location'],
                           storage_class=oss['storage_class'],
                           extranet_endpoint=oss['extranet_endpoint'],
                           intranet_endpoint=oss['intranet_endpoint'],
                           create_time=time_trans(oss['creation_date']),
                           grant=oss['grant'],
                           data_redundancy_type=oss['data_redundancy_type'],
                           u_time=now()))
        else:
            query_oss.update(location=oss['location'],
                             storage_class=oss['storage_class'],
                             extranet_endpoint=oss['extranet_endpoint'],
                             intranet_endpoint=oss['intranet_endpoint'],
                             data_redundancy_type=oss['data_redundancy_type'],
                             grant=oss['grant'],
                             u_time=now())
    if new_oss_list:
        models.Oss.objects.bulk_create(new_oss_list)
    models.Oss.objects.filter(del_tag=0).exclude(
        oss_name__in=oss_name_list).update(del_tag=1)


def cron_sync_ali_vpc():
    vpc_infos = aliyun.Vpc().get_vpc()['vpc']
    vpc_id_list = []
    new_vpc_list = []
    device_id = query_device_type_id('Vpc')
    for vpc in vpc_infos:
        vpc_id_list.append(vpc['vpc_id'])
        region = vpc['region_id']
        vpc_status = vpc['status']
        query_ret = op_common_sql(region=region,
                                  run_status=vpc_status,
                                  device_id=device_id)
        region_id = query_ret['zone_id']
        status_id = query_ret['status_id']
        # vpc
        query_vpc = models.Vpc.objects.filter(del_tag=0, vpc_id=vpc['vpc_id'])
        if not query_vpc:
            new_vpc_list.append(
                models.Vpc(vpc_id=vpc['vpc_id'],
                           vpc_name=vpc['vpc_name'],
                           cidr_block=vpc['cidr_block'],
                           secondary_cidr_blocks=vpc['secondary_cidr_blocks'],
                           vswitch_ids=vpc['vswitch_ids'],
                           vrouter_id=vpc['vrouter_id'],
                           router_table_ids=vpc['router_table_ids'],
                           nat_gateway_ids=vpc['nat_gateway_ids'],
                           resource_group_id=vpc['resource_group_id'],
                           vpc_status=status_id,
                           creation_time=time_trans(vpc['creation_time']),
                           zone_id=region_id,
                           description=vpc['description'],
                           u_time=now()))
        else:
            query_vpc.update(
                vpc_name=vpc['vpc_name'],
                cidr_block=vpc['cidr_block'],
                secondary_cidr_blocks=vpc['secondary_cidr_blocks'],
                vswitch_ids=vpc['vswitch_ids'],
                vrouter_id=vpc['vrouter_id'],
                router_table_ids=vpc['router_table_ids'],
                nat_gateway_ids=vpc['nat_gateway_ids'],
                resource_group_id=vpc['resource_group_id'],
                vpc_status=status_id,
                zone_id=region_id,
                description=vpc['description'],
                u_time=now())
    if new_vpc_list:
        models.Vpc.objects.bulk_create(new_vpc_list)
    models.Vpc.objects.filter(del_tag=0).exclude(
        vpc_id__in=vpc_id_list).update(del_tag=1)
    # vswitch
    vswitch_infos = aliyun.Vpc().get_vpc()['vswitch']
    vswitch_id_list = []
    new_vswitch_list = []
    device_id = query_device_type_id('交换机')
    for vswitch in vswitch_infos:
        vswitch_id_list.append(vswitch['vswitch_id'])
        zone = vswitch['zone_id']
        if "cn" in zone.split('-')[0]:
            region = zone[:-2]
        else:
            region = zone[:-1]
        run_status = vswitch['status']
        sql_ret = op_common_sql(region=region,
                                zone=zone,
                                run_status=run_status,
                                device_id=device_id,
                                provider='alicloud')
        # zone_id = sql_ret['zone_id']
        idc_id = sql_ret['idc_id']
        status_id = sql_ret['status_id']
        route_table = json.dumps(
            vswitch['route_table']) if vswitch['route_table'] else None
        cloud_resources = json.dumps(
            vswitch['cloud_resources']) if vswitch['cloud_resources'] else None
        # vswtich
        query_switch = models.Switch.objects.filter(
            del_tag=0, switch_id=vswitch['vswitch_id'])
        if not query_switch:
            new_vswitch_list.append(
                models.Switch(switch_id=vswitch['vswitch_id'],
                              name=vswitch['vswitch_name'],
                              status=status_id,
                              description=vswitch['description'],
                              resource_group_id=vswitch['resource_group_id'],
                              route_table=route_table,
                              is_default=vswitch['is_default'],
                              network_acl_id=vswitch['network_acl_id'],
                              create_time=time_trans(vswitch['create_time']),
                              cidr_block=vswitch['cidr_block'],
                              idc_id=idc_id,
                              ip_address_no=vswitch['ip_address_count'],
                              vpc_id=vswitch['vpc_id'],
                              cloud_resources=cloud_resources,
                              u_time=now()))
        else:
            query_switch.update(name=vswitch['vswitch_name'],
                                status=status_id,
                                description=vswitch['description'],
                                resource_group_id=vswitch['resource_group_id'],
                                route_table=route_table,
                                is_default=vswitch['is_default'],
                                network_acl_id=vswitch['network_acl_id'],
                                cidr_block=vswitch['cidr_block'],
                                idc_id=idc_id,
                                ip_address_no=vswitch['ip_address_count'],
                                vpc_id=vswitch['vpc_id'],
                                cloud_resources=cloud_resources,
                                u_time=now())
    if new_vswitch_list:
        models.Switch.objects.bulk_create(new_vswitch_list)
    models.Switch.objects.filter(del_tag=0).exclude(
        switch_id__in=vswitch_id_list).update(del_tag=1)


def cron_sync_ali_cdn():
    cdn_infos = aliyun.Cdn().get_cdn_info()
    cdn_name_list = []
    new_cdn_list = []
    device_id = query_device_type_id('CDN')
    for cdn in cdn_infos:
        cdn_name = cdn['cname']
        cdn_name_list.append(cdn_name)
        domain_status = cdn['domain_status']
        status_id = op_common_sql(run_status=domain_status,
                                  device_id=device_id)['status_id']
        source = json.dumps(cdn['sources']) if cdn['sources'] else None
        query_cdn = models.CDN.objects.filter(del_tag=0, cdn_name=cdn_name)
        if not query_cdn:
            new_cdn_list.append(
                models.CDN(domain_name=cdn['domain_name'],
                           cdn_name=cdn['cname'],
                           ssl_protocol=cdn['ssl_protocol'],
                           description=cdn['description'],
                           coverage=cdn['coverage'],
                           resource_group_id=cdn['resource_group_id'],
                           domain_status=status_id,
                           cdn_type=cdn['cdn_type'],
                           gmt_created=time_trans(cdn['gmt_created']),
                           gmt_modified=time_trans(cdn['gmt_modified']),
                           source=source,
                           u_time=now()))
        else:
            query_cdn.update(ssl_protocol=cdn['ssl_protocol'],
                             description=cdn['description'],
                             coverage=cdn['coverage'],
                             resource_group_id=cdn['resource_group_id'],
                             domain_status=status_id,
                             cdn_type=cdn['cdn_type'],
                             gmt_created=cdn['gmt_created'],
                             gmt_modified=time_trans(cdn['gmt_modified']),
                             source=source,
                             u_time=now())
    if new_cdn_list:
        models.CDN.objects.bulk_create(new_cdn_list)
    models.CDN.objects.filter(del_tag=0).exclude(
        cdn_name__in=cdn_name_list).update(del_tag=1)


def cron_sync_ali_slb():
    slb_infos = aliyun.Slb().get_slb()
    slb_id_list = []
    new_slb_list = []
    device_id = query_device_type_id('Slb')
    for slb in slb_infos:
        slb_id_list.append(slb['slb_id'])
        master_idc = slb['master_zone_id']
        slave_idc = slb['slave_zone_id']
        slb_status = slb['slb_status']
        slb_zone = slb['slb_region_id']
        master_idc_id = op_common_sql(region=slb_zone,
                                      zone=master_idc,
                                      provider='alicloud').get('idc_id')
        slave_idc_id = op_common_sql(region=slb_zone,
                                     zone=slave_idc,
                                     provider='alicloud').get('idc_id')
        slb_status = op_common_sql(run_status=slb_status,
                                   device_id=device_id).get('status_id')
        slb_zone_id = op_common_sql(region=slb_zone).get('zone_id')
        # slb
        query_slb = models.Slb.objects.filter(lb_id=slb['slb_id'], del_tag=0)
        if not query_slb:
            new_slb_list.append(
                models.Slb(lb_id=slb['slb_id'],
                           lb_name=slb['slb_name'],
                           vpc_id=slb['vpc_id'],
                           create_time=time_trans(slb['create_time']),
                           pay_type=slb['pay_type'],
                           address_type=slb['address_type'],
                           network_type=slb['network_type'],
                           address_ip_version=slb['address_version'],
                           bandwidth=slb['bandwidth'],
                           address=slb['address'],
                           master_zone_id=master_idc_id,
                           slave_zone_id=slave_idc_id,
                           internet_charge_type=slb['net_charge_type'],
                           lb_spec=slb['slb_spec'],
                           zone_id=slb_zone_id,
                           vswitch_id=slb['vswitch_id'],
                           lb_status=slb_status,
                           resource_group_id=slb['resource_grp_id'],
                           u_time=now()))
        else:
            query_slb.update(lb_name=slb['slb_name'],
                             vpc_id=slb['vpc_id'],
                             pay_type=slb['pay_type'],
                             address_type=slb['address_type'],
                             network_type=slb['network_type'],
                             address_ip_version=slb['address_version'],
                             bandwidth=slb['bandwidth'],
                             address=slb['address'],
                             master_zone_id=master_idc_id,
                             slave_zone_id=slave_idc_id,
                             internet_charge_type=slb['net_charge_type'],
                             lb_spec=slb['slb_spec'],
                             zone_id=slb_zone_id,
                             vswitch_id=slb['vswitch_id'],
                             lb_status=slb_status,
                             resource_group_id=slb['resource_grp_id'],
                             u_time=now())
    if new_slb_list:
        models.Slb.objects.bulk_create(new_slb_list)
    models.Slb.objects.filter(del_tag=0).exclude(lb_id__in=slb_id_list).update(
        del_tag=1)


def cron_sync_ali_domain_record():
    # 域名解析记录
    belong_to = 'alibaba cloud computing'
    domain_name_list = list(
        models.Domain.objects.filter(
            del_tag=0, belong_to=belong_to).values_list('domain_name',
                                                        flat=True))
    if domain_name_list:
        device_id = query_device_type_id('Dns')
        record_id_list = []
        for name_item in domain_name_list:
            ns_info = aliyun.DomainRecords(
                domain_name=name_item).get_domain_ns()
            all_ali_dns = ns_info['AllAliDns']
            include_ali_dns = ns_info['IncludeAliDns']
            domain_id = models.Domain.objects.filter(
                domain_name=name_item).values('id')[0]['id']
            domain_records = aliyun.DomainRecords(
                domain_name=name_item).get_dns_records_info()
            if domain_records and (all_ali_dns or include_ali_dns):
                for d_record in domain_records:
                    record_id_list.append(d_record['record_id'])
                    status_id = op_common_sql(
                        device_id=device_id,
                        run_status=d_record['status'])['status_id']
                    d_record.pop('status')
                    d_record.pop('domain_name')
                    d_record['u_time'] = now()
                    d_record['status_id'] = status_id
                    d_record['belong_to'] = belong_to
                    d_record['domain_id'] = domain_id
                    # query_record = models.DnsRecords.objects.filter(record_id=d_record['record_id'], del_tag=0,
                    #                                                 belong_to=belong_to)
                    # if not query_record:
                    #     d_record['domain_id'] = domain_id
                    #     models.DnsRecords.objects.create(**d_record)
                    # else:
                    #     query_record.update(**d_record)
                    models.DnsRecords.objects.update_or_create(
                        defaults=d_record,
                        record_id=d_record['record_id'],
                        del_tag=0,
                        belong_to=belong_to)
        models.DnsRecords.objects.filter(
            del_tag=0, belong_to=belong_to).exclude(
                record_id__in=record_id_list).update(del_tag=1)


def cron_sync_cloudflare_domain():
    cf = CloudFlareApi(token=ClOUDFLARE_TOKEN)
    zones = cf.get_zone()
    data = {}
    zone_names_list = []
    device_id = query_device_type_id('域名')
    data['domain_status'] = op_common_sql(device_id=device_id,
                                          run_status='3')['status_id']

    for zone in zones:
        if zone and zone['status'] == 'active':
            belong_to = 'alibaba cloud computing' if 'alibaba' in zone[
                'original_registrar'] else zone['original_registrar']
            zone_names_list.append(zone['name'])
            data['domain_name'] = zone['name']
            data['cf_zone_id'] = zone['id']
            data['belong_to'] = belong_to
            models.Domain.objects.update_or_create(defaults=data,
                                                   del_tag=0,
                                                   domain_name=zone['name'],
                                                   belong_to=belong_to)
    models.Domain.objects.filter(del_tag=0, belong_to='CloudFlare').exclude(
        domain_name__in=zone_names_list).update(
            del_tag=1)  # 仅删除cloudflare申请的domain


def cron_sync_cloudflare_domain_record():
    # dns record
    belong_to = 'CloudFlare'
    zone_info = models.Domain.objects.filter(~Q(cf_zone_id=''),
                                             cf_zone_id__isnull=False,
                                             del_tag=0)
    zone_info_list = []
    if zone_info:
        for i in zone_info:
            zone_info_list.append({
                'domain_id': i.id,
                'zone_id': i.cf_zone_id,
                'domain_name': i.domain_name
            })
    cf = CloudFlareApi(token=ClOUDFLARE_TOKEN)
    record_data = {}
    if zone_info_list:
        record_type_id = query_device_type_id('Dns')
        record_ids_list = []
        for zone in zone_info_list:
            record_data['domain_id'] = zone['domain_id']
            record_infos = cf.get_dns_records(zone_id=zone['zone_id'])
            if record_infos:
                for record in record_infos:
                    record_ids_list.append(record['id'])
                    record_data['record_id'] = record['id']
                    if record['name'] != zone['domain_name']:
                        record_data['RR'] = record['name'][:-(
                            len(zone['domain_name']) + 1)]
                    else:
                        record_data['RR'] = record['name']
                    record_data['value'] = record['content']
                    record_data['type'] = record['type']
                    record_data['locked'] = record['locked']
                    record_data[
                        'ttl'] = 600 if record['ttl'] == 1 else record['ttl']
                    priority = record.get('priority', None)
                    if priority:
                        record_data['priority'] = priority
                    else:
                        record_data['priority'] = 10
                        record_data.pop('priority')
                    proxied = record['proxied']
                    record_data['proxied'] = proxied  # 代理状态
                    record_data['belong_to'] = belong_to
                    record_data['status_id'] = op_common_sql(
                        device_id=record_type_id,
                        run_status='ENABLE')['status_id']
                    record_data['u_time'] = now()
                    models.DnsRecords.objects.update_or_create(
                        defaults=record_data,
                        del_tag=0,
                        record_id=record['id'])
        models.DnsRecords.objects.filter(
            del_tag=0, belong_to=belong_to).exclude(
                record_id__in=record_ids_list).update(del_tag=1)


class MachineListView(baseview.BaseView):
    @auth("assets.machine-list.view")
    def get(self, request, args=None):
        """

        :param request:  idc_id,id_address,server_type,status_id
        :param args:
        :return:
        """
        res_type = request.GET.get('type')
        if res_type == "get_all_machines":
            idc_id = int(request.GET.get('idc_id')) if request.GET.get(
                'idc_id') else None
            ip_address = request.GET.get('ip_address')
            server_type = request.GET.get('server_type')
            status_id = request.GET.get('status_id')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if idc_id:
                q.children.append(('idc_id', idc_id))
            if ip_address:
                q.children.append(('ip_address__contains', ip_address))
            if server_type:
                q.children.append(('server_type', server_type))
            if status_id:
                q.children.append(('status_id', status_id))
            machine_infos = models.Machine.objects.filter(q)
            total = machine_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize

            machine_show_infos = machine_infos[start:end].values(
                'id', 'sn_id', 'zone_id', 'instance_name', 'idc_id',
                'status_id', 'server_type', 'ip_address', 'os_type',
                'username', 'authentication_type', 'port', 'password',
                'sudo_password', 'optional', 'u_time')
            data = []
            for item in machine_show_infos:
                data.append({
                    'id': item['id'],
                    'sn_id': item['sn_id'],
                    'zone_id': item['zone_id'],
                    'idc_id': item['idc_id'],
                    'instance_name': item['instance_name'],
                    'ip_address': item['ip_address'],
                    'status_id': item['status_id'],
                    'server_type': item['server_type'],
                    'os_type': item['os_type'],
                    'username': item['username'],
                    'authentication_type': item['authentication_type'],
                    'port': item['port'],
                    'password': item['password'],
                    'sudo_password': item['sudo_password'],
                    'optional': item['optional'],
                    'u_time': item['u_time']
                })
            msg = {
                'code': 200,
                'data': {
                    'machines': data,
                    "total": total
                },
                'msg': 'success'
            }

        elif res_type == "machine_details":
            id = request.GET.get('id')
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_machine_detail = models.Machine.objects.filter(id=id, del_tag=0)
            if query_machine_detail:
                serializer = models.MachineSerializers(query_machine_detail,
                                                many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': '未查询到此ID:%s相关服务器' % id
                }
        elif res_type == "ins_details":
            ins_id = request.GET.get('instance_id', None)
            if not ins_id:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': 'instance id required'
                }
                return JsonResponse(msg)
            else:
                query_machine = models.Machine.objects.filter(
                    del_tag=0, server_type=2).values('id', 'optional')  # 查询云盘
                msg = {'code': 200, 'data': [], 'msg': 'success'}
                if query_machine:
                    for ins in query_machine:
                        if json.loads(
                                ins['optional'])['instance_id'] == ins_id:
                            ins_info = MachineSerializers(
                                models.Machine.objects.filter(id=ins['id']),
                                many=True)
                            msg['data'] = ins_info.data
                            break
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.machine-list.add|assets.machine-input.add")
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "获取成功"}
        data = request.data
        op_type = data.get('type')
        if op_type == 'machine_add':
            post_query_machine = models.Machine.objects.filter(
                instance_name=data["instance_name"], del_tag=0)
            data.pop('type')
            if not post_query_machine:
                models.Machine.objects.create(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息添加成功！'}
                PutAudit(request, msg)  # 审计
            else:
                msg = {'code': 10001, 'data': {}, 'msg': '服务器名称已存在，请勿重复添加！'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': 'op_type参数有误'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("assets.machine-list.edit")
    def put(self, request, args=None):
        data = request.data
        id = int(data['id'])
        instance_name = data['instance_name']
        optional = data.get('optional', None)
        if optional:
            data['optional'] = json.dumps(optional)
        put_query_machine = models.Machine.objects.filter(id=id, del_tag=0)
        if put_query_machine:
            data['u_time'] = now()
            query_machine_id = models.Machine.objects.filter(
                instance_name=instance_name, del_tag=0)
            machine_id = query_machine_id[0].id if query_machine_id else None
            if not machine_id:
                put_query_machine.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息修改成功'}
            elif machine_id == id:
                put_query_machine.update(**data)
                msg = {'code': 200, 'data': {}, 'msg': '服务器信息修改成功'}
            else:
                msg = {'code': 10002, 'data': {}, 'msg': '服务器名称已存在，请勿重复添加！'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未查询到服务器ID,请联系相关运维！'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)

    @auth("assets.machine-list.del")
    def delete(self, request, args=None):
        data = request.data
        if "id" not in data:
            return JsonResponse({
                'code': 10003,
                'data': {},
                'msg': "id required."
            })
        not_found_machine = []
        bind_service = []
        have_virts = []
        ids = data['id']  # list
        for m_id in ids:
            query_virt = models.Machine.objects.filter(del_tag=0,
                                                rel_server_id=m_id).exists()
            if query_virt:
                have_virts.append(m_id)
        if have_virts:
            msg = {
                'code': 10003,
                'data': {},
                'msg': "ID为%s的服务器有虚拟机,请先删除虚拟机" % have_virts
            }
            PutAudit(request, msg)  # 审计
            return JsonResponse(msg)
        for item in ids:
            query_machine = models.Machine.objects.filter(id=item, del_tag=0)
            if query_machine:
                query_rel = models.ServiceToEnv.objects.filter(
                    rel_ips__contains=',' + str(item) + ',')
                if query_rel:
                    bind_service.append(item)
                else:
                    query_machine.update(del_tag=1)
            else:
                not_found_machine.append(item)
        msg1, msg2 = '', ''
        if not_found_machine:
            msg1 = 'ID为%s不存在，删除失败\n' % not_found_machine
        if bind_service:
            msg2 = 'ID为%s已绑定服务，请先解绑' % bind_service
        t_msg = msg1 + msg2
        if t_msg:
            msg = {'code': 10003, 'data': {}, 'msg': t_msg}
        else:
            msg = {'code': 200, 'data': {}, 'msg': '删除成功'}
        PutAudit(request, msg)  # 审计
        return JsonResponse(msg)


class RdsListView(baseview.BaseView):
    @auth("assets.store-list.add")
    def post(self, request, args=None):
        data = request.data
        op_type = data['type']
        if op_type == "cron_ali":
            cron_sync_ali_rds()
            msg = {'code': 200, 'data': {}, 'msg': 'success'}
        elif op_type == "rds_add":
            rds_name = data.get('rds_name', None)
            data.pop('type')
            if not rds_name:
                msg = {'code': 10003, 'data': {}, 'msg': 'name required'}
                return JsonResponse(msg)
            query_rds = models.RDS.objects.filter(rds_name=rds_name, del_tag=0)
            data['u_time'] = now()
            data['create_time'] = now()
            if not query_rds:
                short_uuid = gen_shortuuid()
                rds_id = '-'.join(('lm', short_uuid))
                query_rds_id = models.RDS.objects.filter(rds_id=rds_id,
                                                         del_tag=0)
                while True:
                    if query_rds_id:
                        rds_id = '-'.join(('lm', short_uuid))
                        continue
                    else:
                        data['rds_id'] = rds_id
                        models.RDS.objects.create(**data)
                        msg = {'code': 200, 'data': [], 'msg': 'RDS新增成功'}
                        PutAudit(request, msg)  # 审计
                        return JsonResponse(msg)
            else:
                msg = {'code': 10003, 'data': [], 'msg': 'RDS名称已存在,请勿重复添加'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': 'op_type参数有误'}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.store-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type', None)
        if op_type == "get_all_rds":
            rds_name = request.GET.get('rds_name')
            run_status = request.GET.get('status_id')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if rds_name:
                q.children.append(('rds_name__contains', rds_name))
            if run_status:
                q.children.append(('run_status', run_status))
            rds_infos = models.RDS.objects.filter(q)
            total = rds_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            rds_show_infos = rds_infos[start:end].values(
                'id', 'rds_id', 'rds_name', 'run_status', 'create_time',
                'expiration_time', 'engine', 'engine_version', 'port',
                'conn_address', 'charge_type', 'zone_id', 'remark', 'specs',
                'u_time')
            data = []
            for item in rds_show_infos:
                data.append({
                    'id': item['id'],
                    'rds_name': item['rds_name'],
                    'run_status': item['run_status'],
                    'engine': item['engine'],
                    'engine_version': item['engine_version'],
                    'zone_id': item['zone_id'],
                    'charge_type': item['charge_type'],
                    "create_time": item['create_time'],
                    "expiration_time": item['expiration_time'],
                    "u_time": item["u_time"],
                    "port": item["port"],
                    "conn_address": item["conn_address"],
                })
            msg = {
                'code': 200,
                'data': {
                    'rds_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "rds_details":
            id = request.GET.get('id')
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_rds_detail = models.RDS.objects.filter(id=id, del_tag=0)
            if query_rds_detail:
                serializer = RDSSerializers(query_rds_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': '未查询到此ID:%s相关RDS' % id
                }
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.store-list.edit")
    def put(self, request, args=None):
        data = request.data
        id = int(data['id']) if data.get(id, None) else None
        rds_name = data.get('rds_name', None)
        data['u_time'] = now()
        if not id or not rds_name:
            msg = {'code': 10003, 'data': {}, 'msg': 'id&rds name required'}
            return JsonResponse(msg)
        query_rds = models.RDS.objects.filter(id=id, del_tag=0)
        if query_rds:
            query_rds_name = models.models.fields(rds_name=rds_name, del_tag=0)
            query_rds_id = query_rds_name[0].id if query_rds_name else None
            if query_rds_id == id:
                query_rds_name.update(**data)
                msg = {'code': 200, 'data': [], 'msg': 'RDS信息修改成功'}
            else:
                msg = {'code': 10003, 'data': [], 'msg': 'RDS名称已存在,请勿重复添加'}
        else:
            msg = {'code': 10003, 'data': [], 'msg': '未找到rds信息,修改失败'}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.store-list.del")
    def delete(self, request, args=None):
        data = request.data
        id = int(data['id']) if data.get(id, None) else None
        if not id:
            msg = {'code': 10003, 'data': {}, 'msg': 'id required'}
            return JsonResponse(msg)
        query_rds = models.RDS.objects.filter(del_tag=0, id=id)
        if query_rds:
            query_rds.update(del_tag=1)
            msg = {'code': 200, 'data': [], 'msg': 'RDS删除成功'}
        else:
            msg = {'code': 10003, 'data': [], 'msg': '未找到rds信息,删除失败'}
        PutAudit(request, msg)
        return JsonResponse(msg)


class DiskListView(baseview.BaseView):
    """
    cron_ali

    """
    @auth("assets.store-list.add")
    def post(self, request, args=None):
        data = request.data
        op_type = data['type']
        data.pop('type')
        if op_type == "cron_ali":
            cron_sync_ali_disk()
            return JsonResponse({'code': 200, 'data': {}, 'msg': 'success'})
        elif op_type == "disk_add":  # 页面添加
            short_uuid = gen_shortuuid()
            disk_id = '-'.join(('ld', short_uuid))  # 本地磁盘ID
            query_disk = models.Disk.objects.filter(disk_id=disk_id, del_tag=0)
            data['u_time'] = now()
            data['c_time'] = now()
            if not query_disk:  # 重复
                query_disk_list = [
                    item['disk_id'] for item in models.Disk.objects.filter(
                        del_tag=0).values('disk_id')
                ]
                while True:
                    if disk_id in query_disk_list:
                        disk_id = '-'.join(('ld', short_uuid))
                        continue
                    else:
                        data['disk_id'] = disk_id
                        models.Disk.objects.create(**data)
                        msg = {'code': 200, 'data': {}, 'msg': 'success'}
                        PutAudit(request, msg)
                        return JsonResponse(msg)
            else:
                data['disk_id'] = disk_id
                models.Disk.objects.create(**data)
                msg = {'code': 200, 'data': {}, 'msg': '磁盘新增成功'}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.store-list.view")
    def get(self, request, args=None):
        """
        {type: get_all_disk:{disk_name, run_status, pageNo, pageSize}
               disk_detail:{id}
        """
        op_type = request.GET.get('type')
        if op_type == "get_all_disk":
            idc_id = request.GET.get('idc_id')
            disk_name = request.GET.get('disk_name')
            run_status = request.GET.get('status_id')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if disk_name:
                q.children.append(("disk_name__contains", disk_name))
            if run_status:
                q.children.append(("run_status", run_status))
            if idc_id:
                q.children.append(("idc_id", idc_id))
            disk_infos = models.Disk.objects.filter(q)
            total = disk_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            disk_show_infos = disk_infos[start:end].values(
                'id', 'zone_id', 'idc_id', 'disk_name', 'disk_type',
                'category', 'disk_size', 'expired_time', 'run_status',
                'u_time', 'disk_id')
            data = []
            for item in disk_show_infos:
                data.append({
                    'id': item['id'],
                    'disk_id': item['disk_id'],
                    'zone_id': item['zone_id'],
                    'idc_id': item['idc_id'],
                    'disk_name': item['disk_name'],
                    'disk_type': item['disk_type'],
                    'category': item['category'],
                    'disk_size': item['disk_size'],
                    'expired_time': item['expired_time'],
                    'run_status': item['run_status'],
                    'u_time': item['u_time'],
                })
            msg = {
                'code': 200,
                'data': {
                    'disk_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "disk_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "缺少必要id参数"
                })
            query_disk_detail = models.Disk.objects.filter(id=id)
            if query_disk_detail:
                serializer = DiskSerializers(query_disk_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {
                    'code': 10003,
                    'data': {},
                    'msg': '未查询到此ID:%s相关DISK' % id
                }
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.store-list.edit")
    def put(self, request, args=None):
        data = request.data
        id = int(data['id']) if data.get('id', None) else None
        data['u_time'] = now()
        if not id:
            msg = {'code': 10003, 'data': {}, 'msg': 'id required'}
            return JsonResponse(msg)
        query_disk = models.Disk.objects.filter(id=id, del_tag=0)
        if query_disk:
            query_disk.update(**data)
            msg = {'code': 200, 'data': {}, 'msg': '磁盘信息修改成功'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未查询到磁盘ID,请联系相关运维！'}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.store-list.del")
    def delete(self, request, args=None):
        data = request.data
        id = int(data['id']) if data.get('id', None) else None
        if not id:
            msg = {'code': 10003, 'data': {}, 'msg': 'id required'}
            return JsonResponse(msg)
        query_disk = models.Disk.objects.filter(id=id, del_tag=0)
        if query_disk:
            query_disk.update(del_tag=1)
            msg = {'code': 200, 'data': {}, 'msg': '删除磁盘信息成功'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '删除失败,未查询到磁盘ID'}
        PutAudit(request, msg)
        return JsonResponse(msg)


class DomainListView(baseview.BaseView):
    @auth("assets.network-list.add")
    def post(self, request, args=None):
        op_type = request.data['type']
        if op_type == "cron_ali":
            cron_sync_ali_domain()
            return JsonResponse({'code': 200, 'data': {}, 'msg': 'success'})

    @auth("assets.network-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type')
        if not op_type:
            return JsonResponse({
                'code': 10003,
                'data': {},
                'msg': '缺少必要type参数'
            })
        if op_type == "get_all_domain":
            domain_name = request.GET.get('domain_name')
            domain_owner = request.GET.get('domain_owner')
            domain_status = request.GET.get('domain_status')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if domain_name:
                q.children.append(("domain_name__contains", domain_name))
            if domain_owner:
                q.children.append(("domain_owner__contains", domain_owner))
            if domain_status:
                q.children.append(("domain_status", domain_status))
            domain_infos = models.Domain.objects.filter(q)
            total = domain_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            domain_show_infos = domain_infos[start:end].values(
                'id', 'domain_name', 'registrant_type', 'domain_type', 'email',
                'registration_date', 'expiration_date', 'domain_status',
                'u_time', 'domain_owner')
            data = []
            for item in domain_show_infos:
                data.append({
                    'id': item['id'],
                    'domain_name': item['domain_name'],
                    'registrant_type': item['registrant_type'],
                    'domain_type': item['domain_type'],
                    'email': item['email'],
                    'registration_date': item['registration_date'],
                    'expiration_date': item['expiration_date'],
                    'domain_status': item['domain_status'],
                    'domain_owner': item['domain_owner'],
                    'u_time': item['u_time']
                })
            msg = {
                'code': 200,
                'data': {
                    'domain_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "domain_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "缺少必要id参数"
                })
            query_domain_detail = models.Domain.objects.filter(id=id)
            if query_domain_detail:
                serializer = DomainSerializers(query_domain_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)


class OssListView(baseview.BaseView):
    @auth("assets.store-list.add")
    def post(self, request, args=None):
        op_type = request.data.get('type', None)
        if op_type == 'cron_ali':
            cron_sync_ali_oss()
            return JsonResponse({'code': 200, 'data': {}, 'msg': 'success'})

    @auth("assets.store-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type', None)
        if op_type == "get_all_oss":
            oss_name = request.GET.get('oss_name')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(('del_tag', 0))
            if oss_name:
                q.children.append(('oss_name__contains', oss_name))
            oss_infos = models.Oss.objects.filter(q)
            total = oss_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            oss_show_infos = oss_infos[start:end].values(
                'id', 'oss_name', 'storage_class', 'extranet_endpoint',
                'intranet_endpoint', 'grant', 'location', 'u_time')
            data = []
            for item in oss_show_infos:
                data.append({
                    'id': item['id'],
                    'oss_name': item['oss_name'],
                    'storage_class': item['storage_class'],
                    'extranet_endpoint': item['extranet_endpoint'],
                    'intranet_endpoint': item['intranet_endpoint'],
                    'grant': item['grant'],
                    'location': item['location'],
                    'u_time': item['u_time'],
                })
            msg = {
                'code': 200,
                'data': {
                    'oss_infos': data,
                    'total': total,
                    'msg': 'success'
                }
            }
        elif op_type == "oss_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': '缺少必要id参数'
                })
            query_oss_detail = models.Oss.objects.filter(id=id)
            if query_oss_detail:
                serializer = OssSerializers(query_oss_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)


class VpcListView(baseview.BaseView):
    @auth("assets.network-list.add")
    def post(self, request, args=None):
        op_type = request.data.get('type', None)
        if op_type == 'cron_ali':
            cron_sync_ali_vpc()
            msg = {'code': 200, 'data': {}, 'msg': 'success'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '暂不支持此type'}
        return JsonResponse(msg)

    @auth("assets.network-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type', None)
        if op_type == "get_all_vpc":
            vpc_status = request.GET.get('vpc_status')
            vpc_name = request.GET.get('vpc_name')
            zone_id = request.GET.get('zone_id')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if vpc_status:
                q.children.append(("vpc_status", vpc_status))
            if vpc_name:
                q.children.append(("vpc_name__contains", vpc_name))
            if zone_id:
                q.children.append(("region_id", zone_id))
            vpc_infos = models.Vpc.objects.filter(q)
            total = vpc_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            vpc_show_infos = vpc_infos[start:end].values(
                'id', 'vpc_id', 'vpc_name', 'vpc_status', 'cidr_block',
                'description', 'vpc_status', 'u_time', 'zone_id')
            data = []
            for item in vpc_show_infos:
                data.append({
                    'id': item['id'],
                    'vpc_id': item['vpc_id'],
                    'vpc_name': item['vpc_name'],
                    'vpc_status': item['vpc_status'],
                    'cidr_block': item['cidr_block'],
                    'description': item['description'],
                    'vpc_status': item['vpc_status'],
                    'zone_id': item['zone_id'],
                    'u_time': item['u_time']
                })
            msg = {
                'code': 200,
                'data': {
                    'vpc_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "vpc_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_vpc_detail = models.Vpc.objects.filter(id=id, del_tag=0)
            if query_vpc_detail:
                serializer = VpcSerializers(query_vpc_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)


class CdnListView(baseview.BaseView):
    @auth("assets.network-list.add")
    def post(self, request, args=None):
        op_type = request.data.get('type', None)
        if op_type == "cron_ali":
            cron_sync_ali_cdn()
            msg = {'code': 200, 'data': {}, 'msg': 'success'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '暂不支持此type'}
        return JsonResponse(msg)

    @auth("assets.network-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type')
        if op_type == "get_all_cdn":
            coverage = request.GET.get('coverage')
            domain_status = request.GET.get('domain_status')
            domain_name = request.GET.get('domain_name')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if domain_name:
                q.children.append(("domain_name__contains", domain_name))
            if coverage:
                q.children.append(("coverage", coverage))
            if domain_status:
                q.children.append(("domain_status", domain_status))
            cdn_infos = models.CDN.objects.filter(q)
            total = cdn_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageSize * pageNo
            cdn_show_infos = cdn_infos[start:end].values(
                'id', 'domain_name', 'cdn_name', 'description', 'coverage',
                'domain_status', 'cdn_type')
            data = []
            for item in cdn_show_infos:
                data.append({
                    'id': item['id'],
                    'domain_name': item['domain_name'],
                    'cdn_name': item['cdn_name'],
                    'description': item['description'],
                    'coverage': item['coverage'],
                    'domain_status': item['domain_status'],
                    'cdn_type': item['cdn_type']
                })
            msg = {
                'code': 200,
                'data': {
                    'cdn_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "cdn_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_cdn_detail = models.CDN.objects.filter(id=id, del_tag=0)
            if query_cdn_detail:
                serializer = CdnSerializers(query_cdn_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)


class SlbListView(baseview.BaseView):
    @auth("assets.network-list.add")
    def post(self, request, args=None):
        op_type = request.data.get('type', None)
        if op_type == "cron_ali":
            cron_sync_ali_slb()
            msg = {'code': 200, 'data': {}, 'msg': "success"}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.network-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type', None)
        if op_type == "get_all_slb":
            lb_name = request.GET.get('lb_name')
            address = request.GET.get('address')
            zone_id = request.GET.get('zone_id')
            lb_status = request.GET.get('lb_status')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if lb_name:
                q.children.append("lb_name__contains", lb_name)
            if address:
                q.children.append("address__contains", address)
            if zone_id:
                q.children.append("zone_id", zone_id)
            if lb_status:
                q.children.append("lb_status", lb_status)
            slb_infos = models.Slb.objects.filter(q)
            total = slb_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            slb_show_infos = slb_infos[start:end].values(
                'id', 'lb_id', 'lb_name', 'address_type', 'address_ip_version',
                'bandwidth', 'master_zone_id', 'slave_zone_id', 'zone_id',
                'lb_status')
            data = []
            for item in slb_show_infos:
                data.append({
                    'id': item['id'],
                    'lb_id': item['lb_id'],
                    'lb_name': item['lb_name'],
                    'address_type': item['address_type'],
                    'address_ip_version': item['address_ip_version'],
                    'bandwidth': item['bandwidth'],
                    'master_zone_id': int(item['master_zone_id']),
                    'slave_zone_id': int(item['slave_zone_id']),
                    'zone_id': item['zone_id'],
                    'lb_status': item['lb_status']
                })
            msg = {
                'code': 200,
                'data': {
                    'slb_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "slb_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "id required."
                })
            query_slb_detail = models.Slb.objects.filter(id=id, del_tag=0)
            if query_slb_detail:
                serializer = SlbSerializers(query_slb_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)


class SwitchListView(baseview.BaseView):
    @auth("assets.network-list.view")
    def get(self, request, args=None):
        op_type = request.GET.get('type')
        if not op_type:
            return JsonResponse({
                'code': 10003,
                'data': {},
                'msg': '缺少必要type参数'
            })
        if op_type == "get_all_switch":
            switch_id = request.GET.get('switch_id')
            switch_name = request.GET.get('switch_name')
            switch_status = request.GET.get('switch_status')
            pageNo = int(request.GET.get('page_no', 1))
            pageSize = int(request.GET.get('page_size', 10))
            q = Q()
            q.children.append(("del_tag", 0))
            if switch_id:
                q.children.append(("switch_id__contains", switch_id))
            if switch_name:
                q.children.append(("name__contains", switch_name))
            if switch_status:
                q.children.append(("status", switch_status))
            switch_infos = models.Switch.objects.filter(q)
            total = switch_infos.count()
            start = (pageNo - 1) * pageSize
            end = pageNo * pageSize
            switch_show_infos = switch_infos[start:end].values(
                'id', 'switch_id', 'name', 'status', 'description',
                'ip_address_no', 'route_table', 'cidr_block', 'idc_id')
            data = []
            for item in switch_show_infos:
                data.append({
                    'id': item['id'],
                    'switch_id': item['switch_id'],
                    'name': item['name'],
                    'status': item['status'],
                    'description': item['description'],
                    'ip_address_no': item['ip_address_no'],
                    'route_table': item['route_table'],
                    'cidr_block': item['cidr_block'],
                    'idc_id': item['idc_id'],
                })
            msg = {
                'code': 200,
                'data': {
                    'switch_infos': data,
                    'total': total
                },
                'msg': 'success'
            }
        elif op_type == "switch_details":
            id = request.GET.get('id', None)
            if not id:
                return JsonResponse({
                    'code': 10003,
                    'data': {},
                    'msg': "缺少必要id参数"
                })
            query_switch_detail = models.Switch.objects.filter(id=id)
            if query_switch_detail:
                serializer = SwitchSerializers(query_switch_detail, many=True)
                msg = {'code': 200, 'data': serializer.data, 'msg': 'success'}
            else:
                msg = {'code': 10003, 'data': {}, 'msg': '未查询到此ID:%s相关信息' % id}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        return JsonResponse(msg)

    @auth("assets.network-list.add")
    def post(self, request, args=None):
        data = request.data
        op_type = request.data.get('type', None)
        if op_type == "switch_add":
            name = data.get('name', None)
            data['create_time'] = now()
            data['u_time'] = now()
            data.pop('type')
            if not name:
                msg = {'code': 10003, 'data': {}, 'msg': 'name required'}
                return JsonResponse(msg)
            query_switch = models.Switch.objects.filter(del_tag=0, name=name)
            if not query_switch:
                short_uuid = gen_shortuuid()
                switch_id = '-'.join(('lsw', short_uuid))
                query_switch_id = models.Switch.objects.filter(
                    del_tag=0, switch_id=switch_id)
                while True:
                    if query_switch_id:
                        switch_id = '-'.join(('lsw', short_uuid))
                        continue
                    else:
                        data['switch_id'] = switch_id
                        models.Switch.objects.create(**data)
                        msg = {'code': 200, 'data': {}, 'msg': 'switch新增成功'}
                        return JsonResponse(msg)
            else:
                msg = {'code': 10003, 'data': {}, 'msg': 'switch名称已存在，请勿重复添加'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': "暂不支持此type"}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.network-list.edit")
    def put(self, request, args=None):
        data = request.data
        id = int(data['id']) if data.get('id', None) else None
        data['u_time'] = now()
        if not id:
            msg = {'code': 10003, 'data': {}, 'msg': 'name required'}
            return JsonResponse(msg)
        query_switch = models.Switch.objects.filter(del_tag=0, id=id)
        if query_switch:
            query_switch.update(**data)
            msg = {'code': 200, 'data': {}, 'msg': 'switch信息更新成功'}
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未找到相关信息,更新失败'}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.network-list.del")
    def delete(self, request, args=None):
        msg = {"code": 200, "data": {}, "msg": "删除成功"}
        data = request.data
        id = int(data['id']) if data.get('id', None) else None
        if not id:
            msg = {'code': 10003, 'data': {}, 'msg': 'name required'}
            return JsonResponse(msg)
        query_switch = models.Switch.objects.filter(del_tag=0, id=id)
        if query_switch:
            query_switch.update(del_tag=1)
        else:
            msg = {'code': 10003, 'data': {}, 'msg': '未找到相关信息,删除失败'}
        PutAudit(request, msg)
        return JsonResponse(msg)


class InnerPostMachine(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 machine 数据成功"}
        cron_sync_ali_ecs()
        return JsonResponse(msg)


class InnerPostRds(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 rds 数据成功"}
        cron_sync_ali_rds()
        return JsonResponse(msg)


class InnerPostDisk(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 disk 数据成功"}
        cron_sync_ali_disk()
        return JsonResponse(msg)


class InnerPostDomain(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 domain 数据成功"}
        cron_sync_ali_domain()
        cron_sync_cloudflare_domain()
        return JsonResponse(msg)


class InnerPostOss(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 oss 数据成功"}
        cron_sync_ali_oss()
        return JsonResponse(msg)


class InnerPostVpc(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 vpc/switch 数据成功"}
        cron_sync_ali_vpc()
        return JsonResponse(msg)


class InnerPostCdn(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 cdn 数据成功"}
        cron_sync_ali_cdn()
        return JsonResponse(msg)


class InnerPostSlb(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 slb 数据成功"}
        cron_sync_ali_slb()
        return JsonResponse(msg)


class InnerPostDnsRecord(baseview.AnyLogin):
    def post(self, request, args=None):
        msg = {"code": 200, "data": "", "msg": "同步 dnsrecord 数据成功"}
        cron_sync_ali_domain_record()
        # cron_sync_cloudflare_domain_record()
        return JsonResponse(msg)


class DNSListView(baseview.BaseView):
    @auth("assets.network-list.view")
    def get(self, request, args=None):
        domain_id = request.GET.get('domain_id', None)
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        RR = request.GET.get('RR', None)
        if not domain_id:
            msg = {'code': 10003, 'data': {}, 'msg': "缺少必要domain_id参数"}
            return JsonResponse(msg)
        if RR:
            query_records = models.DnsRecords.objects.filter(
                domain_id=domain_id, del_tag=0, RR__contains=RR)
        else:
            query_records = models.DnsRecords.objects.filter(
                domain_id=domain_id, del_tag=0)
        total = query_records.count()
        start = (pageNo - 1) * pageSize
        end = pageNo * pageSize
        serializer = DnsRecordsSerializers(query_records[start:end], many=True)
        msg = {
            'code': 200,
            'data': {
                'record_infos': serializer.data,
                'total': total
            },
            'msg': 'success'
        }
        return JsonResponse(msg)

    @auth("assets.network-list.add")
    def post(self, request, args=None):
        """
        :param request:  belong_to,domain_id,domain_name,RR,ttl,type,priority(MX),value,line(ali),op_type(cron_dns_records|record_add)
        :param args:
        :return:
        """
        spec_type_list = ['MX', 'SRV', 'URI']
        data = request.data
        op_type = data.get('op_type')
        msg = {"code": 100002, "data": {}, "msg": "请传递参数 op_type"}
        if op_type == 'cron_all':
            cron_sync_ali_domain_record()
            cron_sync_cloudflare_domain_record()
            msg = {"code": 200, "data": {}, "msg": "success"}
        elif op_type == 'record_add':  # record 新增
            belong_to = data['belong_to']
            domain_id = data.get('domain_id')
            domain = models.Domain.objects.filter(id=domain_id,
                                                  del_tag=0).first()
            domain_name = domain.domain_name
            rr = data.get('RR')
            ttl = int(data.get('ttl')) if data.get('ttl') else 600
            r_type = data.get('type')
            r_value = data.get('value')
            priority = int(
                data.get('priority')) if data.get('priority') else None
            # 状态
            status_id = data.get('status_id')
            if r_type not in spec_type_list:
                if priority:
                    msg = {
                        "code": 10003,
                        "data": {},
                        "msg": "当类型为'MX'、'SRV'、'URI'时，priority不应有值"
                    }
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            else:
                if not priority:
                    msg = {
                        "code": 10003,
                        "data": {},
                        "msg": "当类型为'MX'、'SRV'、'URI'时，priority必须有值"
                    }
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            query_has = models.DnsRecords.objects.filter(
                RR=rr,
                type=type,
                value=r_value,
                del_tag=0,
                belong_to=belong_to).first()
            if query_has:
                msg = {'code': 10003, 'data': {}, 'msg': 'record已存在，请勿重复添加'}
                PutAudit(request, msg)
                return JsonResponse(msg)
            if 'alibaba' in belong_to:  # ali
                line = data.get('line')
                line_choices = models.DnsRecords.line_choices
                for item in line_choices:
                    if item[1] == line:
                        line = item[0]
                        break
                ali_dns = aliyun.DomainRecords(domain_name=domain_name)
                new_ali_dns_record = ali_dns.new_record(rr=rr,
                                                        ttl=ttl,
                                                        type=r_type,
                                                        value=r_value,
                                                        priority=priority,
                                                        line=line)
                record_id = new_ali_dns_record.get('RecordId', None)
                if record_id:
                    # 落库
                    models.DnsRecords.objects.create(domain_id=domain_id,
                                                     RR=rr,
                                                     type=r_type,
                                                     value=r_value,
                                                     ttl=ttl,
                                                     priority=priority,
                                                     u_time=now(),
                                                     belong_to=belong_to,
                                                     status_id=status_id,
                                                     line=line,
                                                     record_id=record_id)
                    msg = {"code": 200, "data": {}, "msg": "success"}
                else:
                    msg = {
                        "code": 10003,
                        "data": {},
                        "msg": "domain record新增失败"
                    }
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            elif 'CloudFlare' in belong_to:
                cf = CloudFlareApi(token=ClOUDFLARE_TOKEN)
                zone_id = cf.get_zone(zone_name=domain_name)[0]['id']
                proxied = data.get('proxied', None)
                new_cf_dns_record = cf.new_record(zone_id=zone_id,
                                                  name=rr,
                                                  type=r_type,
                                                  content=r_value,
                                                  ttl=ttl,
                                                  priority=priority,
                                                  proxied=proxied)
                cf_dns_record_id = new_cf_dns_record.get('id', None)
                if cf_dns_record_id:
                    models.DnsRecords.objects.create(
                        domain_id=domain_id,
                        RR=rr,
                        type=r_type,
                        value=r_value,
                        ttl=ttl,
                        priority=priority,
                        proxied=proxied,
                        u_time=now(),
                        status_id=status_id,
                        belong_to=belong_to,
                        record_id=cf_dns_record_id)
                else:
                    msg = {
                        "code": 10003,
                        "data": {},
                        "msg": "domain record新增失败"
                    }
                    PutAudit(request, msg)
                    return JsonResponse(msg)
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.network-list.del")
    def delete(self, request, args=None):
        """
        :param request:  ids:list ,domain_id
        :param args:
        :return:
        """
        del_ids = request.data['ids']
        domain_id = request.data['domain_id']
        domain = models.Domain.objects.filter(id=domain_id, del_tag=0).first()
        domain_name = domain.domain_name
        no_has_ids = []
        del_failed = []
        if del_ids:
            for id in del_ids:
                query_record = models.DnsRecords.objects.filter(
                    id=id, del_tag=0).first()
                if not query_record:
                    no_has_ids.append(id)
                else:
                    belong_to = query_record.belong_to
                    record_id = query_record.record_id
                    if 'alibaba' in belong_to:
                        ali = aliyun.DomainRecords(domain_name=domain_name)
                        del_record = ali.delete_record(record_id)  # api删除
                        del_record_id = del_record.get('RecordId', None)
                        if del_record_id == record_id:
                            models.DnsRecords.objects.filter(
                                id=id, del_tag=0).update(del_tag=1)
                        else:
                            del_failed.append(record_id)
                    elif 'CloudFlare' in belong_to:
                        cf = CloudFlareApi(token=ClOUDFLARE_TOKEN)
                        zone_id = cf.get_zone(domain_name)[0]['id']
                        del_cf_record = cf.delete_record(
                            zone_id=zone_id, dns_record_id=record_id)
                        def_cf_record_id = del_cf_record.get('id', None)
                        if def_cf_record_id == zone_id:  # 落库
                            models.DnsRecords.objects.filter(
                                id=id, del_tag=0).update(del_tag=1)
                        else:
                            del_failed.append(record_id)
        # 信息返回
        msg1 = ''
        if no_has_ids:
            msg1 = '未查询到%s记录信息，请确认\n' % no_has_ids
        msg2 = ''
        if del_failed:
            msg2 = '%s记录删除失败,请联系相关运维' % del_failed
        t_msg = msg1 + msg2
        if t_msg:
            msg = {"code": 10003, "data": {}, "msg": t_msg}
        else:
            msg = {"code": 200, "data": {}, "msg": "success"}
        PutAudit(request, msg)
        return JsonResponse(msg)

    @auth("assets.network-list.edit")
    def put(self, request, args=None):
        """
        :param request: domain_id,id, belong_to
        :param args:
        :return:
        """
        data = request.data
        spec_type_list = ['MX', 'SRV', 'URI']
        r_id = data['id']
        domain_id = request.data['domain_id']
        domain_name = models.Domain.objects.filter(
            del_tag=0, id=domain_id).first().domain_name
        rr = data.get('RR', None)
        r_type = data.get('type', None)
        r_value = data.get('value', None)
        ttl = data.get('ttl', None)
        belong_to = data.get('belong_to')
        priority = data.get('priority', None)
        query_record = models.DnsRecords.objects.filter(id=r_id, del_tag=0)
        record_id = query_record[0].record_id
        # 重新赋值
        rr1 = rr if rr else query_record[0].RR
        r_type1 = r_type if r_type else query_record[0].type
        r_value1 = r_value if r_value else query_record[0].value
        ttl1 = ttl if ttl else query_record[0].ttl
        belong_to1 = belong_to if belong_to else query_record[0].belong_to
        priority1 = priority if priority else query_record[0].priority
        if (rr or r_type or r_value):  # 是否重复
            query_has_record = models.DnsRecords.objects.filter(
                ~Q(id=r_id),
                RR=rr1,
                type=r_type1,
                value=r_value1,
                del_tag=0,
                belong_to=belong_to1).first()
            if query_has_record:
                msg = {"code": 10003, "data": {}, "msg": "此解析记录已存在，请勿重复添加"}
                PutAudit(request, msg)
                return JsonResponse(msg)
        if r_type1 not in spec_type_list:
            if priority:
                msg = {
                    "code": 10003,
                    "data": {},
                    "msg": "仅记录类型为'MX'、'SRV'、'URI'时，priority有值"
                }
                PutAudit(request, msg)
                return JsonResponse(msg)
        else:
            if not priority:
                msg = {
                    "code": 10003,
                    "data": {},
                    "msg": "当记录类型为'MX'、'SRV'、'URI'时，priority required"
                }
                PutAudit(request, msg)
                return JsonResponse(msg)
        msg = {"code": 10002, "data": {}, "msg": "确认domain record归属"}
        if 'alibaba' in belong_to1:
            line = data.get('line', None)
            line_choices = models.DnsRecords.line_choices
            for item in line_choices:
                if item[1] == line:
                    line = item[0]
                    break
            remark = data.get('remark', None)
            status_id = data.get('status_id', None)
            line1 = line if line else query_record[0].line
            ali_domain_record = aliyun.DomainRecords(domain_name=domain_name)
            if (rr or r_type or r_value or ttl or priority or line):
                update_ali_record = ali_domain_record.update_record(
                    record_id=record_id,
                    rr=rr1,
                    type=r_type1,
                    value=r_value1,
                    ttl=ttl1,
                    priority=priority1,
                    line=line1)
                resp_id = update_ali_record.get('RecordId', None)
                if resp_id == record_id:
                    query_record.update(RR=rr1,
                                        type=r_type1,
                                        value=r_value1,
                                        ttl=ttl1,
                                        priority=priority1,
                                        line=line1)  # 落库
                else:
                    msg = {"code": 10003, "data": {}, "msg": "解析记录更新失败"}
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            if status_id:
                record_status = \
                    models.DeviceStatus.objects.filter(del_tag=0, id=int(status_id)).values('description')[0][
                        'description'].split(',')[1]
                update_record_status = ali_domain_record.set_record_status(
                    record_id=record_id, status=record_status)
                resp_status = update_record_status.get('Status', None)
                if resp_status == record_status:
                    query_record.update(status_id=int(status_id))  # 落库
                else:
                    msg = {"code": 10003, "data": {}, "msg": "解析记录更新失败"}
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            if remark:
                update_record_remark = ali_domain_record.update_record_remark(
                    record_id=record_id, remark=remark)
                resp_remark = update_record_remark.get('RequestId', None)
                if resp_remark:
                    query_record.update(remark=remark)  # 落库
                else:
                    msg = {"code": 10003, "data": {}, "msg": "解析记录更新失败"}
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            msg = {"code": 200, "data": {}, "msg": "success"}
        elif 'CloudFlare' in belong_to1:
            proxied = data.get('proxied', None)
            proxied1 = proxied if proxied else query_record[0].proxied
            if (rr or r_type or r_value or ttl or priority or proxied):
                cf = CloudFlareApi(token=ClOUDFLARE_TOKEN)
                zone_id = cf.get_zone(domain_name)[0]['id']
                update_cf_record = cf.patch_record(zone_id=zone_id,
                                                   dns_record_id=record_id,
                                                   name=rr1,
                                                   type=r_type1,
                                                   content=r_value1,
                                                   ttl=ttl1,
                                                   proxied=proxied1,
                                                   priority=priority1)
                resp_cf_record = update_cf_record.get('id', None)
                if resp_cf_record:
                    query_record.update(RR=rr1,
                                        type=r_type1,
                                        value=r_value1,
                                        ttl=ttl1,
                                        proxied=proxied,
                                        priority=priority1)
                else:
                    msg = {"code": 10003, "data": {}, "msg": "解析记录更新失败"}
                    PutAudit(request, msg)
                    return JsonResponse(msg)
            msg = {"code": 200, "data": {}, "msg": "success"}
        PutAudit(request, msg)
        return JsonResponse(msg)


# 新增虚拟机定时任务
class VirturlMachine:
    '''
    domain_name,ip,status,cpu,mem,disk,os_name,mac_addr

    :return:
    '''

    def __init__(self, host_ip, passwd, port=22, auth_type=0, username='root'):
        # 远程验证
        self.host_ip = host_ip
        self.port = port  # 默认linux 22端口
        self.passwd = passwd
        self.auth_type = auth_type  # 0:密码 1:文件
        self.username = username  # 默认 root
        self.sshContr = LinuxRemoteConn(host_ip=self.host_ip,
                                        password=self.passwd,
                                        port=self.port,
                                        auth_type=self.auth_type,
                                        username=self.username)

    def __vsrv_ip(self, cidr, remote_path=None):
        if not cidr:  # 默认宿主机IP段
            cidr = self.host_ip[:self.host_ip.rfind('.')]
        # 本地脚本路径(项目相对路径)
        local_path = '/data/proj_cmt/cmdb_backend/scripts/get_virt_ip.sh'
        if not remote_path:
            remote_path = '/root/scripts/get_virt_ip.sh'  # 远程脚本路径
        remote_dir = os.path.dirname(remote_path)  # 远程目录
        _cmd_exit_dir = 'ls -al %s' % remote_dir
        _cmd_exit_file = 'ls -al %s' % remote_path
        _cmd_dir = 'mkdir -p %s' % remote_dir
        rlt2 = self.sshContr.run_cmd(_cmd_exit_file)  # 判断文件
        if not rlt2:
            rlt1 = self.sshContr.run_cmd(_cmd_exit_dir)  # 判断目录
            if not rlt1:
                self.sshContr.run_cmd(_cmd_dir)
            self.sshContr.run_sftp('push',
                                   local_path=local_path,
                                   remote_path=remote_path)
        # 开始执行脚本
        _cmd = "sh %s %s" % (remote_path, cidr)
        rlt3 = self.sshContr.run_cmd(cmd=_cmd)
        vsrv_list = []  # josn数据处理
        if rlt3[0]:
            rlt4 = rlt3[0]
        else:
            rlt4 = rlt3[1][1]
        for item in list(filter(None, rlt4)):
            vsrv_list.append(json.loads(item.replace("\'", "\"")))
        return vsrv_list

    def __translate(self, ins):
        inst = {}
        inst['name'] = ins['name']
        inst['disk'] = ins['disk']
        inst['cpu'] = ins['cpu']
        inst['uuid'] = ins['uuid']
        inst['status'] = ins['status']
        inst['memory'] = ins['mem']
        if inst['memory']:
            inst['memory'] = int(int(inst['memory']) / 1024 / 1024)  # 内存单位G
        inst['mac'] = ins['mac']
        inst['ip'] = ins['ip']
        inst['master_ip'] = self.host_ip
        return inst

    def get_vsrv_info(self, cidr: list, remote_path=None):
        vsrv_infos = []
        for i in cidr:
            vname_list = self.__vsrv_ip(remote_path=remote_path, cidr=i)
            vsrv_info = list(map(self.__translate, vname_list))
            vsrv_infos.extend(vsrv_info)
        return vsrv_infos

    def get_all_virt(self):
        a = self.sshContr.run_cmd(cmd='virsh list --all')
        return a


def cron_sync_virt_machine():
    virt_machine_infos = []
    cron_sync_failed = []
    device_id = models.DeviceType.objects.filter(del_tag=0,
                                                 name='物理机').first().id
    virt_device_id = models.DeviceType.objects.filter(del_tag=0,
                                                      name='虚拟机').first().id
    query_master = models.Machine.objects.filter(del_tag=0,
                                                 server_type=device_id,
                                                 has_virt=True).values(
                                                     'ip_address',
                                                     'username',
                                                     'password',
                                                     'port',
                                                     'authentication_type',
                                                     'virt_cird',
    )
    for srv_item in query_master:
        try:
            auth_type = srv_item['authentication_type'] if srv_item[
                'authentication_type'] == 2 else 0
            virt_machine = VirturlMachine(
                host_ip=srv_item['ip_address'],
                username=srv_item['username'],
                passwd=srv_item['password'],
                port=srv_item['port'] if srv_item['port'] else 22,
                auth_type=auth_type)
            virt_cird = json.loads(
                srv_item['virt_cird']) if srv_item['virt_cird'] else None

            if virt_cird:
                machine_info = virt_machine.get_vsrv_info(cidr=virt_cird)
                virt_machine_infos.extend(machine_info)
            else:
                machine_info = virt_machine.get_vsrv_info(cidr=[''])
                virt_machine_infos.extend(machine_info)
            # 落库
            uuid_list = []
            if virt_machine_infos:
                data = {}
                for info in virt_machine_infos:
                    uuid = info['uuid']
                    uuid_list.append(uuid)
                    master_node_info = models.Machine.objects.filter(
                        ip_address=info['master_ip'],
                        del_tag=0,
                        server_type=device_id).first()
                    run_status = 'Running' if 'running' in info[
                        'status'] else 'Stopped'
                    status_id = models.DeviceStatus.objects.filter(
                        type_id=device_id,
                        del_tag=0,
                        description=',' + run_status + ',').first().id

                    data['sn_id'] = uuid
                    data['instance_name'] = info['name']
                    data['zone_id'] = master_node_info.zone_id
                    data['idc_id'] = master_node_info.idc_id
                    data['status_id'] = status_id
                    data['server_type'] = virt_device_id
                    data['ip_address'] = info['ip']
                    data['rel_server_id'] = master_node_info.id
                    ext = {
                        'cpu': info['cpu'],
                        'disk': info['disk'],
                        'memory': info['memory']
                    }
                    data['optional'] = json.dumps(ext)
                    models.Machine.objects.update_or_create(del_tag=0,
                                                            sn_id=uuid,
                                                            defaults=data)
            models.Machine.objects.filter(
                del_tag=0, server_type=virt_device_id).exclude(
                    sn_id__in=uuid_list).update(del_tag=1)
        except Exception as e:
            print('ERROR:', e)
            cron_sync_failed.append(srv_item['ip_address'])
            pass
    # 重置master主机参数
    master_ids = models.Machine.objects.filter(del_tag=0,
                                               has_virt=True).values('id')
    if master_ids:
        for item in master_ids:
            rlt = models.Machine.objects.filter(
                del_tag=0, rel_server_id=item['id']).first()
            if not rlt:
                models.Machine.objects.filter(id=item('id')).update(
                    has_virt=False)
