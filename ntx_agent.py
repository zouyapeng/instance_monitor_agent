#!/usr/bin/env python
# -*- coding: utf8 -*-

import time
import sched
import logging
import libvirt
import socket

from logging.handlers import RotatingFileHandler
from multiprocessing import Process

from heartbeat import heartbeat


HOSTNAME = None
UUIDS = None
ID = None
CONFIG = {}

R_handler = RotatingFileHandler('./ntx_agent.log', maxBytes=10 * 1024 * 1024,backupCount=5)
formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')
R_handler.setFormatter(formatter)
logging.getLogger('').setLevel(logging.DEBUG)
logging.getLogger('').addHandler(R_handler)


class LibvirtClient(object):
    def __init__(self):
        self.conn = None
        self.try_count = 0
        while self.conn is None and self.try_count < 3:
            self.conn = libvirt.open(None)
            self.try_count += 1
            time.sleep(0.1)

        if self.conn is None:
            raise libvirt.VIR_ERR_INTERNAL_ERROR

        self.domains = self.conn.listAllDomains()

    def close(self):
        self.conn.close()


def collector_worker():
    logging.info('collector')


def heartbeat_worker():
    libvirt_client = LibvirtClient()
    uuids = [domain.UUIDString() for domain in libvirt_client.domains]
    libvirt_client.close()

    global UUIDS, ID, CONFIG
    uuids_status = cmp(UUIDS, uuids)

    if ID and uuids_status == 0:
        ID, CONFIG = heartbeat(agent_id=ID)
    elif ID and uuids_status != 0:
        UUIDS = uuids
        ID, CONFIG = heartbeat(agent_id=ID, uuids=UUIDS)
    else:
        ID, CONFIG = heartbeat(hostname=HOSTNAME, uuids=UUIDS)


class CollectorProcess(Process):
    def __init__(self, interval):
        super(CollectorProcess, self).__init__()
        self.interval = interval

    def main_loop(self, sc):
        sc.enter(self.interval, 1, self.main_loop, (sc,))
        collector_worker()

    def run(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(self.interval, 1, self.main_loop, (scheduler,))
        scheduler.run()


class HeartbeatProcess(Process):
    def __init__(self, interval):
        super(HeartbeatProcess, self).__init__()
        self.interval = interval

    def main_loop(self, sc):
        sc.enter(self.interval, 1, self.main_loop, (sc,))
        heartbeat_worker()

    def run(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(self.interval, 1, self.main_loop, (scheduler,))
        scheduler.run()


def init_server():
    global UUIDS, HOSTNAME

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('www.baidu.com', 80))
    HOSTNAME = s.getsockname()[0]
    s.close()

    libvirt_client = LibvirtClient()
    UUIDS = [domain.UUIDString() for domain in libvirt_client.domains]
    libvirt_client.close()


if __name__ == '__main__':
    init_server()

    heartbeat_process = HeartbeatProcess(15)
    heartbeat_process.daemon = True
    heartbeat_process.start()

    collector_process = CollectorProcess(60)
    collector_process.daemon = True
    collector_process.start()

    while True:
        # check sub processes is working
        time.sleep(3600)
