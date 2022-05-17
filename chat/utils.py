import os
import subprocess

def restart_beat():
    retcode, output = subprocess.getstatusoutput('supervisorctl restart beat')
    return retcode, output

if __name__ == '__main__':
    code,out = restart_beat()
    print(code)
    print(out)