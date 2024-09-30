import paramiko
import platform
import subprocess

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
        stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=300)
        return stdout.read().decode('utf8'), stderr.read().decode('utf8')

    def close(self):
        self.ssh.close()


globalChan = {}
CMD = """/usr/bin/expect <<^
spawn /bin/ssh lihan@132.224.201.188
expect "lihan@132.224.201.188's password:" {send "Hx+U7GtsWsaQP@s9Dw\n"}
expect "]$ " {send "cd ~/peizhijiaofu/.hostMsgs/\n"}
expect "]$ " {send "sh ips_form.sh %s %s\n"}
expect "]$ " {send "rm -f log/*%s*\n"}
"""
ServerWin = SSH2("132.252.37.204", 18022,
                 "proxyagent@lihan@lihan@132.224.201.188", "cFJ#zZ#8qE2WP&hs")

ServerLin = SSH2("132.224.201.188", 22, "lihan", 'Hx+U7GtsWsaQP@s9Dw')

if plat == "linux":
    Server = ServerLin
else:
    Server = ServerWin


if __name__ == "__main__":
    cmd1 = """/usr/bin/expect <<^
spawn /bin/ssh lihan@132.224.201.188
expect "]$ " {send "cd ~/peizhijiaofu/.hostMsgs\n"}
"""
    cmd1 += """
expect "]$ " {send "cat > operate.sh<< EAF 
ls /opt
EAF\n"}
"""
    cmd1 += """
expect "]$ " {set timeout 300;send "/usr/sbin/auto-jszc-bash -b operate.sh -N operateIplist -d log\n"}
expect "]$ " {send "cat log/expect_log_file_operateIplist*\n"}
expect "]$ " {send "exit\n"}
^"""
    process = subprocess.Popen(
        cmd1,  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, unused_err = process.communicate(timeout=300)
    output = output.decode("utf-8")
    print(output)
