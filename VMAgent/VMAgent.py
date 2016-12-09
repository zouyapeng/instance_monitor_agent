#!/usr/bin/env python
# -*- coding: utf8 -*-

import json
import logging
import sched
import socket
import time
import signal
from functools import partial
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Queue

from config import CONF
from trigger_analysis import analysis
from collector import get_current_uuids, collector
from heartbeat import heartbeat

HOSTNAME = None
ID = None
UUIDS = None
CONFIG = {}

LOGGING = logging.getLogger('')
R_handler = RotatingFileHandler(CONF.log_path, maxBytes=10 * 1024 * 1024,backupCount=5)
formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')
R_handler.setFormatter(formatter)
LOGGING.setLevel(logging.DEBUG)
LOGGING.addHandler(R_handler)


def analysis_worker():
    global UUIDS, CONFIG
    try:
        if CONFIG and UUIDS:
            for uuid in UUIDS:
                config = CONFIG.get(uuid, None)
                analysis(uuid, config)
    except Exception:
        LOGGING.exception('!!!!!analysis failed!!!!!')


def collector_worker():
    try:
        collector()
    except Exception:
        LOGGING.exception('!!!!!collector failed!!!!!')


def heartbeat_worker():
    global ID, UUIDS
    try:
        uuids = get_current_uuids()
        uuids_status = cmp(uuids, UUIDS)

        if ID and uuids_status == 0:
            ID, config = heartbeat(agent_id=ID)
        elif ID and uuids_status != 0:
            ID, config = heartbeat(agent_id=ID, uuids=uuids)
        else:
            ID, config = heartbeat(hostname=HOSTNAME, uuids=UUIDS)
    except Exception:
        LOGGING.exception('!!!!!heartbeat failed!!!!!')
        return None, None

    if uuids_status == 0:
        return None, config
    else:
        return uuids, config


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
    def __init__(self, interval, queue):
        super(HeartbeatProcess, self).__init__()
        self.interval = interval
        self.queue = queue

    def main_loop(self, sc):
        sc.enter(self.interval, 1, self.main_loop, (sc,))
        global UUIDS, CONFIG
        uuids, config = heartbeat_worker()
        if uuids:
            self.queue.put(json.dumps({'uuids': uuids}))
            UUIDS = uuids
        if config:
            self.queue.put(json.dumps({'config': config}))
            CONFIG = config

    def run(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(self.interval, 1, self.main_loop, (scheduler,))
        scheduler.run()


class AnalysisProcess(Process):
    def __init__(self, interval, queue):
        super(AnalysisProcess, self).__init__()
        self.interval = interval
        self.queue = queue

    def main_loop(self, sc):
        sc.enter(self.interval, 1, self.main_loop, (sc,))
        global UUIDS, CONFIG
        while not self.queue.empty():
            queue_data = self.queue.get()
            queue_data = json.loads(queue_data)
            uuids = queue_data.get('uuids', None)
            config = queue_data.get('config', None)
            if uuids:
                UUIDS = uuids
            if config:
                CONFIG = config

        try:
            analysis_worker()
        except Exception as error:
            logging.exception(str(error))

    def run(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(self.interval, 1, self.main_loop, (scheduler,))
        scheduler.run()


def init_server():
    global HOSTNAME, UUIDS
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('www.baidu.com', 80))
    HOSTNAME = s.getsockname()[0]
    s.close()

    UUIDS = get_current_uuids()


def kill_process(processes, signum, frame):
    for process in processes:
        process.terminate()

    exit(0)


def vm_agent_run():
    queue = Queue()

    init_server()

    heartbeat_process = HeartbeatProcess(CONF.heartbeat_interval, queue)
    heartbeat_process.daemon = True

    collector_process = CollectorProcess(CONF.collector_interval)
    collector_process.daemon = True

    analysis_process = AnalysisProcess(CONF.analysis_interval, queue)
    analysis_process.daemon = True

    heartbeat_process.start()
    collector_process.start()
    analysis_process.start()

    while True:
        signal.signal(signal.SIGTERM, partial(kill_process, [heartbeat_process, collector_process, analysis_process]))
        time.sleep(3600)