#!/usr/bin/env python

import logging
from pymongo import MongoClient

LOGGING = logging.getLogger('')

MONGODB_HOST = '192.168.213.230'
MONGODB_PORT = 27017
MONGODB_EXPIRE = 30 * 24 * 60 * 60

def mongo_save(datas):
    mongodb_client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = mongodb_client.VmDataBase

    for data in datas:
        try:
            collection = db[data['uuid']]
            collection.create_index('time', expireAfterSeconds=MONGODB_EXPIRE)
            collection.insert_one(data)
        except Exception, error:
            LOGGING.exception(error)