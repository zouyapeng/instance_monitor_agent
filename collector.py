#!/usr/bin/env python

import libvirt
import time
import datetime
from pymongo import MongoClient
from xml.etree import ElementTree


DATA_TEMPLATE = {
    'uuid': None,
    'time': None,
    'cpu': None,
    'memory': None,
    'disk': [],
    'interface': []
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
            domain_data.update({'cpu': {'cpu_number': self.get_cpu_num(domain),
                                        'cpu_time': self.get_cpu_time(domain),
                                        'cpu_usage': 0}})
            domain_data.update({'disk': self.get_disk_statistics(domain)})

            print self.get_memory_statistics(domain)

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
        return domain.memoryStats()

    @staticmethod
    def get_disk_statistics(domain):
        disks_statistics = list()

        tree = ElementTree.fromstring(domain.XMLDesc())

        for target in tree.findall('devices/disk/target'):
            disk_statistics = {}
            name = target.get('dev')
            rd_req, rd_bytes, wr_req, wr_bytes, err = domain.blockStats(name)
            disk_statistics.update({name: {'rd_req': rd_req,
                                           'rd_req_speed': 0,
                                           'rd_bytes': rd_bytes,
                                           'rd_bytes_speed': 0,
                                           'wr_req': wr_req,
                                           'wr_req_speed': 0,
                                           'wr_bytes': wr_bytes,
                                           'wr_bytes_speed': 0,
                                           'err': err}})

            disks_statistics.append(disk_statistics)

        return disks_statistics

    @staticmethod
    def get_interface_statistics(domain):
        ifaces_statistics = list()

        tree = ElementTree.fromstring(domain.XMLDesc())
        ifaces = [iface.get('dev') for iface in tree.findall('devices/interface/target')]

        for iface in ifaces:
            stats = domain.interfaceStats(iface)
            iface_statistics = {
                'devname': iface,
                'receive': {
                    'bytes': stats[0],
                    'packets': stats[1],
                    'errs': stats[2],
                    'drop': stats[3],
                },
                'transmit': {
                    'bytes': stats[4],
                    'packets': stats[5],
                    'errs': stats[6],
                    'drop': stats[7],
                }
            }

            ifaces_statistics.append(iface_statistics)

        return ifaces_statistics

    def close(self):
        self.conn.close()


def get_current_uuids():
    client = LibvirtClient()
    uuids = [domain.UUIDString() for domain in client.domains]
    client.close()

    return uuids


def collector():
    client = LibvirtClient()
    import pprint
    datas = client.get_all_data()
    # pprint.pprint(datas)