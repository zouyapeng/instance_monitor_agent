#!/usr/bin/env python
from mongo import *
from heartbeat import set_trigger
import datetime


def get_data_queue(uuid, item, item_option, period):
    data_queue = []
    start = datetime.datetime.now() - datetime.timedelta(minutes=period)

    if item == 'cpu usage':
        data_queue = mongodb_get_cpu(uuid=uuid, start=start, end=None, flag=True)
    elif item == 'memory usage':
        data_queue = mongodb_get_memory(uuid=uuid, start=start, end=None, flag=True)
    elif item == 'disk read speed':
        data_queue = mongodb_get_disk(uuid=uuid, start=start, end=None, item='rds', item_option=item_option, flag=True)
    elif item == 'disk write speed':
        data_queue = mongodb_get_disk(uuid=uuid, start=start, end=None, item='wrs', item_option=item_option, flag=True)
    elif item == 'incoming network traffic':
        data_queue = mongodb_get_interface(uuid=uuid, start=start, end=None, item='rxs', item_option=item_option, flag=True)
    elif item == 'outgoing network traffic':
        data_queue = mongodb_get_interface(uuid=uuid, start=start, end=None, item='txs', item_option=item_option, flag=True)
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

        return eval(analysis_string)
    else:
        return False


def analysis(uuid, configs):
    for trigger in configs:
        item = trigger.get('item')
        item_option = trigger.get('item_option')
        period = trigger.get('period')
        method = trigger.get('method')
        method_option = trigger.get('method_option')
        threshold = trigger.get('threshold')

        data = get_data_queue(uuid, item, item_option, period)

        analysis_status = analysis_trigger(method, method_option, threshold, data)
        set_trigger(trigger, analysis_status)
