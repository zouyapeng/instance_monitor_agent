#!/usr/bin/env python
# -*- coding: utf8 -*-

import httplib
import urllib
import json


server_host = '192.168.213.230'

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

    print body
    print agent_id, config

    return agent_id, config