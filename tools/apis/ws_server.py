import asyncio
import websockets
import paramiko
import json
import sys
import platform

plat = platform.system().lower()

if plat == "linux":
    JobFile = "/data/codes/backend_main/tools/apis/results.txt"
else:
    JobFile = "C:/data/codes/backend_main/tools/apis/results.txt"


def writejob(file, c):
    import time
    timestamp = time.time()
    strtime = time.strftime("%Y%m%d", time.localtime(timestamp))
    strtime1 = time.strftime("%H:%M:%S", time.localtime(timestamp))
    c = "[%s] %s" % (strtime1, c)
    line = "%s:" % (strtime)
    f = open(file, 'r', encoding='UTF-8')
    count = 0
    for l in f:
        if line in l:
            count = 1
    if count == 0:
        with open(file, 'r+', encoding='utf-8') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line+'\n'+content)
    count1 = 0
    f = open(file, "r", encoding="UTF-8")
    for l in f:
        if c in l:
            count1 = 1
    if count1 == 0:
        f = open(file, 'r', encoding='UTF-8')
        contents = f.readlines()
        contents = [contents[0]]+["%s\n" % (c)]+contents[1:]
        with open(file, "w", encoding='UTF-8') as fobj:
            fobj.writelines(contents)


class SSH2:
    def __init__(self, hostname, port=22, username='root', password=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None

    def do(self, cmd):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.hostname,
                         port=self.port,
                         username=self.username,
                         password=self.password)
        stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=1800)
        return stdout.read().decode(), stderr.read().decode()

    def close(self):
        # 关闭连接
        self.ssh.close()


globalChan = {}
CMD = """/usr/bin/expect <<^
spawn /bin/ssh lihan@132.252.197.136
expect "yes/no" {send "yes\n"}
expect "lihan@132.252.197.136's password:" {send "Hx+U7GtsWsaQP@s9Dw\n"}
expect "]$ " {send "cd ~/peizhijiaofu/.hostMsgs/\n"}
expect "]$ " {send "sh ips_form.sh %s %s\n"}
expect "]$ " {send "rm -f log/*%s*\n"}
"""
# if plat == "linux":
#     Server = SSH2("10.149.4.33", 22,
#                   "root", "Rfwh@o#xj&cj%58H")
# else:
#     Server = SSH2("132.252.139.254", 18022,
#                   "proxyagent@lihan@EM_LIHAN@132.252.197.136", "cFJ#zZ#8qE2WP&hs")
# Server2 = SSH2("132.252.197.136", 22, "lihan", 'Hx+U7GtsWsaQP@s9Dw')
# Server = SSH2("132.252.139.254", 18022,"proxyagent@lihan@EM_LIHAN@132.252.197.136", "cFJ#zZ#8qE2WP&hs")
Server = SSH2("132.252.197.136", 22, "lihan", 'Hx+U7GtsWsaQP@s9Dw')

