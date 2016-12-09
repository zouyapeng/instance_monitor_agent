#!/usr/bin/env python

import logging

from pymongo import MongoClient
from config import CONF

LOGGING = logging.getLogger('')

MONGODB_HOST = CONF.mongodb_host
MONGODB_PORT = CONF.mongodb_port
MONGODB_EXPIRE = CONF.mongodb_expire


def mongodb_save(datas):
    mongodb_client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = mongodb_client.VmDataBase

    for data in datas:
        try:
            collection = db[data['uuid']]
            collection.create_index('time', expireAfterSeconds=MONGODB_EXPIRE)
            collection.insert_one(data)
        except Exception, error:
            LOGGING.exception(error)


def mongodb_get_last(uuid):
    pass


def mongodb_get_cpu(uuid, start, end, flag=False):
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

    results =collection.aggregate([match, {'$project': {'_id': 0, 'time': 1, 'cpu.cpu_usage': 1}}])

    if flag:
        return [result['cpu']['cpu_usage'] for result in results]

    return [{'time': result['time'], 'cpu_usage': result['cpu']['cpu_usage']} for result in results]


def mongodb_get_memory(uuid, start, end, flag=False):
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

    results = collection.aggregate([match, {'$project': {'_id': 0, 'time': 1, 'memory.usage': 1}}])

    if flag:
        return [result['memory']['usage'] for result in results]

    return [{'time': result['time'], 'memory_usage': result['memory']['usage']} for result in results]


def mongodb_get_disk(uuid, start, end, item, item_option, flag=False):
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
            'disk.{}.{}'.format(item_option, item): 1
        }
    }

    results = collection.aggregate([match, project])

    if flag:
        return [result['disk'][item_option][item] for result in results]

    return [{'time': result['time'], item: result['disk'][item_option][item]} for result in results]


def mongodb_get_interface(uuid, start, end, item, item_option, flag):
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

    if item == 'rxs':
        item = 'rx_bytes_speed'
    elif item == 'txs':
        item = 'tx_bytes_speed'
    else:
        return []

    project = {
        '$project': {
            '_id': 0,
            'time': 1,
            'interface.{}.{}'.format(item_option, item): 1
        }
    }

    results = collection.aggregate([match, project])

    if flag:
        return [result['interface'][item_option][item] for result in results]

    return [{'time': result['time'], item: result['interface'][item_option][item]} for result in results]
