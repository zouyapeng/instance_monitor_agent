#!/usr/bin/env python
from oslo.config import cfg
from oslo.config import types

CONF = cfg.CONF

PortType = types.Integer(1, 65535)

# [DEFAULT]
common_opts = [
    cfg.IPOpt('server_host',
              default='127.0.0.1',
              help='instance monitor server host'),

    cfg.Opt('server_port',
            type=PortType,
            default=9339,
            help='instance monitor server port'),

    cfg.IntOpt('heartbeat_interval',
               default=30,
               help='heartbeat interval between agent and server. Default=30'),

    cfg.IntOpt('collector_interval',
               default=60,
               help='instances monitor data collection interval. Default=60'),

    cfg.IntOpt('analysis_interval',
               default=60,
               help='instances monitor data analysis interval. Default=60'),

    cfg.StrOpt('log_path',
               default='/var/log/VMAgent/VMAgent.log',
               help='log path')
]

CONF.register_cli_opts(common_opts)


# [mongodb]
mongodb_opt_group = cfg.OptGroup(name='mongodb', title='mongodb')
mongodb_opts = [
    cfg.IPOpt('host',
              default='0.0.0.0',
              help='mongodb host'),

    cfg.Opt('port',
            type=PortType,
            default=27017,
            help='mongodb port'),

    cfg.IntOpt('expire',
               default=2592000,
               help='data expire time'),
]

CONF.register_group(mongodb_opt_group)
CONF.register_opts(mongodb_opts, mongodb_opt_group)

CONF(default_config_files=['/etc/VMAgent/VMAgent.conf'])