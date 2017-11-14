import logging
import multiprocessing
from multiprocessing import Process

import time

from cloudServer import CloudServer
from thirdparty.Ping import quiet_ping
from thirdparty.Singleton import Singleton

@Singleton
class Works:
    def __init__(self):
        self.processes = []
        self.is_running = False

    def star_works(self, hosts):
        logging.debug('star_works')
        i = 0
        if self.is_running:
            logging.debug('Teste de Latencia ja esta em execucao. Parar primeiro.')
            return

        for host in hosts:
            self.processes.append(Process(target=ping, args=(host,)))
            self.processes[i].start()
            i = i + 1
        self.is_running = True

    def stop_works(self):
        logging.debug('stop_works')
        for p in self.processes:
            p.terminate()
            p.join()
        self.processes = []
        self.is_running = False

    def is_working(self):
        return self.is_running


def ping(oHost):
    logging.debug('Starting: %s', multiprocessing.current_process().name)
    app = CloudServer.Instance()

    try:
        pings = oHost.pings
    except AttributeError:
        pings = 5

    try:
        url = oHost.url
    except AttributeError:
        logging.error("Error: no URL Exit")
        return

    try:
        step = oHost.step
    except AttributeError:
        step = 5

    while True:
        percent_lost, mrtt, artt = quiet_ping(url, count=pings)
        mrtt = float("{0:.2f}".format(mrtt))
        artt = float("{0:.2f}".format(artt))
        logging.debug('Ping %s artt: %d',url, artt)
        app.store_latency_test(host=oHost, avg=artt, mrtt=mrtt, percent_lost=percent_lost)
        time.sleep(step)