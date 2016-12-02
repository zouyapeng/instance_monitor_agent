#!/usr/bin/env python

import libvirt
import time
import logging
import datetime
from copy import deepcopy

from xml.etree import ElementTree
from mongo import mongodb_save

PRE_DATAS = None
LOGGING = logging.getLogger('')
DATA_TEMPLATE = {
    'uuid': None,
    'time': None,
    'cpu': None,
    'memory': None,
    'disk': None,
    'interface': None
}


class LibvirtClient(object):
    def __init__(self):
        self.conn = None
        self.try_count = 0
        while self.conn is None and self.try_count < 3:
            self.conn = libvirt.open(None)
            self.try_count += 1
            time.sleep(0.1)

        if self.conn is None:
            raise libvirt.VIR_ERR_INTERNAL_ERROR

        self.domains = self.conn.listAllDomains()

    def get_all_data(self):
        domain_data_list = list()
        for domain in self.domains:
            domain_data = dict()
            domain_data.update(DATA_TEMPLATE)
            domain_data.update({'uuid': domain.UUIDString()})
            domain_data.update({'time': datetime.datetime.now()})
            if domain.isActive() == 1:
                domain_data.update({'cpu': {'cpu_number': self.get_cpu_num(domain),
                                            'cpu_time': self.get_cpu_time(domain),
                                            'cpu_usage': 0L}})
                domain_data.update({'disk': self.get_disk_statistics(domain)})
                domain_data.update({'memory': self.get_memory_statistics(domain)})
                domain_data.update({'interface': self.get_interface_statistics(domain)})

            domain_data_list.append(domain_data)

        return domain_data_list

    @staticmethod
    def get_cpu_num(domain):
        return domain.info()[3]

    @staticmethod
    def get_cpu_time(domain):
        return domain.getCPUStats(True)[0]['cpu_time']

    @staticmethod
    def get_memory_statistics(domain):
        memory_stats = domain.memoryStats()
        memory_total = memory_stats.get('actual')
        memory_unused = memory_stats.get('unused', None)
        memory_available = memory_stats.get('available', None)

        if memory_available is not None:
            memory_used = memory_total - memory_unused
            return {'actual': memory_total,
                    'available': memory_available,
                    'unused': memory_unused,
                    'used': memory_used,
                    'usage': round(memory_used * 100.00 / memory_total, 2)}
        else:
            return {'actual': memory_total,
                    'available': memory_available,
                    'unused': memory_unused,
                    'used': None,
                    'usage': None}

    @staticmethod
    def get_disk_statistics(domain):
        disks_statistics = dict()

        tree = ElementTree.fromstring(domain.XMLDesc())

        for target in tree.findall('devices/disk/target'):
            name = target.get('dev')
            rd_req, rd_bytes, wr_req, wr_bytes, err = domain.blockStats(name)
            disks_statistics.update({name: {'rd_req': rd_req,
                                            'rd_req_speed': 0L,
                                            'rd_bytes': rd_bytes,
                                            'rd_bytes_speed': 0L,
                                            'wr_req': wr_req,
                                            'wr_req_speed': 0L,
                                            'wr_bytes': wr_bytes,
                                            'wr_bytes_speed': 0L,
                                            'err': err}})

        return disks_statistics

    @staticmethod
    def get_interface_statistics(domain):
        ifaces_statistics = dict()

        tree = ElementTree.fromstring(domain.XMLDesc())
        ifaces = [iface.get('dev') for iface in tree.findall('devices/interface/target')]

        for iface in ifaces:
            stats = domain.interfaceStats(iface)
            ifaces_statistics.update({
                iface: {'rx_bytes': stats[0],
                        'rx_bytes_speed': 0L,
                        'rx_packets': stats[1],
                        'rx_errs': stats[2],
                        'rx_drop': stats[3],
                        'tx_bytes': stats[4],
                        'tx_bytes_speed': 0L,
                        'tx_packets': stats[5],
                        'tx_errs': stats[6],
                        'tx_drop': stats[7]}
            })

        return ifaces_statistics

    def close(self):
        self.conn.close()


def get_current_uuids():
    try:
        client = LibvirtClient()
    except libvirt.VIR_ERR_INTERNAL_ERROR:
        LOGGING.error('Can not connect to libvirt!')
        return []

    uuids = [domain.UUIDString() for domain in client.domains]
    client.close()

    return uuids


def set_cpu_usage(pre_data, data, timedelta):
    cpu_usage = (data['cpu']['cpu_time'] - pre_data['cpu']['cpu_time']) * 100.00 \
                / data['cpu']['cpu_number'] \
                / (timedelta * 1000 * 1000 * 1000)

    data['cpu']['cpu_usage'] = round(cpu_usage, 2)


def set_disk_speed(pre_data, data, timedelta):
    for key, value in data['disk'].items():
        pre_disk_data = pre_data['disk'].get(key, None)
        if pre_disk_data is None:
            continue

        data['disk'][key]['rd_req_speed'] = round((value['rd_req'] - pre_disk_data['rd_req']) / timedelta, 2)
        data['disk'][key]['rd_bytes_speed'] = round((value['rd_bytes'] - pre_disk_data['rd_bytes']) / timedelta, 2)
        data['disk'][key]['wr_req_speed'] = round((value['wr_req'] - pre_disk_data['wr_req']) / timedelta, 2)
        data['disk'][key]['wr_bytes_speed'] = round((value['wr_bytes'] - pre_disk_data['wr_bytes']) / timedelta, 2)


def set_interface_speed(pre_data, data, timedelta):
    for key, value in data['interface'].items():
        pre_interface_data = pre_data['interface'].get(key, None)
        if pre_interface_data is None:
            continue

        data['interface'][key]['rx_bytes_speed'] = round((value['rx_bytes'] - pre_interface_data['rx_bytes']) * 1.00 / timedelta, 2)
        data['interface'][key]['tx_bytes_speed'] = round((value['tx_bytes'] - pre_interface_data['tx_bytes']) * 1.00 / timedelta, 2)


def set_speed(pre_data, data):
    if data['cpu'] is None or pre_data['cpu'] is None:
        return

    timedelta = (data.get('time') - pre_data.get('time')).total_seconds()
    try:
        set_cpu_usage(pre_data, data, timedelta)
    except Exception:
        LOGGING.exception('%s set cpu usage failed' % data['uuid'])

    try:
        set_disk_speed(pre_data, data, timedelta)
    except Exception:
        LOGGING.exception('%s set disk speed failed' % data['uuid'])

    try:
        set_interface_speed(pre_data, data, timedelta)
    except Exception:
        LOGGING.exception('%s set interface speed failed' % data['uuid'])


def collector():
    global PRE_DATAS

    try:
        client = LibvirtClient()
    except libvirt.VIR_ERR_INTERNAL_ERROR:
        LOGGING.error('Can not connect to libvirt!')
        return

    datas = client.get_all_data()
    client.close()

    if len(datas) == 0:
        return

    if PRE_DATAS is not None:
        for i in range(len(datas)):
            uuid = datas[i].get('uuid')
            pre_data = filter(lambda domain: domain['uuid'] == uuid, PRE_DATAS)

            if len(pre_data) == 0:
                continue
            try:
                set_speed(pre_data[0], datas[i])
            except Exception:
                LOGGING.exception('%s set speed failed' % datas[i]['uuid'])

    try:
        if PRE_DATAS is not None:
            mongodb_save(datas)
    except Exception:
        LOGGING.exception('save datas to mongo failed!')

    PRE_DATAS = deepcopy(datas)
