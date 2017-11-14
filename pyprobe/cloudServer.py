import logging
import time
import os
import settings_local

os.environ["PARSE_API_ROOT"] = settings_local.PARSE_HOST
import schedule
from parse_rest.connection import register
from parse_rest.query import QueryResourceDoesNotExist

from models.latencyReport import LatencyReport
from speed import speed_test
from helper import vnetwork_utils
from models.probe import Probe
from models.host import Host
from models.speedTestReport import SpeedTestReport
from  thirdparty.Singleton import Singleton

sched = schedule.Scheduler()

@Singleton
class CloudServer:
    def __init__(self):
        register(settings_local.APPLICATION_ID, settings_local.REST_API_KEY, master_key=settings_local.MASTER_KEY)
        self.probe = None
        self.host_list = None

    def self_register(self, interface):
        self.interface = interface
        addr = vnetwork_utils.get_mac(interface)
        try:
            self.probe = Probe.Query.get(mac=addr)
            logging.debug('Probe->objectId: %s', self.probe.objectId)

        except QueryResourceDoesNotExist:
            ip_local = self.get_local_ip()
            logging.debug('Probe (mac): %s, is not registered yet', addr)
            self.probe = Probe(mac=addr,name=addr+"-"+interface, ip=ip_local, version=settings_local.VERSION, stSchedule="22:00")
            self.probe.save()
            logging.debug('Probe (mac): %s, with objectId = %s now is registered', addr, self.probe.objectId)

    def get_local_ip(self):
        try:
            ip_local = vnetwork_utils.get_ip_address((self.interface))
            return ip_local
        except IOError:
            return "0.0.0.0"

    def get_probe(self):
        return self.probe

    def store_speed_test(self, probe, download, upload, latency):
        speedTestObj = SpeedTestReport(probe=probe, download=download, upload=upload, latency=latency)
        speedTestObj.save()

    def store_latency_test(self, host,  avg, mrtt, percent_lost):
        classLatency = LatencyReport(host=host, avg=avg, max=mrtt, loss=percent_lost, probe=self.probe)
        classLatency.save()

    def get_host_list(self):
        try:
            self.host_list = Host.Query.filter(probe=self.probe)
        except QueryResourceDoesNotExist:
            return None
        return self.host_list

    def reload(self):
        try:
            logging.info("Reloading probe")
            self.probe = Probe.Query.get(objectId=self.probe.objectId)
            start_schedule(self.probe.stSchedule)

        except:
            logging.error("Not possible reload probe")


def st_schedule_job():
    logging.debug('st_schedule_job')
    # FIXME:
    for x in xrange(2):
        app = CloudServer.Instance()
        down, up, ping = speed_test()
        app.store_speed_test(app.get_probe(), down, up, ping)

        time.sleep(25)

def start_schedule(stime):
    jobs = sched.jobs
    sched.clear()

    if (stime != None and stime != ''):
        logging.debug('Time to run %s ', stime)
        sched.every().day.at(stime).do(st_schedule_job)