#!/usr/bin/env python
# -*- coding: utf8 -*-

import time
import sched
import logging
import socket

from logging.handlers import RotatingFileHandler
from multiprocessing import Process

from heartbeat import heartbeat
from collector import get_current_uuids, collector, analysis, set_trigger


HOSTNAME = None
UUIDS = None
ID = None
CONFIG = {}

LOGGING = logging.getLogger('')
R_handler = RotatingFileHandler('./ntx_agent.log', maxBytes=10 * 1024 * 1024,backupCount=5)
formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')
R_handler.setFormatter(formatter)
LOGGING.setLevel(logging.DEBUG)
LOGGING.addHandler(R_handler)


def analysis_worker():
    global CONFIG, UUIDS
    try:
        if CONFIG and UUIDS:
            for uuid in UUIDS:
                config = CONFIG.get(uuid, None)
                if analysis(uuid, config):
                    set_trigger(config['id'])
    except Exception:
        LOGGING.exception('!!!!!analysis failed!!!!!')


def collector_worker():
    try:
        collector()
    except Exception:
        LOGGING.exception('!!!!!collector failed!!!!!')


def heartbeat_worker():
    uuids = get_current_uuids()

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


class AnalysisProcess(Process):
    def __init__(self, interval):
        super(AnalysisProcess, self).__init__()
        self.interval = interval

    def main_loop(self, sc):
        sc.enter(self.interval, 1, self.main_loop, (sc,))
        analysis_worker()

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

    UUIDS = get_current_uuids()


if __name__ == '__main__':
    init_server()

    heartbeat_process = HeartbeatProcess(60)
    heartbeat_process.daemon = True
    heartbeat_process.start()

    time.sleep(10)

    collector_process = CollectorProcess(30)
    collector_process.daemon = True
    collector_process.start()

    time.sleep(10)

    # analysis_process = AnalysisProcess(60)
    # analysis_process.daemon = True
    # analysis_process.start()

    while True:
        # check sub processes is working
        time.sleep(3600)
