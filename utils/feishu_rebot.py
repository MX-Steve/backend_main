import json
import requests
import base64
import hmac
import time
from hashlib import sha256

class FeishuRobot():
    def __init__(self, url, secret):
        self.url = url
        self.secret = secret
        self.timestamp = str(round(time.time()))
        self.sign = ""
    
    def sign_generate(self):
        key = f'{self.timestamp}\n{self.secret}'
        key_enc = key.encode('utf-8')
        msg = ""
        msg_enc = msg.encode('utf-8')
        hmac_code = hmac.new(key_enc, msg_enc, digestmod=sha256).digest()
        self.sign = base64.b64encode(hmac_code).decode('utf-8')
    
    def send(self, msg):
        payload_message = {
            "timestamp": self.timestamp,
            "sign": self.sign,
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST",
                                self.url,
                                headers=headers,
                                data=json.dumps(payload_message))
        print(response.text)


if __name__ == '__main__':
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/57210d66-1c63-49a4-9be4-72db49f21780"
    secret = "HUwQMaclGibuYPKguibiyf"
    msg = """abcdefg.<at user_id="all">所有人</at>"""
    # <at user_id="ou_xxx">Name</at> //取值必须使用ou_xxxxx格式的 open_id 来at指定人
    robot = FeishuRobot(url, secret)
    robot.sign_generate()
    robot.send(msg)