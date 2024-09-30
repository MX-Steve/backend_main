# encoding: utf-8
import requests
import json
import sys
import pymysql
dbHost = "10.149.4.33"
dbPort = 3306
dbUser = "root"
dbPassword = "123456"
dbDbname = "test"

def cuser(username,password):
    url="http://127.0.0.1:8081/users/v1/register"
    headers={
        "Content-Type": "application/json",
    }
    data = {
        "username": username,
        "password": password
    }
    res = requests.post(url=url,headers=headers,data=json.dumps(data))
    print(res)
    dbConn = pymysql.connect(
            host=dbHost,
            port=dbPort,
            user=dbUser,
            password=dbPassword,
            db=dbDbname
        )
    dbCursor = dbConn.cursor()
    usql="UPDATE users_user SET roles='[2,]',is_staff=1,is_active=1,first_name='%s' WHERE username='%s'"%(username,username)
    dbCursor.execute(usql)
    dbConn.commit()
    print("successful!")
    
if __name__ == "__main__":
    username=input("input username: ")
    password=input("input password: ")
    print(username)
    print(password)
    cuser(username=username,password=password)
