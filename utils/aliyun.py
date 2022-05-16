import json
import os, sys
from multiprocessing import Pool
from django.conf import settings
from aliyunsdkcore.client import AcsClient
# REGION
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest
# ECS
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
# DISK
from aliyunsdkecs.request.v20140526.DescribeDisksRequest import DescribeDisksRequest
# RDS
from aliyunsdkrds.request.v20140815.DescribeDBInstancesRequest import DescribeDBInstancesRequest
from aliyunsdkrds.request.v20140815.DescribeDBInstanceAttributeRequest import DescribeDBInstanceAttributeRequest
# Domain
from aliyunsdkdomain.request.v20180129.QueryDomainListRequest import QueryDomainListRequest
from aliyunsdkdomain.request.v20180129.QueryDomainByInstanceIdRequest import QueryDomainByInstanceIdRequest
# OSS
import oss2
# vpc
from aliyunsdkvpc.request.v20160428 import DescribeVpcAttributeRequest
from alibabacloud_vpc20160428 import models as vpc_20160428_models
from alibabacloud_vpc20160428.client import Client as Vpc20160428Client
from alibabacloud_tea_openapi import models as open_api_models
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
# Vswitch
from aliyunsdkvpc.request.v20160428 import DescribeVSwitchAttributesRequest
# cdn
from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_cdn20180510 import models as cdn_20180510_models
# slb
from alibabacloud_slb20140515.client import Client as Slb20140515Client
from alibabacloud_slb20140515 import models as slb_20140515_models
# dns records
from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_20150109_models

import logging

logger = logging.getLogger("ttool.app")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')
MY_PROJ_KEY = {
    'RegionId': 'cn-shanghai',
    'AK': settings.ALICLOUD_ACESS_KEY,
    'SK': settings.ALICLOUD_SECRET_KEY,
}


def print_dict_key(item, key):
    region_id = item.get(key)
    return region_id


class AliCloud:
    def __init__(self):
        pass

    """
    账户所支持的区域
    """

    @staticmethod
    def get_region_ids(client=None):
        try:
            client = client if client else AliCloud.auth_client()
            request = DescribeRegionsRequest()
            request.set_accept_format('json')
            response = json.loads(
                str(client.do_action_with_exception(request),
                    encoding='utf-8'))
            if response is not None:
                region_list = response.get('Regions').get('Region')
                assert response is not None
                assert region_list is not None
                result = [item['RegionId'] for item in region_list]
                return result
        except Exception as e:
            logger.error(e)

    """
    账户鉴权
    """

    @staticmethod
    def auth_client(access_key_id=None,
                    access_key_secret=None,
                    region_id=None):
        access_key = access_key_id if access_key_id else MY_PROJ_KEY['AK']
        secret = access_key_secret if access_key_secret else MY_PROJ_KEY['SK']
        region_id = region_id if region_id else MY_PROJ_KEY['RegionId']
        client = AcsClient(access_key, secret, region_id)
        return client


