#!/usr/bin/python
import commands
import datetime
import multiprocessing
import os
import time
from pprint import pprint

from parse_rest.connection import register
from parse_rest.datatypes import Object

import settings_local


class DeviceStatus(Object):
    pass


class RemoteCommands(Object):
    pass


def get_pid():
    try:
        file = open(settings_local.FILE_VPROBE_PID, "r")
        spid = file.read()
        pid = int(spid)
        return pid
    except IOError:
        print "Error: File does not appear to exist."
        return 0

def poolingServer():
    while 1:
        print 'Pooling webservice...'
        get_data_parse()
        time.sleep(10)


def getUpTime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return uptime_seconds
    # uptime_string = str(timedelta(seconds=uptime_seconds))


def setStatus():
    print "DEBUG - setStatus"

    while True:
        up = getUpTime()
        allStatus = DeviceStatus.Query.all()
        statusDevice = allStatus.limit(1)

        print statusDevice
        device = statusDevice[0]

        device.status = True
        device.uptime = up
        device.timeout = settings_local.INFORM_TIMEOUT
        device.save()
        time.sleep(settings_local.INFORM_TIMEOUT)

def runCommand(commnad):
     return commands.getstatusoutput(commnad)

def handle_commands():
    while True:
        all_commands = RemoteCommands.Query.all()
        for cmd in all_commands:
            start = datetime.datetime.utcnow()
            delta = start - cmd.updatedAt
            if ((cmd.executed == True) or (delta.total_seconds() > 20)):#FIXME hardcoded
                print str(delta)
                print  "Ignore command."
                continue

            r, v = runCommand(cmd.command)
            cmd.ret = r
            cmd.result = v
            cmd.executed = True
            print cmd.result
            pprint(cmd)
            print "Result ", cmd.result
            cmd.save()
            time.sleep(2)
        time.sleep(10)

def get_data_parse():
    pass
    # open the file for writing
    # global all_hosts
    # all_hosts = Host.Query.all()
    # pickle.dump(all_hosts, fileObject)
    # fileObject.close()


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def checkLatencyProcess():
    while True:
        pid = get_pid()
        if check_pid(pid):
            print "Process is running ", pid
        else:
            print "Process not found:  ", pid
            print "Restart Process "
            startProcess()

        time.sleep(10)


def startProcess():
    from subprocess import check_output
    out = check_output(["./python-sudo.sh", "-p"])
    # print out


if __name__ == '__main__':
    register(settings_local.APPLICATION_ID, settings_local.REST_API_KEY, master_key=settings_local.MASTER_KEY)

    d = multiprocessing.Process(name='pooling', target=poolingServer)
    d.daemon = True
    d.start()

    time.sleep(1)
    s = multiprocessing.Process(name='statusPooling', target=setStatus)
    s.daemon = True
    s.start()

    time.sleep(1)
    c = multiprocessing.Process(name='checkLatencyProcess', target=checkLatencyProcess)
    c.daemon = True
    c.start()

    time.sleep(1)
    com = multiprocessing.Process(name='handle_commands', target=handle_commands)
    com.daemon = True
    com.start()

    d.join()
    s.join()
    c.join()
    com.join()
