import CloudFlare
import json


class CloudFlareApi:
    def __init__(self, token, email=None):
        self.token = token
        self.email = email

    @staticmethod
    def cf_auth(token, email=None):
        if email:
            cf = CloudFlare.CloudFlare(token=token, email=email)
        else:
            cf = CloudFlare.CloudFlare(token=token)
        return cf

    def get_zone(self, zone_name=None):  # 获取site信息
        # status active, pending, initializing, moved, deleted, deactivated
        cf = CloudFlareApi.cf_auth(token=self.token)
        if zone_name:
            # params = {'name': 'pbrmax.com'}
            params = {'name': zone_name}
            zone_info = cf.zones.get(params=params)
            return zone_info
        else:
            zone_infos = cf.zones.get()
            return zone_infos

    def new_zone(self):
        pass

    def get_dns_records(self, zone_id):  # 获取dns record信息
        cf = CloudFlareApi.cf_auth(token=self.token)
        dns_records_list = cf.zones.dns_records.get(zone_id)
        return dns_records_list

    def new_record(self,
                   zone_id,
                   name,
                   type,
                   content,
                   ttl=1,
                   priority=None,
                   proxied=None):  # 新建dns record
        '''

        :param zone_id:str domain_id
        :param name:str dns record 名称  max length: 255
        :param type:str record类型 A,AAAA,CNAME,HTTPS,TXT,SRV,LOC,MX,NS,CERT,DNSKEY,DS,NAPTR,SMIMEA,SSHFP,SVCB,TLSA,URI
        :param content:str 记录内容
        :param ttl:int 生存时间 60-86400或者1自动
        :param priority:int 优先级 0-65535
        :param proxied:bool  代理状态 true(已代理)|false(仅限DNS)
        :return:
        '''
        cf = CloudFlareApi.cf_auth(token=self.token)
        dns_record = {
            'name': name,
            'type': type,
            'content': content,
            'ttl': ttl
        }
        if priority:
            dns_record.update({'priority': priority})
        if proxied:
            dns_record.update({'proxied': proxied})
        rlt = cf.zones.dns_records.post(zone_id, data=json.dumps(dns_record))
        return rlt

    def delete_record(self, zone_id, dns_record_id):  # 删除record
        cf = CloudFlareApi.cf_auth(token=self.token)
        rlt = cf.zones.dns_records.delete(zone_id, dns_record_id)
        return rlt

    def put_record(self,
                   zone_id,
                   dns_record_id,
                   name,
                   type,
                   content,
                   ttl=1,
                   proxied=None,
                   priority=None):  # 更新record
        cf = CloudFlareApi.cf_auth(token=self.token)
        dns_record = {
            'name': name,
            'type': type,
            'content': content,
            'ttl': ttl
        }
        if proxied:
            dns_record.update({'proxied': proxied})
        if priority:
            dns_record['priority'] = priority
        rlt = cf.zones.dns_records.post(zone_id,
                                        dns_record_id,
                                        data=dns_record)
        return rlt

    def patch_record(self,
                     zone_id,
                     dns_record_id,
                     type=None,
                     name=None,
                     content=None,
                     ttl=None,
                     proxied=None):
        cf = CloudFlareApi.cf_auth(token=self.token)
        dns_record = {}
        if type:
            dns_record['type'] = type
        if name:
            dns_record['name'] = name
        if content:
            dns_record['content'] = content
        if ttl:
            dns_record['ttl'] = ttl
        if proxied:
            dns_record['proxied'] = proxied
        rlt = cf.zones.dns_records.patch(zone_id,
                                         dns_record_id,
                                         data=dns_record)
        return rlt
