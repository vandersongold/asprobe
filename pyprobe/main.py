#!/usr/bin/env python
import json
import logging
import os
import sys
import time
import getopt

import settings_local
from cloudMQTT import CloudMQTT
from cloudServer import CloudServer, start_schedule, sched
from works import Works
from speed import speed_test
from helper.filter import FilterTopic
from helper.probecommands import reboot, exec_command


# Define callback functions which will be called when certain events happen.
def connected(client):
    logging.debug('Connected to MQTT server!  Listening for commands changes...')
    # Subscribe to changes on a feed named DemoFeed.
    cloudMqtt.subscribe_main_channels(probe.objectId)

def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    logging.debug('Disconnected from NT LABS IO!')
    sys.exit(1)

def on_message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    logging.debug('Message {0} received new value: {1}'.format(feed_id, payload))
    app = CloudServer.Instance()

    if feed_id == FilterTopic.SPEED_TEST:
        logging.debug("SPEED TEST - Value =  %s", payload)
        down, up, ping = speed_test()
        data = {}
        data['download'] = down
        data['upload'] = up
        data['ping'] = ping
        json_data = json.dumps(data)
        cloudMqtt.publish_speedtest_result(json_data)
        app.store_speed_test(app.get_probe(), down, up, ping)

    elif feed_id == FilterTopic.REBOOT:
        logging.debug("REBOOT Command - Value =  %s", payload)
        reboot()

    elif feed_id == FilterTopic.COMMAND:
        logging.debug("COMMAND Command - Value =  %s", payload)
        cloudMqtt.publish_command_result(exec_command(payload))

    elif feed_id == FilterTopic.APPLY:
        logging.debug("APPLY Command - Value =  %s", payload)
        app.reload()

    elif feed_id == FilterTopic.LATENCY:
        logging.debug("LATENCY Command - Value =  %s", payload)
        works = Works.Instance()
        if payload == '1':
            works.star_works(app.get_host_list())
        elif payload == '0':
            works.stop_works()
        send_status_latency(app.get_probe().objectId)

    elif feed_id == FilterTopic.STATUS:
        logging.debug("STATUS Command - Value =  %s", payload)
        cloudMqtt.publish_status(app.get_probe().objectId)

    else:
        logging.debug('Message  received new value: %s', payload)


def send_status_latency(deviceID):
    works = Works.Instance()
    if works.is_working():
        ret = '1'
    else:
        ret = '0'
    cloudMqtt.publish("probe/" + deviceID + "/latency/result", ret)

def main_loop():
    while True:
        sched.run_pending()
        time.sleep(10)

def savePidFile():
    pidfile = settings_local.FILE_VPROBE_PID
    if pidfile:
        # ensure the directory where the pid-file should be set exists (for
        # instance /var/run/cubicweb may be deleted on computer restart)
        piddir = os.path.dirname(pidfile)
        if not os.path.exists(piddir):
            os.makedirs(piddir)
        f = file(pidfile, 'w')
        pid = os.getpgrp()
        logging.debug("DEBUG: %d", pid)
        f.write(str(pid))
        f.close()
        os.chmod(pidfile, 0o644)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
    logging.debug('Started')

    argv = sys.argv[1:]
    # fixme: uncomment for device status
    # savePidFile()
    interface = "enp7s0"

    try:
        opts, args = getopt.getopt(argv, "hi:", ["inteface="])
    except getopt.GetoptError:
        print 'main.py -h'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'main.py -i <inteface>'
            sys.exit()
        elif opt in ("-i", "--interface"):
            inteface = arg

    app = CloudServer.Instance()
    app.self_register(interface)
    time.sleep(3)
    probe = app.get_probe()

    stime = probe.stSchedule
    start_schedule(stime)

    cloudMqtt = CloudMQTT()
    cloudMqtt.on_connect = connected
    cloudMqtt.on_disconnect = disconnected
    cloudMqtt.on_message = on_message
    cloudMqtt.connect()
    cloudMqtt.loop_background()

    main_loop()
