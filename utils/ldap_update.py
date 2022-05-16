import ldap
import os
import uuid
import pymysql
import json
import requests


def is_all_chinese(str):
    for _char in str:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
    return True


def request_method(url, headers, data):
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    return r.json()


class LDAP:
    def __init__(self):
        self.connect = ldap.initialize(os.environ["AUTH_LDAP_SERVER_URI"])
        self.connect.set_option(ldap.OPT_REFERRALS, 0)
        self.connect.simple_bind_s(os.environ["AUTH_LDAP_BIND_DN"],
                                   os.environ["AUTH_LDAP_BIND_PASSWORD"])
        self.db = pymysql.connect(host=os.environ["CLOVER_MYSQL_HOST"],
                                  user=os.environ["CLOVER_MYSQL_USER"],
                                  password=os.environ["CLOVER_MYSQL_PASSWORD"],
                                  database=os.environ["CLOVER_MYSQL_DB"])
        self.cursor = self.db.cursor()
        self.app_id = os.environ["HELLO_APP_ID"]
        self.app_secret = os.environ["HELLO_APP_SECRET"]
        self.headers = {
            "content-type": "application/json; charset=utf-8",
            "Authorization": ""
        }

    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"content-type": "application/json; charset=utf-8"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        res = request_method(url, headers, data)
        if res["code"] == 0:
            self.headers[
                "Authorization"] = "Bearer " + res["tenant_access_token"]

    def get_ldap_user(self):
        data = []
        result = self.connect.search_s(os.environ["USER_SEARCH"],
                                       ldap.SCOPE_SUBTREE)
        for item in result:
            obj = item[1]
            keys = obj.keys()
            if "sn" in keys and \
                "userPassword" in keys and \
                    "mail" in keys:
                sn = str(obj["sn"][0], encoding='utf-8')
                pwd = str(obj["userPassword"][0], encoding='utf-8')
                mail = str(obj["mail"][0], encoding='utf-8')
                data.append({"sn": sn, "pwd": pwd, "mail": mail})
        return data

    def insert_db(self):
        users = self.get_ldap_user()
        self.get_tenant_access_token()
        for user in users:
            self.cursor.execute("select * from users_user where email='%s'" %
                                (user["mail"]))
            data = self.cursor.fetchone()
            if not data:
                sn = user["sn"]
                first_name = ""
                last_name = ""
                if is_all_chinese(sn):
                    first_name = sn[1:]
                    last_name = sn[0]
                pwd = user["pwd"]
                mail = user["mail"]
                username = mail.split("@")[0]
                res = requests.get(
                    "https://open.feishu.cn/open-apis/user/v1/batch_get_id?emails=%s"
                    % (mail),
                    headers=self.headers)
                d2 = res.json()
                d2 = d2["data"]
                if "email_users" in d2:
                    if mail in d2["email_users"]:
                        user_id = d2["email_users"][mail][0]["user_id"]
                        print(mail, user_id)
                        sql = "insert into users_user values('%s','%s',0,'%s','%s','%s','%s', 1, 1, '%s','%s','%s','','','%s')" % (
                            pwd, '2022-01-01 00:00:00.000000000', username,
                            first_name, last_name, mail,
                            '2022-01-01 00:00:00.000000000', str(
                                uuid.uuid4()).replace("-", "",
                                                      4), '[2,]', user_id)
                        self.cursor.execute(sql)
                        self.db.commit()
        self.cursor.close()
        self.db.close()


if __name__ == "__main__":
    ld = LDAP()
    ld.insert_db()