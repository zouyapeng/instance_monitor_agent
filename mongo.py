#!/usr/bin/env python

import logging
import datetime
from pymongo import MongoClient, DESCENDING

LOGGING = logging.getLogger('')

MONGODB_HOST = '192.168.213.230'
MONGODB_PORT = 27017
MONGODB_EXPIRE = 30 * 24 * 60 * 60


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


def mongodb_get_cpu(uuid, start, end):
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

    results =collection.aggregate([match, {'$project': {'_id': 0, 'cpu.cpu_usage': 1}}])

    return [result['cpu']['cpu_usage'] for result in results]


def mongodb_get_memory(uuid, start, end):
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

    results = collection.aggregate([match, {'$project': {'_id': 0, 'memory.usage': 1}}])

    return [result['memory']['usage'] for result in results]


def mongodb_get_disk(uuid, item, start, end):
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

    results = collection.aggregate([match, {'$project': {'_id': 0, 'disk': 1}}])


    results_re = {}
    for result in results:
        for disk, value in result['disk'].items():
            if results_re.get(disk, None) is None:
                results_re[disk] = []

            if item == 'rds':
                results_re[disk].append(value.get('rd_bytes_speed'))
            elif item == 'rdops':
                results_re[disk].append(value.get('rd_req_speed'))
            elif item == 'wrs':
                results_re[disk].append(value.get('wr_bytes_speed'))
            elif item == 'wrops':
                results_re[disk].append(value.get('wr_req_speed'))
            else:
                results_re[disk].append(None)

    return results_re


def mongodb_get_interface(uuid, item, start, end):
    pass


print mongodb_get_disk('0d5b82ba-f20b-49b3-beeb-14cd76612692',
                       item='wrs',
                       start=datetime.datetime.strptime('2016-11-24 01:00:00', '%Y-%m-%d %H:%M:%S'),
                       end=None)