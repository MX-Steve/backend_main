# -*- coding:utf-8 -*-
from jenkins import Jenkins
import sys,os
import logging
from django.conf import settings

#初始化logger
logger = logging.getLogger("djentry.app")
# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djentry.settings')

class JenkinsApi():
    def __init__(self):
        jenkins_host = settings.JENKINS_HOST
        jenkins_user = settings.JENKINS_USER
        jenkins_pwd = settings.JENKINS_PASSWD
        try:
            self.jk = Jenkins(jenkins_host, username = jenkins_user,password = jenkins_pwd)
        except:
            err = '%s [%s] happend on %s line at %s' % (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)
            # print err

    def execute_job(self,job_name, params):
        try:
            self.jk.build_job(job_name, parameters=params)
        except:
            err = '%s [%s] happend on %s line at %s' % (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

    def get_next_buildnum(self,job_name):
        try:
            next_build_number = self.jk.get_job_info(job_name)['nextBuildNumber']
            return next_build_number
        except:
            err = '%s [%s] happend on %s line at %s' % (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

    def get_jenkins_log(self, job_name, build_num):
        try:
            log = self.jk.get_build_console_output(job_name, build_num)
            return log.strip()
        except:
            err = '%s [%s] happend on %s line at %s' % (
            sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno, os.path.basename(__file__))
            logger.error(err)

if __name__ == '__main__':
    JenkinsApi = JenkinsApi()
    print(JenkinsApi.get_next_buildnum('devJob'))
    # JenkinsApi.execute_job('devJob')
    print(JenkinsApi.get_jenkins_log('devJob', 4))