from celery import shared_task
import time
import requests
from django.conf import settings

BaseURL = 'http://127.0.0.1:' + str(settings.CMDB_BACK_PORT)
ITSMURL = settings.ITSMURL


@shared_task
def add2(x, y):
    time.sleep(2)
    return x + y


@shared_task
def machine_get():
    url = BaseURL + "/assets/v1/inner/machine"
    r = requests.post(url)
    return r.json()


@shared_task
def oss_get():
    url = BaseURL + "/assets/v1/inner/oss"
    r = requests.post(url)
    return r.json()


@shared_task
def disk_get():
    url = BaseURL + "/assets/v1/inner/disk"
    r = requests.post(url)
    return r.json()


@shared_task
def domain_get():
    url = BaseURL + "/assets/v1/inner/domain"
    r = requests.post(url)
    return r.json()


@shared_task
def rds_get():
    url = BaseURL + "/assets/v1/inner/rds"
    r = requests.post(url)
    return r.json()


@shared_task
def vpc_get():
    url = BaseURL + "/assets/v1/inner/vpc"
    r = requests.post(url)
    return r.json()


@shared_task
def cdn_get():
    url = BaseURL + "/assets/v1/inner/cdn"
    r = requests.post(url)
    return r.json()


@shared_task
def slb_get():
    url = BaseURL + "/assets/v1/inner/slb"
    r = requests.post(url)
    return r.json()


@shared_task
def approval_get():
    url = ITSMURL
    r = requests.post(url)
    return r.json()


@shared_task
def users_update():
    url = BaseURL + "/users/v1/user-update"
    r = requests.post(url)
    return r.json()


@shared_task
def dnsrecord_get():
    url = BaseURL + "/assets/v1/inner/dnsrecord"
    r = requests.post(url)
    return r.json()
