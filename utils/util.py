# -*- coding:utf-8 -*-
# pylint: disable=duplicate-code
'''

Some tool sets

'''
import time
import datetime
import shortuuid
import paramiko


def now():
    '''
    datetime
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))



def time_trans(utc_time: str):  # UTC时间转化本地时间
    if utc_time:
        utc_len = len(utc_time.split(':'))
        if utc_len == 2:
            UTC_FORMAT = "%Y-%m-%dT%H:%MZ"
        elif utc_len == 3:
            if len(utc_time.split('.')) == 2:
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
            else:
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        utcTime = datetime.datetime.strptime(utc_time, UTC_FORMAT)
        trans = utcTime + datetime.timedelta(hours=8)
        return str(trans)


def gen_shortuuid():
    uuid = shortuuid.ShortUUID().random(length=20)
    return uuid


class LinuxRemoteConn:  # 基于paramiko实现linux远程执行
    def __init__(self,
                 host_ip,
                 password,
                 username='root',
                 port=22,
                 auth_type=0):
        self.srv_info = {
            'hostname': host_ip,
            'password': password,
            'port': port,  # 默认22端口
            'username': username  # 默认root
        }
        self.auth_type = auth_type  # 0:密码|1:文件

    def __conn(self):  # 封装ssh连接
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机
        if not self.auth_type:
            ssh_client.connect(**self.srv_info, timeout=50)
        else:
            private = paramiko.RSAKey.from_private_key_file(self.password)
            self.srv_info = self.srv_info.pop('password')
            ssh_client.connect(**self.srv_info, pkey=private, timeout=50)
        self.__sshconn = ssh_client

    def __sftpConn(self):  # 封装sftp连接
        transport = self.__sshconn.get_transport()
        # 创建sftp实例
        sftp = paramiko.SFTPClient.from_transport(transport)
        self.__sftp = sftp

    def sshCmd(self, cmd):  # 封装命令执行
        stdin, stdout, stderr = self.__sshconn.exec_command(cmd)
        stderr_info = stderr.read().decode('utf8')
        stdout_info = stdout.read().decode('utf8').split('\n')
        if stderr_info == "":
            return stdout_info  # list
        else:
            return False, (stderr_info, stdout_info)

    def sftpUpload(self, local_path, remote_path):  # 封装文件上传
        push_info = self.__sftp.put(local_path, remote_path)
        return push_info

    def sftpDownload(self, local_path, remote_path):  # 封装文件下载
        pull_info = self.__sftp.get(remote_path, local_path, callback=None)
        return pull_info

    def run_cmd(self, cmd):  # 执行命令/脚本
        self.__conn()
        result = self.sshCmd(cmd)
        self.__sshconn.close()  # 关闭连接
        return result

    def run_sftp(self, sftp_type, local_path, remote_path):  # 远程上传/下载
        self.__conn()
        self.__sftpConn()
        if "pull" in sftp_type:
            result = self.sftpDownload(local_path, remote_path)
        else:
            result = self.sftpUpload(local_path, remote_path)
        self.__sftp.close()  # 关闭连接
        return result
