from rest_framework import serializers
from .models import DeviceType, ZoneInfo, DeviceStatus, IdleAssets, IDC, Machine, RDS, Disk, Domain, Oss, Vpc, CDN, Slb, \
    Switch, BusinessServices, BusinessProject, BusinessEnvironment, ServiceToEnv, DnsRecords
import json


class DeviceTypeSerializers(serializers.ModelSerializer):
    """user serializers"""
    class Meta:
        model = DeviceType
        fields = "__all__"


class ZoneInfoSerializers(serializers.ModelSerializer):
    """zone info serializers"""
    class Meta:
        model = ZoneInfo
        fields = "__all__"


class DeviceStatusSerializers(serializers.ModelSerializer):
    """device status serializers"""
    class Meta:
        model = DeviceStatus
        fields = "__all__"


class IDCSerializers(serializers.ModelSerializer):
    """idc serializers"""
    class Meta:
        model = IDC
        fields = "__all__"


class IdleAssetsSerializers(serializers.ModelSerializer):
    """idle assets serializers"""
    class Meta:
        model = IdleAssets
        fields = "__all__"


class MachineSerializers(serializers.ModelSerializer):
    """machine serializers"""
    class Meta:
        model = Machine
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        if value.optional:
            data['optional'] = json.loads(value.optional)
        return data


class RDSSerializers(serializers.ModelSerializer):
    """RDS serializers"""
    class Meta:
        model = RDS
        fields = "__all__"


class DiskSerializers(serializers.ModelSerializer):
    """DISK serializers"""
    disk_type = serializers.CharField(source='get_disk_type_display')
    category = serializers.CharField(source='get_category_display')

    class Meta:
        model = Disk
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        data['tags'] = []
        if value.tags:
            data['tags'] = json.loads(value.tags)
        return data


class DomainSerializers(serializers.ModelSerializer):
    """Domain serializers"""
    registrant_type = serializers.CharField(
        source='get_registrant_type_display')

    class Meta:
        model = Domain
        fields = "__all__"


class OssSerializers(serializers.ModelSerializer):
    """Oss serializers"""
    class Meta:
        model = Oss
        fields = "__all__"


class VpcSerializers(serializers.ModelSerializer):
    """Vpc serializers"""
    class Meta:
        model = Vpc
        fields = "__all__"


class CdnSerializers(serializers.ModelSerializer):
    """CDN serializers"""
    cdn_type = serializers.CharField(source='get_cdn_type_display')

    class Meta:
        model = CDN
        fields = "__all__"


class SlbSerializers(serializers.ModelSerializer):
    """Slb serializers"""
    class Meta:
        model = Slb
        fields = "__all__"


class SwitchSerializers(serializers.ModelSerializer):
    """Switch serializers"""
    class Meta:
        model = Switch
        fields = "__all__"


class ServicesSerializers(serializers.ModelSerializer):
    service_type = serializers.CharField(source='get_service_type_display')

    class Meta:
        model = BusinessServices
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        if value.manager:
            data['manager'] = list(filter(None, value.manager.split(',')))
        rel_ips = ServiceToEnv.objects.filter(
            del_tag=0, service_id=value.id).values('rel_ips')
        rel_ips_list = list((filter(None,
                                    [item['rel_ips'] for item in rel_ips])))
        rel_machine = []
        if rel_ips_list:
            for ips_str in rel_ips_list:
                machine_list = [
                    int(ids) for ids in list(filter(None, ips_str.split(',')))
                ]
                rel_machine.extend(machine_list)
        data['rel_machine'] = list(set(rel_machine))
        return data


class EnvironmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessEnvironment
        fields = "__all__"


class ProjectSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessProject
        fields = "__all__"

    def to_representation(self, value):
        data = super().to_representation(value)
        if value.manager:
            data['manager'] = list(filter(None, value.manager.split(',')))
        return data


class DnsRecordsSerializers(serializers.ModelSerializer):
    line = serializers.CharField(source='get_line_display')

    class Meta:
        model = DnsRecords
        fields = "__all__"
