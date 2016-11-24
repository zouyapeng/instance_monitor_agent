#!/usr/bin/env python
# -*- coding: utf8 -*-

import httplib
import json


server_host = '192.168.7.164'

heartbeat_uri = '/heartbeat/'


def heartbeat(agent_id=None, hostname=None, uuids=None):
    if agent_id and uuids is not None:
        body = json.dumps({'id': agent_id, 'uuids': uuids})
    elif agent_id and uuids is None:
        body = json.dumps({'id': agent_id})
    else:
        body = json.dumps({'hostname': hostname, 'uuids': uuids})

    conn = httplib.HTTPConnection(server_host, port=9339)
    headers = {'Content-type': 'application/json'}
    conn.request('POST', heartbeat_uri, body=body, headers=headers)
    response = conn.getresponse()
    response_str = json.loads(response.read())
    conn.close()

    agent_id = response_str.get('id', None)
    config = response_str.get('config', None)

    return agent_id, config