def sdo2(data):
    # disk,user,ssh, iptables, iptablesCheck, dir, operate, time, hostDown
    op = data["op"]
    ipFile = data["process"]["ip_file"]
    str1 = ""
    if op == "ssh":
        hosts = data["data"]["hosts"]
        str1 = "%s OpenSSH 升级操作" % (hosts)
        writejob(JobFile, str1)
        scripts = data["process"]["scripts"]
        cmd = CMD % ("sshIplist0", hosts, ipFile)
        cmd += """
        expect "]$ " {set timeout 1800;send "/bin/bash %s 1\n"}
        expect "]$ " {set timeout 1800;send "/bin/bash %s 2\n"}
        expect "]$ " {send "cat log/expect_log_file_%s*\n"}
        expect "]$ " {send "exit\n"}
        expect eof
        ^""" % (scripts, scripts, ipFile)
        out, err = Server.do(cmd)
        return out
    elif op == "iptables":
        str1 = "%s 访问 %s 白名单设置" % (data["data"]["src"], data["data"]["dst"])
        writejob(JobFile, str1)
        scripts = data["process"]["scripts"]
        cmd = """/usr/bin/expect <<^
spawn /bin/ssh lihan@132.252.197.136
expect "lihan@132.252.197.136's password:" {send "Hx+U7GtsWsaQP@s9Dw\n"}
expect "]$ " {send "cd ~/peizhijiaofu/.hostMsgs/\n"}
expect "]$ " {send "rm -f log/*%s*\n"}
""" % (ipFile)
        iplist0 = "%s %s" % (data["data"]["src"], data["data"]["dst"])
        cmd += """
expect "]$ " {send "cat > %s<< EOF 
%s
EOF\n"}
        """ % ("%sIplist0" % (op), iplist0)
        cmd += """
        expect "]$ " {set timeout 1800;send "/bin/bash %s 1\n"}
        expect "]$ " {send "cat log/expect_log_file_%s*\n"}
        expect "]$ " {send "exit\n"}
        expect eof
        ^""" % (scripts, ipFile)
        out, err = Server.do(cmd)
        return out
    elif op == "iptablesCheck":
        str1 = "%s 访问 %s 白名单设置校验" % (data["data"]["src"], data["data"]["dst"])
        writejob(JobFile, str1)
        scripts = data["process"]["scripts"]
        dst = data["data"]["dst"]
        dst = dst.split(":")[0]
        cmd = """/usr/bin/expect <<^
spawn /bin/ssh lihan@132.252.197.136
expect "lihan@132.252.197.136's password:" {send "Hx+U7GtsWsaQP@s9Dw\n"}
expect "]$ " {send "cd ~/peizhijiaofu/.hostMsgs/\n"}
expect "]$ " {send "sh ips_form.sh %s %s\n"}
expect "]$ " {send "rm -f log/*%s*\n"}
""" % (ipFile, dst, ipFile)
        iplist0 = "%s %s" % (data["data"]["src"], data["data"]["dst"])
        cmd += """
expect "]$ " {send "cat > %s<< EOF 
%s
EOF\n"}
        """ % ("iptablesIplist0", iplist0)
        cmd += """
        expect "]$ " {set timeout 1800;send "/bin/bash %s\n"}
        expect "]$ " {send "cat log/expect_log_file_%s*\n"}
        expect "]$ " {send "exit\n"}
        expect eof
        ^""" % (scripts, ipFile)
        out, err = Server.do(cmd)
        return out
    elif op == "disk":
        hosts = data["data"]["hosts"]
        scripts = data["process"]["scripts"]
        disk = data["data"]
        exDir = str(disk["exDir"])
        exDir = exDir.replace("T", "t").replace("F", "f")
        iplist0 = "%s:%s:%s:%s:%s:%s:%s" % (
            disk["hosts"], disk["disks"], disk["VgName"], disk["LvName"], disk["LvSize"], disk["mountDir"], exDir)
        str1 = "%s 机器 %s 磁盘挂载 %s 目录" % (
            disk["hosts"], disk["disks"], disk["mountDir"])
        writejob(JobFile, str1)
        cmd = CMD % (ipFile, hosts, ipFile)
        cmd += """expect "]$ " {send "cat > %s<< EOF 
%s
EOF\n"}
            """ % ("%sIplist0" % (op), iplist0)
        cmd += """
        expect "]$ " {set timeout 1800;send "/bin/bash %s post\n"}
        expect "]$ " {send "cat log/expect_log_file_%s*\n"}
        expect "]$ " {send "exit\n"}
        expect eof
        ^""" % (scripts, ipFile)
        out, err = Server.do(cmd)
        return out
    elif op == "user":
        hosts = data["data"]["hosts"]
        scripts = data["process"]["scripts"]
        user = data["data"]
        create = str(user["create"])
        create = create.replace("T", "t").replace("F", "f")
        sudo = str(user["sudo"])
        sudo = sudo.replace("T", "t").replace("F", "f")
        passwd = user["passwd"]
        passwd = passwd.replace("$", "\$")
        iplist0 = "%s:%s:%s:%s:%s:%s" % (
            user["hosts"], user["users"], create, passwd, sudo, user["homedir"])
        str1 = "%s 机器 %s 用户" % (user["hosts"], user["users"])
        if create == "true":
            str1 += "新增操作,"
        else:
            str1 += "密码更新,"
        if sudo == "true":
            str1 += "授权操作"
        writejob(JobFile, str1)
        cmd = CMD % (ipFile, hosts, ipFile)
        cmd += """expect "]$ " {send "cat > %s<< EOF 
%s
EOF\n"}
            """ % ("%sIplist0" % (op), iplist0)
        cmd += """
        expect "]$ " {set timeout 1800;send "/bin/bash %s post\n"}
        expect "]$ " {send "cat log/expect_log_file_%s*\n"}
        expect "]$ " {send "exit\n"}
        expect eof
        ^""" % (scripts, ipFile)
        out, err = Server.do(cmd)
        return out
    elif op == "dir":
        scripts = data["process"]["scripts"]
        hosts = data["data"]["hosts"]
        ipFile = data["process"]["ip_file"]
        op = data["op"]
        cmd = CMD % (ipFile, hosts, ipFile)
        str1 = "%s var 目录磁盘告警清理" % (hosts)
        writejob(JobFile, str1)
        cmd += """
expect "]$ " {set timeout 1800;send "auto-jszc-bash -b %s -N %s -d log\n"}
expect "]$ " {send "cat log/expect_log_file_%s*\n"}
expect "]$ " {send "exit\n"}
expect eof
^""" % (scripts, ipFile, ipFile)
        print(cmd)
        out, err = Server.do(cmd)
        return out
    elif op == "operate":
        scripts = data["process"]["scripts"]
        hosts = data["data"]["hosts"]
        ipFile = data["process"]["ip_file"]
        op = data["op"]
        cmd = CMD % (ipFile, hosts, ipFile)
        str1 = ""
        description = data["data"]["description"]
        if description == "":
            str1 = "%s 执行脚本操作" % (hosts)
        else:
            str1 = "%s %s" % (hosts, description)
        ops = data["data"]["ops"]
        ops = ops.replace("[", "\[").replace("]", "\]")
        print(ops)
        cmd += """
expect "]$ " {send "cat > %s<< EAF 
%s
EAF\n"}
        """ % (scripts, ops)
        writejob(JobFile, str1)
        cmd += """
expect "]$ " {set timeout 1800;send "auto-jszc-bash -b %s -N %s -d log\n"}
expect "]$ " {send "cat log/expect_log_file_%s*\n"}
expect "]$ " {send "exit\n"}
expect eof
^""" % (scripts, ipFile, ipFile)
        print(cmd)
        out, err = Server.do(cmd)
        return out
    elif op == "time":
        scripts = data["process"]["scripts"]
        hosts = data["data"]["hosts"]
        ipFile = data["process"]["ip_file"]
        op = data["op"]
        cmd = CMD % (ipFile, hosts, ipFile)
        str1 = "%s 时钟同步" % (hosts)
        writejob(JobFile, str1)
        cmd += """
expect "]$ " {set timeout 1800;send "auto-jszc-bash -b %s -N %s -d log\n"}
expect "]$ " {send "cat log/expect_log_file_%s*\n"}
expect "]$ " {send "exit\n"}
expect eof
^""" % (scripts, ipFile, ipFile)
        print(cmd)
        out, err = Server.do(cmd)
        return out
    elif op == "hostDown":
        scripts = data["process"]["scripts"]
        hosts = data["data"]["hosts"]
        ipFile = data["process"]["ip_file"]
        op = data["op"]
        cmd = CMD % (ipFile, hosts, ipFile)
        str1 = "%s 机器zabbix_agent卸载，zabbix_server 删除，融合云删除下线" % (hosts)
        writejob(JobFile, str1)
        cmd += """
expect "]$ " {set timeout 1800;send "/bin/bash hostDown.sh\n"}
expect "]$ " {send "cat log/hostDown.log\n"}
expect "]$ " {send "exit\n"}
expect eof
^"""
        print(cmd)
        out, err = Server.do(cmd)
        return out


