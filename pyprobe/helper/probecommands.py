import logging
import os
from subprocess import check_output, CalledProcessError
import json
import time
import sys

from tempfile import TemporaryFile

def get_out(*args):
    with TemporaryFile() as t:
        try:
            out = check_output(args, stderr=t)
            return  0, out
        except CalledProcessError as e:
            t.seek(0)
            return e.returncode, t.read()

def isValidCommand(command):
    valid_commands = ['df', 'free', 'ps', 'uptime', 'date', 'dmesg', 'ifconfig']
    if any(command in s for s in valid_commands):
        return True

def exec_command(command):
    data = {}
    if not isValidCommand(command):
        logging.debug('operation not permitted %s', command)
        data['ret'] = -1
        data["result"] = "operation not permitted"
        json_data = json.dumps(data)
        return json_data

    r, result = get_out(command)
    data['ret'] = r
    data["result"] = result
    json_data = json.dumps(data)
    return  json_data

def reboot():
    for i in range(1, 10):
        print('reboot in', i)
        # Do your code here
        time.sleep(1)
    os.system("reboot")
