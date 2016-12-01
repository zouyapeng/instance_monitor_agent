#!/usr/bin/env python
import logging
import datetime
from pymongo import MongoClient, DESCENDING
import pprint

LOGGING = logging.getLogger('')

MONGODB_HOST = '192.168.213.230'
MONGODB_PORT = 27017
MONGODB_EXPIRE = 30 * 24 * 60 * 60


def mongodb_get_disk(uuid, start, end, item):
    mongodb_client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = mongodb_client.VmDataBase
    collection = db[uuid]

    if start is not None and end is not None:
        match = {
            '$match': {
                'time': {
                    '$gt': start,
                    '$lt': end
                }
            }
        }
    elif start is not None and end is None:
        match = {
            '$match': {
                'time': {
                    '$gt': start
                }
            }
        }
    else:
        match = {'$match': {}}

    if item == 'rds':
        item = 'rd_bytes_speed'
    elif item == 'rdops':
        item = 'rd_req_speed'
    elif item == 'wrs':
        item = 'wr_bytes_speed'
    elif item == 'wrops':
        item = 'wr_req_speed'
    else:
        return []

    project = {
        '$project': {
            '_id': 0,
            'time': 1,
            'disk': 1
        }
    }

    results = collection.aggregate([match, project])

    data = {}
    for result in results:
        for key, value in result['disk'].items():
            if data.get(key, None) is None:
                data[key] = []

            data[key].append({'time': result['time'], 'value': value[item]})

    return data


def mongodb_get_last(uuid):
    mongodb_client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = mongodb_client.VmDataBase
    collection = db[uuid]

    sort = {
        '$sort': {
            'time': -1
        }
    }

    datas = collection.aggregate([sort])

    try:
        data = datas.next()
    except StopIteration:
        data = {}

    for key, value in data['disk'].items():
        data['disk'][key].pop('err')
        data['disk'][key].pop('rd_bytes')
        data['disk'][key].pop('rd_req')
        data['disk'][key].pop('rd_req_speed')
        data['disk'][key].pop('wr_bytes')
        data['disk'][key].pop('wr_req')
        data['disk'][key].pop('wr_req_speed')

    for key, value in data['interface'].items():
        data['interface'][key].pop('rx_bytes')
        data['interface'][key].pop('rx_drop')
        data['interface'][key].pop('rx_errs')
        data['interface'][key].pop('rx_packets')
        data['interface'][key].pop('tx_bytes')
        data['interface'][key].pop('tx_drop')
        data['interface'][key].pop('tx_errs')
        data['interface'][key].pop('tx_packets')

    return {'uuid': data['uuid'],
            'time': data['time'],
            'cpu_usage': data['cpu']['cpu_usage'],
            'memory_usage': data['memory']['usage'],
            'disk': data['disk'],
            'interface': data['interface']}


# data = mongodb_get_disk('0d5b82ba-f20b-49b3-beeb-14cd76612692',
#                             item='wrops',
#                             start=datetime.datetime.strptime('2016-11-28 22:00:00', '%Y-%m-%d %H:%M:%S'),
#                             end=None)

data = mongodb_get_last('0d5b82ba-f20b-49b3-beeb-14cd76612692')

pprint.pprint(data)