def sdo(data):
    # operate, time, hostDown
    scripts = data["process"]["scripts"]
    hosts = data["data"]["hosts"]
    ipFile = data["process"]["ip_file"]
    op = data["op"]
    cmd = CMD % (ipFile, hosts, ipFile)
    str1 = ""
    if op == "time":
        str1 = "%s 时钟同步" % (hosts)
    if op == "hostDown":
        str1 = "%s 机器zabbix_agent卸载，zabbix_server 删除，融合云删除下线" % (hosts)
    if op == "operate":
        description = data["data"]["description"]
        if description == "":
            str1 = "%s 执行脚本操作" % (hosts)
        else:
            str1 = "%s %s" % (hosts, description)
        ops = data["data"]["ops"]
        ops = ops.replace("[", "\[").replace("]", "\]")
        print(ops)
        cmd += """
expect "]$ " {send "cat > %s<< EAF 
%s
EAF\n"}
        """ % (scripts, ops)
    writejob(JobFile, str1)
    if op == "hostDown":
        cmd += """
expect "]$ " {set timeout 1800;send "/bin/bash hostDown.sh\n"}
expect "]$ " {send "cat log/hostDown.log\n"}
expect "]$ " {send "exit\n"}
expect eof
^"""
    else:
        cmd += """
expect "]$ " {set timeout 1800;send "auto-jszc-bash -b %s -N %s -d log\n"}
expect "]$ " {send "cat log/expect_log_file_%s*\n"}
expect "]$ " {send "exit\n"}
expect eof
^""" % (scripts, ipFile, ipFile)
    print(cmd)
    out, err = Server.do(cmd)
    return out


