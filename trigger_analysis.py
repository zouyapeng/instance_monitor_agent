#!/usr/bin/env python
import datetime
from mongo import *
from heartbeat import set_trigger, get_trigger


def get_data_queue(uuid, item, period):
    data_queue = []
    start = datetime.datetime.now() - datetime.timedelta(minutes=period)

    if item == 'cpu usage':
        data_queue = mongodb_get_cpu(uuid=uuid, start=start, end=None, flag=True)
    elif item == 'memory usage':
        data_queue = mongodb_get_memory(uuid=uuid, start=start, end=None, flag=True)
    elif item == 'disk read speed':
        data_queue = mongodb_get_disk(uuid=uuid, start=start, end=None, item='rds', flag=True)
    elif item == 'disk write speed':
        data_queue = mongodb_get_disk(uuid=uuid, start=start, end=None, item='wrs', flag=True)
    elif item == 'incoming network traffic':
        data_queue = mongodb_get_interface(uuid=uuid, start=start, end=None, item='rxs', flag=True)
    elif item == 'outgoing network traffic':
        data_queue = mongodb_get_interface(uuid=uuid, start=start, end=None, item='txs', flag=True)
    else:
        pass

    return data_queue


def analysis_trigger(method, method_option, threshold, data_queue):
    if isinstance(data_queue, dict):
        pass
    elif isinstance(data_queue, list):
        if method == 'avg':
            method = 'sum'
            threshold = int(threshold) * len(data_queue)
        analysis_string = ''.join([method, '(', str(data_queue), ')', method_option, str(threshold)])

        # print analysis_string
        # print eval(analysis_string)
        return eval(analysis_string)
    else:
        return False


def analysis(uuid, configs):
    for config in configs:
        item = config.get('item')
        period = config.get('period')
        method = config.get('method')
        method_option = config.get('method_option')
        threshold = config.get('threshold')

        data = get_data_queue(uuid, item, period)

        analysis_status = analysis_trigger(method, method_option, threshold, data)
        set_trigger(get_trigger(config['id']), analysis_status)
