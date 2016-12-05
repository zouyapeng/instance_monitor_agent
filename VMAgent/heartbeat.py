#!/usr/bin/env python
# -*- coding: utf8 -*-

import httplib
import json

from config import CONF

heartbeat_uri = '/heartbeat/'
trigger_uri = '/trigger/'


def heartbeat(agent_id=None, hostname=None, uuids=None):
    if agent_id and uuids is not None:
        body = json.dumps({'id': agent_id, 'uuids': uuids, 'agent': True})
    elif agent_id and uuids is None:
        body = json.dumps({'id': agent_id, 'agent': True})
    else:
        body = json.dumps({'hostname': hostname, 'uuids': uuids, 'agent': True})

    conn = httplib.HTTPConnection(CONF.server_host, port=CONF.server_port)
    headers = {'Content-type': 'application/json'}
    conn.request('POST', heartbeat_uri, body=body, headers=headers)
    response = conn.getresponse()
    response_str = json.loads(response.read())
    conn.close()

    agent_id = response_str.get('id', None)
    config = response_str.get('config', None)

    return agent_id, config


def get_trigger(trigger_id):
    conn = httplib.HTTPConnection(CONF.server_host, port=CONF.server_port)
    headers = {'Content-type': 'application/json'}
    conn.request('GET', ''.join([trigger_uri, str(trigger_id), '/']), headers=headers)
    response = conn.getresponse()
    response_str = json.loads(response.read())
    conn.close()

    return response_str


def set_trigger(trigger, status):
    trigger_status = trigger.get('status', None)

    if trigger_status == status or trigger_status is None:
        return

    conn = httplib.HTTPConnection(CONF.server_host, port=CONF.server_port)
    headers = {'Content-type': 'application/json'}
    trigger['status'] = status
    trigger['agent'] = True
    body = json.dumps(trigger)
    conn.request('PUT', ''.join([trigger_uri, str(trigger['id']), '/']), body=body, headers=headers)
    response = conn.getresponse()
    response_str = json.loads(response.read())
    conn.close()

    return response_str
