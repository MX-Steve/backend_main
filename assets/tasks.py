from celery import shared_task
import time
from tools.apis.lcront import sdo_iptables

def add0(x,y):
    time.sleep(2)
    return int(x) + int(y)

@shared_task
def add2(x, y):
    return add0(x,y)

@shared_task
def add3(x, y):
    return add0(x,y)

@shared_task
def siptables(s,d):
    return sdo_iptables(s, d)

@shared_task
def s1iptables(s,d):
    return sdo_iptables(s, d)

@shared_task
def s2iptables(s,d):
    return sdo_iptables(s, d)

@shared_task
def s3iptables(s,d):
    return sdo_iptables(s, d)

@shared_task
def s4iptables(s,d):
    return sdo_iptables(s, d)

@shared_task
def s5iptables(s,d):
    return sdo_iptables(s, d)

# @shared_task
# def machine_get():
#     url = BaseURL + "/assets/v1/inner/machine"
#     r = requests.post(url)
#     return r.json()

