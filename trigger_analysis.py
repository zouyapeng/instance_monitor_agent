#!/usr/bin/env python


def get_data_queue(uuid, item, period):
    pass


def analysis(uuid, config):
    item = config.get('item')
    period = config.get('period')
    method = config.get('method')
    method_option = config.get('method_option')
    threshold = config.get('threshold')

    data = get_data_queue(uuid, item, period)


def set_trigger(trigger_id):
    pass