class ECS:
    '''
    获取阿里云当前账户下所有的ECS主机及其详细信息
    参考文档：https://help.aliyun.com/document_detail/25506.html?spm=a2c4g.11186623.6.1162.477c49baOuAWJA
    参考文档：https://help.aliyun.com/document_detail/25514.html?spm=a2c4g.11186623.6.1216.39a5431dHF33HN
    '''
    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id if access_key_id else MY_PROJ_KEY['AK']
        self.secret = access_key_secret if access_key_secret else MY_PROJ_KEY[
            'SK']
        self.client = None
        self.currentPage = []
        self.regionList = []
        self.instance_list_total = []
        self.disk_list_total = []
        self.TotalPageNum = 0
        self.PageSize = 100

    def __get_client(self, region_id=None):
        region_id = region_id if region_id else MY_PROJ_KEY['RegionId']
        self.client = AcsClient(self.access_key, self.secret, region_id)

    def __do_action(self, request):
        try:
            request.set_accept_format('json')
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def __get_total_page_num(self, PageNum=1, PageSize=1):
        '''
        获取ECS总数，及当前页ECS列表
        :param PageNum: 页ID
        :param PageSize: 页大小
        :return:
        '''
        request = DescribeInstancesRequest()
        request.set_PageNumber(PageNum)
        request.set_PageSize(PageSize)
        response = self.__do_action(request)
        if self.TotalPageNum != 0:
            ins_obj = response['Instances']['Instance']
            self.instance_list_total.extend(ins_obj)
            return

        else:
            if int(response['TotalCount']) % self.PageSize != 0:
                self.TotalPageNum = int(
                    response['TotalCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize)
            return self.TotalPageNum

    def __get_disk_total_page_num(self, PageNum=1, PageSize=1):
        request = DescribeDisksRequest()
        request.set_PageSize(PageSize)
        request.set_PageNumber(PageNum)
        response = self.__do_action(request)

        if self.TotalPageNum != 0:
            ins_obj = response['Disks']['Disk']
            self.disk_list_total.extend(ins_obj)
            return

        else:
            if int(response['TotalCount']) % self.PageSize != 0:
                self.TotalPageNum = int(
                    response['TotalCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize)
            return self.TotalPageNum

    def __get_ecs_of_region(self, region):
        '''
        按区获取
        :param region:
        :return:
        '''
        self.TotalPageNum = 0
        self.__get_client(region)
        self.__get_total_page_num()
        # self.instance_list_obj.clear()
        list(
            map(self.__get_total_page_num, range(1, self.TotalPageNum + 1),
                [self.PageSize] * self.TotalPageNum))
        return

    def __get_disk_of_region(self, region):
        '''
        按区获取硬盘
        :param region:
        :return:
        '''
        self.TotalPageNum = 0
        self.__get_client(region)
        self.__get_disk_total_page_num()
        list(
            map(self.__get_disk_total_page_num, range(1,
                                                      self.TotalPageNum + 1),
                [self.PageSize] * self.TotalPageNum))
        return

    def translate(self, ins):
        '''
        将接口返回的数据翻译成库字段，便于批量插入
        :param ins:
        :return:
        '''

        instrance = {}
        try:
            instrance['disk'] = 0
            instrance['hostname'] = ins['HostName']
            if ins.get('NetworkInterfaces'):
                instrance['host_ip'] = ins['NetworkInterfaces'][
                    'NetworkInterface'][0]['PrimaryIpAddress']
            if ins['PublicIpAddress'].get('IpAddress'):
                ip = ins['PublicIpAddress'].get('IpAddress', '')
                instrance['public_ip'] = ip[0]
            if ins.get('NetworkInterfaces'):
                instrance['mac'] = ins['NetworkInterfaces'][
                    'NetworkInterface'][0]['MacAddress']
            instrance['os'] = ins['OSNameEn']
            instrance['cpu'] = ins['Cpu']
            instrance['memory'] = int(ins['Memory'] / 1024)
            instrance['sn'] = ins['SerialNumber']
            instrance['instance_id'] = ins['InstanceId']
            instrance['instance_name'] = ins['InstanceName']
            instrance['create_time'] = ins['CreationTime']
            instrance['expiration_time'] = ins['ExpiredTime']
            instrance['zone'] = ins['ZoneId']
            instrance['region'] = ins['RegionId']
            instrance['status'] = ins['Status']
            if ins['Status'] != 'Running':
                instrance['power_state'] = 'poweredOff'
            else:
                instrance['power_state'] = 'poweredOn'
            instrance['ostype'] = ins['OSType']
            # instrance['instancechargetype'] = ins['InstanceChargeType']
            # instrance['internetchargetype'] = ins['InternetChargeType']
            instrance['charge_type'] = ins['InstanceChargeType']
            instrance['net_charge_type'] = ins['InternetChargeType']
            instrance['salecycle'] = ins.get('SaleCycle', '')
            instrance['comment'] = ins.get('Description', '')
            instrance['specs'] = {
                'name': ins['InstanceType'],
                'family': ins['InstanceTypeFamily'],
                'cpu': ins['Cpu'],
                'memory': ins['Memory']
            }
        except Exception as e:
            logger.error(e)
        return instrance

    def get_ecs(self):
        '''
        获取所有ECS信息
        :return:
        '''
        self.get_region()
        list(map(self.__get_ecs_of_region, self.regionList))
        pool = Pool(50)
        ins_list_total = list(
            pool.map(self.translate, self.instance_list_total))
        pool.close()
        pool.join()
        return ins_list_total

    def get_disk(self):
        '''
        获取所有硬盘信息
        :return:
        '''

        self.PageSize = 100
        self.get_region()
        list(map(self.__get_disk_of_region, self.regionList))

        return self.disk_list_total

    def get_region(self):
        '''
        获取账户支持的所有区域id
        :return:
        '''
        self.__get_client()
        request = DescribeRegionsRequest()
        response = self.__do_action(request)
        region_list = response.get('Regions').get('Region')
        assert response is not None
        assert region_list is not None
        self.regionList = list(
            map(print_dict_key, region_list, ['RegionId'] * len(region_list)))
        return self.regionList


class RDS:
    '''
    获取阿里云当前账户下所有的RDS实例及其详细信息
    参考文档：https://help.aliyun.com/document_detail/26232.html?spm=a2c4g.11186623.6.1450.57ea75abVgYvHr
    参考文档：https://help.aliyun.com/document_detail/26231.html?spm=a2c4g.11186623.6.1449.760a75abInu9sW
    '''
    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id if access_key_id else MY_PROJ_KEY['AK']
        self.secret = access_key_secret if access_key_secret else MY_PROJ_KEY[
            'SK']
        self.client = None
        self.currentPage = []
        self.regionList = []
        self.instance_list_total = []
        self.instance_ids_list = []
        self.TotalPageNum = 0
        self.PageSize = 100

    def __get_client(self, region_id=MY_PROJ_KEY['RegionId']):
        self.client = AcsClient(self.access_key, self.secret, region_id)

    def __do_action(self, request):
        try:
            request.set_accept_format('json')
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def __get_total_page_num(self, PageNum=1, PageSize=1):
        '''
        获取RDS总数，及当前页RDS列表
        :param PageNum: 页ID
        :param PageSize: 页大小
        :return:
        '''
        request = DescribeDBInstancesRequest()
        request.set_PageNumber(PageNum)
        request.set_PageSize(PageSize)
        response = self.__do_action(request)
        if self.TotalPageNum != 0:
            ins_obj = response['Items']['DBInstance']
            self.instance_list_total.extend(ins_obj)
            return
        else:
            if int(response['TotalRecordCount']) % self.PageSize != 0:
                self.TotalPageNum = int(
                    response['TotalRecordCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalRecordCount'] /
                                        self.PageSize)
            return self.TotalPageNum

    def __get_rds_of_region(self, region):
        '''
        按区获取
        :param region:
        :return:
        '''
        self.TotalPageNum = 0
        self.__get_client(region)
        self.__get_total_page_num()
        # self.instance_list_obj.clear()
        list(
            map(self.__get_total_page_num, range(1, self.TotalPageNum + 1),
                [self.PageSize] * self.TotalPageNum))
        return

    def __get_rds_ids(self):
        '''
        获取所有RDS信息
        :return:
        '''

        list(map(self.__get_rds_of_region, self.regionList))
        self.instance_ids_list = list(
            map(print_dict_key, self.instance_list_total,
                ['DBInstanceId'] * len(self.instance_list_total)))
        self.instance_list_total = []
        return self.instance_ids_list

    def __get_rds_attribute(self, ins_id):
        request = DescribeDBInstanceAttributeRequest()
        request.set_DBInstanceId(ins_id)
        response = self.__do_action(request)
        self.instance_list_total.extend(
            response['Items']['DBInstanceAttribute'])

    def translate(self, ins):
        '''
        将接口返回的数据翻译成库字段，便于批量插入
        :param ins:RDS Instance ID
        :return: 与表字段匹配的Mapping
        '''

        instrance = {}
        try:
            instrance['instance_id'] = ins['DBInstanceId']
            instrance['instance_name'] = ins.get('DBInstanceDescription')
            instrance['instance_type'] = ins.get('DBInstanceType')
            instrance['instancenet_type'] = ins.get('DBInstanceNetType')
            instrance['vpc_cloud_instance_id'] = ins.get('VpcCloudInstanceId')
            instrance['vpc_id'] = ins.get('VpcId')
            instrance['connection_mode'] = ins.get('ConnectionMode')
            instrance['vswitch_id'] = ins.get('VSwitchId')
            instrance['host_address'] = ins.get('ConnectionString')
            instrance['port'] = ins.get('Port')
            instrance['engine'] = ins.get('Engine')
            instrance['engine_version'] = ins.get('EngineVersion')
            instrance['status'] = ins.get('DBInstanceStatus')
            instrance['lock_mode'] = ins.get('LockMode')

            # 如果有被锁定，则取其原因
            if ins.get('LockReason'):
                instrance['lock_reason'] = ins.get('LockReason')

            instrance['resource_group_id'] = ins.get('ResourceGroupId')
            instrance['zone'] = ins.get('ZoneId')
            instrance['region'] = ins.get('RegionId')

            instrance['category'] = ins.get('Category')

            # 如果有设置时区，则取值
            if ins.get('TimeZone'):
                instrance['timezone'] = ins.get('TimeZone')

            instrance['charge_type'] = ins.get('PayType')
            instrance['comment'] = ins.get('DBInstanceDescription')

            # 如果有只读实例，则取其ID
            if ins['ReadOnlyDBInstanceIds'].get('ReadOnlyDBInstanceId'):
                instrance['readonly_ins'] = ins['ReadOnlyDBInstanceIds'].get(
                    'ReadOnlyDBInstanceId')

            instrance['maintain_time'] = ins.get('MaintainTime')
            instrance['create_time'] = ins.get('CreationTime')
            instrance['expiration_time'] = ins.get('ExpireTime')

            instrance['cpu'] = ins.get('DBInstanceCPU')

            instrance['memory'] = int(ins.get('DBInstanceMemory')) / 1024

            instrance['disk'] = ins['DBInstanceStorage']

            # 规格
            instrance['specs'] = {
                'name': ins['DBInstanceClass'],
                'family': ins['DBInstanceClassType'],
                'cpu': instrance['cpu'],
                'memory': instrance['memory'],
                'max_conn': ins['MaxConnections'],
                'max_iops': ins['MaxIOPS'],
                'db_max_quantity': ins['DBMaxQuantity'],
                'account_max_quantity': ins['AccountMaxQuantity']
            }

        except Exception as e:
            logger.error(e)
        return instrance

    def get_rds(self):
        '''
        获取所有RDS信息
        :return:
        '''
        self.get_region()
        # 获取所有区域下的RDS实例ID
        self.__get_rds_ids()
        # 初始化连接
        self.__get_client()
        # 获取所有RDS详细配置信息
        list(map(self.__get_rds_attribute, self.instance_ids_list))
        # 字段翻译
        pool = Pool(50)
        instance_list_total = list(
            pool.map(self.translate, self.instance_list_total))
        pool.close()
        pool.join()
        return instance_list_total

    def get_region(self):
        '''
        获取账户支持的所有区域id
        :return:
        '''
        self.__get_client()
        request = DescribeRegionsRequest()
        response = self.__do_action(request)
        region_list = response.get('Regions').get('Region')
        assert response is not None
        assert region_list is not None
        self.regionList = list(
            map(print_dict_key, region_list, ['RegionId'] * len(region_list)))
        return self.regionList


class Domain:
    def __init__(self, access_key=None, secret=None):
        self.page_size = 50
        self.access_key = access_key if access_key else MY_PROJ_KEY['AK']
        self.secret = secret if secret else MY_PROJ_KEY['SK']
        self.client = AcsClient(self.access_key, self.secret,
                                MY_PROJ_KEY['RegionId'])
        self.TotalPageNum = 0
        self.TotalItemNum = 0
        self.currentPage = []

    def __do_action(self, request):
        try:
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def __get_total_page_num(self, PageNum=1):
        '''
        获取总域名数，及当前页域名列表
        :param PageNum:
        :return:
        '''
        request = QueryDomainListRequest()
        request.set_accept_format('json')
        request.set_PageNum(PageNum)
        request.set_PageSize(int(self.page_size))
        response = self.__do_action(request)
        if response:
            self.currentPage = response['Data']['Domain']
            if PageNum == 1:
                self.TotalPageNum = int(response['TotalPageNum'])

    def __get_domainInfo(self, domainIns):
        '''
        获取域名详细注册信息，同whois查询结果
        :return:
        '''
        request = QueryDomainByInstanceIdRequest()
        request.set_InstanceId(domainIns)
        return self.__do_action(request)

    def __translate(self, domain):
        domainInfo = {}
        domainInfo['name'] = domain['DomainName']
        domainInfo['domain_isp'] = 1
        domainInfo['domain_id'] = domain['InstanceId']
        domainInfo['domain_status'] = int(domain['DomainStatus'])
        domainInfo['domain_type'] = domain['DomainType']
        domainInfo['registrant_type'] = int(domain['RegistrantType'])
        domainInfo['registration_date'] = domain['RegistrationDate']
        domainInfo['expiration_date'] = domain['ExpirationDate']
        info = self.__get_domainInfo(domain['InstanceId'])
        domainInfo['nameserver_master'] = info['DnsList']['Dns'][0]
        domainInfo['nameserver_slave'] = info['DnsList']['Dns'][1]
        domainInfo['owner'] = info['ZhRegistrantOrganization']
        domainInfo['email'] = info['Email']
        domainInfo['verification_status'] = info[
            'DomainNameVerificationStatus']
        return domainInfo

    def get_domainListInfo(self):
        domainListInfo = []
        if not self.client: return []
        self.__get_total_page_num()
        for page in range(1, self.TotalPageNum + 1):
            self.__get_total_page_num(page)
            domainListInfo.extend(list(map(self.__translate,
                                           self.currentPage)))
        return domainListInfo


class OSS:
    """
    不区分region
    """
    def __init__(self,
                 access_key_id=None,
                 access_key_secret=None,
                 region_id=None):
        self.access_key_id = access_key_id if access_key_id else MY_PROJ_KEY[
            'AK']
        self.access_key_secret = access_key_secret if access_key_secret else MY_PROJ_KEY[
            'SK']
        self.region_id = region_id if region_id else MY_PROJ_KEY['RegionId']
        self.bucket_names = []
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)

    def __get_bucket_name(self):
        service = oss2.Service(self.auth,
                               'http://oss-%s.aliyuncs.com' % self.region_id)
        for bucket_item in oss2.BucketIterator(service):
            region_id = bucket_item.location.split("oss-")[1]
            self.bucket_names.append([region_id, bucket_item.name])
        return self.bucket_names

    def __get_bucket_detail(self, region_id, bucket_name):
        try:
            bucket = {}
            buckets = oss2.Bucket(self.auth,
                                  'http://oss-%s.aliyuncs.com' % region_id,
                                  bucket_name)
            bucket_info = buckets.get_bucket_info()
            bucket['name'] = bucket_info.name
            bucket['storage_class'] = bucket_info.storage_class
            bucket['creation_date'] = bucket_info.creation_date
            bucket['intranet_endpoint'] = bucket_info.intranet_endpoint
            bucket['extranet_endpoint'] = bucket_info.extranet_endpoint
            bucket['owner'] = bucket_info.owner.display_name
            bucket['grant'] = bucket_info.acl.grant
            bucket['location'] = bucket_info.location
            bucket[
                'data_redundancy_type'] = bucket_info.data_redundancy_type  # Bucket的数据容灾类型
        except:
            err = '%s [%s] happend on %s line at %s' % (
                sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)
        return bucket

    def get_bucket(self):
        self.__get_bucket_name()
        bucket_info_list = []
        for item in self.bucket_names:
            bucket_info = self.__get_bucket_detail(item[0], item[1])
            bucket_info_list.append(bucket_info)
        return bucket_info_list


class Vpc:
    # 区分auth区域
    def __init__(self):
        self.vpc_list = []
        self.vswitch_id_list = []
        self.vswitch_list = []

    @staticmethod
    def vpc_client(
        access_key_id=None,
        access_key_secret=None,
    ) -> Vpc20160428Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            access_key_id=access_key_id
            if access_key_id else MY_PROJ_KEY['AK'],
            access_key_secret=access_key_secret
            if access_key_secret else MY_PROJ_KEY['SK'])
        # 访问的域名
        config.endpoint = 'vpc.aliyuncs.com'
        return Vpc20160428Client(config)

    def __translate(self, ins):
        vpc = {}
        try:
            vpc['vpc_id'] = ins['VpcId']
            vpc['vpc_name'] = ins['VpcName']
            vpc['status'] = ins['Status']
            vpc['creation_time'] = ins['CreationTime']
            vpc['nat_gateway_ids'] = ins['NatGatewayIds']['NatGatewayIds']
            vpc['cidr_block'] = ins['CidrBlock']
            vpc['secondary_cidr_blocks'] = ins['SecondaryCidrBlocks'][
                'SecondaryCidrBlock']
            vpc['description'] = ins['Description']
            vpc['vswitch_ids'] = ins['VSwitchIds']['VSwitchId']
            vpc['router_table_ids'] = ins['RouterTableIds']['RouterTableIds']
            vpc['is_default'] = ins['IsDefault']
            vpc['region_id'] = ins['RegionId']
            vpc['vrouter_id'] = ins['VRouterId']
            vpc['cen_status'] = ins['CenStatus']
            vpc['resource_group_id'] = ins['ResourceGroupId']
            vpc['user_cidr'] = ins['UserCidrs']['UserCidr']
        except:
            err = '%s [%s] happend on %s line at %s' % (
                sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)
        return vpc

    def __get_vpc_info(self, region_id):
        try:
            vpc_request = vpc_20160428_models.DescribeVpcsRequest(
                region_id=region_id)
            client = self.vpc_client()
            vpc_response = client.describe_vpcs(vpc_request)

            vpc_info = vpc_response.body.to_map()['Vpcs']['Vpc']
            if vpc_info:
                self.vpc_list.extend(vpc_info)
                for item in vpc_info:
                    if item['VSwitchIds']['VSwitchId']:
                        self.vswitch_id_list.extend(
                            item['VSwitchIds']['VSwitchId'])
        except:
            err = '%s [%s] happend on %s line at %s' % (
                sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

    def __get_vswitch(self, vswitch_id):
        try:
            client = AliCloud.auth_client()
            request = DescribeVSwitchAttributesRequest.DescribeVSwitchAttributesRequest(
            )
            request.set_VSwitchId(vswitch_id)
            response = client.do_action_with_exception(request)
            response_json = json.loads(response)
            return response_json
        except ServerException as e:
            logger.error(e)
        except ClientException as e:
            logger.error(e)

    def __vswitch_translate(self, ins):
        vswitch = {}
        vswitch['status'] = ins['Status']
        vswitch['is_default'] = ins['IsDefault']
        vswitch['description'] = ins['Description']
        vswitch['network_acl_id'] = ins['NetworkAclId']
        vswitch['resource_group_id'] = ins['ResourceGroupId']
        vswitch['zone_id'] = ins['ZoneId']
        vswitch['ip_address_count'] = ins['AvailableIpAddressCount']
        vswitch['vswitch_id'] = ins['VSwitchId']
        vswitch['cidr_block'] = ins['CidrBlock']
        vswitch['route_table'] = ins['RouteTable']
        vswitch['vpc_id'] = ins['VpcId']
        vswitch['create_time'] = ins['CreationTime']
        vswitch['vswitch_name'] = ins['VSwitchName']
        vswitch['cloud_resources'] = ins['CloudResources']
        return vswitch

    def get_vpc(self):
        region_list = AliCloud.get_region_ids()
        list(map(self.__get_vpc_info, region_list))
        vpc_info_list = list(map(self.__translate, self.vpc_list))
        vswitch_infos = list(map(self.__get_vswitch, self.vswitch_id_list))
        vswitch_infos_list = list(map(self.__vswitch_translate, vswitch_infos))
        infos = {'vpc': vpc_info_list, 'vswitch': vswitch_infos_list}
        return infos


class Cdn:
    def create_client(
        self,
        access_key_id=None,
        access_key_secret=None,
    ) -> Cdn20180510Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            access_key_id=access_key_id
            if access_key_id else MY_PROJ_KEY['AK'],
            access_key_secret=access_key_secret
            if access_key_secret else MY_PROJ_KEY['SK'])
        # 访问的域名
        config.endpoint = 'cdn.aliyuncs.com'
        return Cdn20180510Client(config)

    def __get_cdn(self, client):
        try:
            describe_user_domains_request = cdn_20180510_models.DescribeUserDomainsRequest(
            )
            cdn_info = client.describe_user_domains(
                describe_user_domains_request)
            cdn = cdn_info.body.domains.to_map()['PageData']
            return cdn
        except Exception as e:
            return f'Error:{e}'

    def __translate(self, ins):
        instance = {}
        instance['gmt_created'] = ins['GmtCreated']
        instance['gmt_modified'] = ins['GmtModified']
        instance['domain_name'] = ins['DomainName']
        instance['cname'] = ins['Cname']
        instance['cdn_type'] = ins['CdnType']
        instance['coverage'] = ins['Coverage']
        instance['sandbox'] = ins['Sandbox']
        instance['resource_group_id'] = ins['ResourceGroupId']  # 资源组ID
        instance['ssl_protocol'] = ins['SslProtocol']
        instance['domain_status'] = ins['DomainStatus']
        instance['description'] = ins['Description']
        instance['sources'] = ins['Sources']['Source']
        return instance

    def get_cdn_info(self, client=None):
        client = client if client else self.create_client()
        cdns = self.__get_cdn(client)
        cdn_infos = list(map(self.__translate, cdns))
        return cdn_infos


class Slb:
    def __init__(self):
        self.slb_list = []

    def create_client(
        self,
        access_key_id=None,
        access_key_secret=None,
    ) -> Slb20140515Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            access_key_id=access_key_id
            if access_key_id else MY_PROJ_KEY['AK'],
            access_key_secret=access_key_secret
            if access_key_secret else MY_PROJ_KEY['SK'])
        # 访问的域名
        config.endpoint = 'slb.aliyuncs.com'
        return Slb20140515Client(config)

    def __get_slb_info(self, region_id):
        client = self.create_client()
        describe_load_balancers_request = slb_20140515_models.DescribeLoadBalancersRequest(
            region_id=region_id)
        slb_response = client.describe_load_balancers(
            describe_load_balancers_request)
        slb_info = slb_response.body.to_map()['LoadBalancers']['LoadBalancer']
        # slb_info = slb_response.body.to_map()
        if slb_info:
            self.slb_list.extend(slb_info)

    def __translate(self, ins):
        slb_info = {}
        slb_info['slb_name'] = ins['LoadBalancerName']
        slb_info['slb_id'] = ins['LoadBalancerId']
        slb_info['vpc_id'] = ins['VpcId']
        slb_info['pay_type'] = ins['PayType']
        slb_info['create_time'] = ins['CreateTime']
        slb_info['address'] = ins['Address']
        slb_info['address_type'] = ins['AddressType']
        slb_info['network_type'] = ins['NetworkType']
        slb_info['address_version'] = ins['AddressIPVersion']
        slb_info['bandwidth'] = ins['Bandwidth']
        slb_info['slave_zone_id'] = ins['SlaveZoneId']
        slb_info['master_zone_id'] = ins['MasterZoneId']
        slb_info['net_charge_type'] = ins['InternetChargeTypeAlias']
        slb_info['net_charge_type_id'] = ins['InternetChargeType']
        slb_info['slb_spec'] = ins['LoadBalancerSpec']
        slb_info['slb_region_id'] = ins['RegionId']
        slb_info['vswitch_id'] = ins['VSwitchId']
        slb_info['slb_status'] = ins['LoadBalancerStatus']
        slb_info['resource_grp_id'] = ins['ResourceGroupId']
        return slb_info

    def get_slb(self):
        region_list = AliCloud.get_region_ids()
        skip_region = ['cn-nanjing']
        region_list = list(set(region_list).difference(set(skip_region)))
        list(map(self.__get_slb_info, region_list))
        slb_infos = list(map(self.__translate, self.slb_list))
        return slb_infos


class DomainRecords:  # 不区分region
    def __init__(self, **kwargs):
        self.access_key_id = kwargs.get('access_key_id', None)
        self.access_key_secret = kwargs.get('access_key_secret', None)
        self.region_id = kwargs.get('region_id', None)
        self.page_size = 500
        self.domain_name = kwargs.get('domain_name')

    # 鉴权
    @staticmethod
    def __create_client(access_key_id=None,
                        access_key_secret=None,
                        region_id=None) -> Alidns20150109Client:
        access_key_id = access_key_id if access_key_id else MY_PROJ_KEY['AK']
        access_key_secret = access_key_secret if access_key_secret else MY_PROJ_KEY[
            'SK']
        region_id = region_id if region_id else MY_PROJ_KEY['RegionId']
        config = open_api_models.Config(access_key_id=access_key_id,
                                        access_key_secret=access_key_secret)
        # 访问的域名
        config.endpoint = f'alidns.%s.aliyuncs.com' % region_id
        return Alidns20150109Client(config)

    def __get_page_num(self, client):
        page_number = 1
        # client = DomainRecords.__create_client(self.access_key_id, self.access_key_secret, self.region_id)
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name=self.domain_name, page_size=1, page_number=1)
        total_count = client.describe_domain_records(
            describe_domain_records_request).body.to_map()['TotalCount']
        if total_count:
            if total_count % self.page_size != 0:
                page_number = int(total_count / self.page_size) + 1
            else:
                page_number = int(total_count / self.page_size)
        return page_number

    def __get_dns_records(self):
        client = DomainRecords.__create_client(self.access_key_id,
                                               self.access_key_secret,
                                               self.region_id)
        page_num = self.__get_page_num(client)
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name=self.domain_name,
            page_size=self.page_size,
            page_number=page_num)
        reps = client.describe_domain_records(
            describe_domain_records_request).body.to_map(
            )['DomainRecords']['Record']
        return reps

    def __translate(self, ins):
        records = {}
        records['status'] = ins['Status']
        records['type'] = ins['Type']
        records['ttl'] = ins['TTL']
        records['record_id'] = ins['RecordId']
        records['RR'] = ins['RR']
        records['domain_name'] = ins['DomainName']
        records['weight'] = ins.get('Weight', None)
        records['value'] = ins['Value']
        records['line'] = ins['Line']
        records['locked'] = ins['Locked']
        records['remark'] = ins.get('Remark', None)
        return records

    def get_dns_records_info(self):
        records_list = self.__get_dns_records()
        records_info = list(map(self.__translate, records_list))
        return records_info

    def new_record(self,
                   rr,
                   type,
                   value,
                   ttl=600,
                   priority=None,
                   line=None):  # 添加dns记录
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        add_req = alidns_20150109_models.AddDomainRecordRequest()
        add_req.domain_name = self.domain_name
        add_req.rr = rr
        add_req.type = type
        add_req.value = value
        if ttl:
            add_req.ttl = ttl
        if priority:
            add_req.priority = priority
        if line:
            add_req.line = line
        rlt = dnsclient.add_domain_record(add_req).body.to_map()
        return rlt

    def delete_record(self, record_id):  # 删除dns记录
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        del_req = alidns_20150109_models.DeleteDomainRecordRequest(
            record_id=record_id)
        rlt = dnsclient.delete_domain_record(del_req).body.to_map()
        return rlt

    def update_record(self,
                      record_id,
                      rr,
                      type,
                      value,
                      ttl=600,
                      priority=None,
                      line=None):  # 修改dns记录
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        update_req = alidns_20150109_models.UpdateDomainRecordRequest()
        update_req.record_id = str(record_id)
        update_req.rr = str(rr)
        update_req.type = str(type)
        update_req.value = str(value)
        update_req.ttl = int(ttl)
        if priority:
            update_req.priority = int(priority)
        if line:
            update_req.line = str(line)
        rlt = dnsclient.update_domain_record(update_req).body.to_map()
        return rlt

    def update_record_remark(self, record_id, remark):  # 修改dns记录的备注
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        update_remark_req = alidns_20150109_models.UpdateDomainRecordRemarkRequest(
            record_id=record_id, remark=remark)
        rlt = dnsclient.update_domain_record_remark(
            update_remark_req).body.to_map()
        return rlt

    def set_record_status(self, record_id, status):  # 设置记录状态
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        set_status = alidns_20150109_models.SetDomainRecordStatusRequest(
            record_id=record_id, status=status)
        rlt = dnsclient.set_domain_record_status(set_status).body.to_map()
        return rlt

    def get_domain_ns(self):  #
        dnsclient = DomainRecords.__create_client(self.access_key_id,
                                                  self.access_key_secret,
                                                  self.region_id)
        domain_ns = alidns_20150109_models.DescribeDomainNsRequest(
            domain_name=self.domain_name)
        rlt = dnsclient.describe_domain_ns(domain_ns).body.to_map()
        return rlt