def main_sdo1():
    # operate, time, hostDown
    print(' ========= websocket sdo1 is going to run =========')

    async def subRun(websocket):
        async for message in websocket:
            data = json.loads(message)
            op = data["op"]
            await asyncio.sleep(0.1)
            await websocket.send("正在执行，请稍等。。。")
            if op in ["operate", "dir", "time", "hostDown"]:
                if op not in globalChan.keys():
                    globalChan[op] = 0
                globalChan[op] = globalChan[op] + 1
                value = globalChan[op]
                if value > 1:
                    await websocket.send("有正在执行的相同类型任务，请等待刷新重试")
                else:
                    result = sdo(data)
                    await websocket.send(result)
                    globalChan[op] = 0
            else:
                await websocket.send("当前任务不走这个接口，请后台检查")
            await websocket.send("        全部执行完成！！！")

    async def run(websocket, path):
        while True:
            await subRun(websocket)

    start_server = websockets.serve(run, "0.0.0.0", 38082)
    print(' ========= websocket sdo1 running =========')
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


def main_sdo2():
    # disk, user, iptables, ssh, dir, operate, time, hostDown
    print(' ========= websocket sdo2 is going to run =========')

    async def subRun(websocket):
        async for message in websocket:
            data = json.loads(message)
            op = data["op"]
            await asyncio.sleep(0.1)
            await websocket.send("正在执行，请稍等。。。")
            if op in ["disk", "user", "iptables", "iptablesCheck", "ssh", "dir", "operate", "time", "hostDown"]:
                if op not in globalChan.keys():
                    globalChan[op] = 0
                globalChan[op] = globalChan[op] + 1
                value = globalChan[op]
                if value > 1:
                    await websocket.send("有正在执行的相同类型任务，请等待刷新重试")
                else:
                    result = sdo2(data)
                    await websocket.send(result)
                    globalChan[op] = 0
            else:
                await websocket.send("当前任务不走这个接口，请后台检查")
            await websocket.send("        全部执行完成！！！")

    async def run(websocket, path):
        while True:
            await subRun(websocket)

    start_server = websockets.serve(run, "0.0.0.0", 38083)
    print(' ========= websocket sdo2 running =========')
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    whichOne = sys.argv[1]
    if whichOne == "sdo1":
        main_sdo1()
    elif whichOne == "sdo2":
        main_sdo2()
    else:
        print("不存在")
