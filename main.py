#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import glob
import json
import os
import sys

import dns.resolver
from twisted.internet import reactor, ssl

from BaneBot.BaneBot import BaneBot, BaneBotFactory
from utils.jsonhooks import _decode_dict
from utils.privs import drop_privs

if __name__ == '__main__':
    # Set the default encoding to utf-8
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # Drop privileges of the bot
    drop_privs()

    # Get a list of all networks to connect to
    network_configs = glob.glob('config/networks/*.conf')
    networks = [json.loads(open(nw_config).read(), object_hook=_decode_dict) \
                for nw_config in network_configs]

    # Load the main config file and add the base dir 
    main_config = json.loads(open('config/main.conf').read())
    main_config['base_dir'] = os.getcwd()

    for network in networks:
        bbf = BaneBotFactory(main_config, network)
        if network['force_ipv6']:
            answers = dns.resolver.query(network['server'], 'AAAA')
            if not answers:
                quit('{} did not have an AAAA records'.format(network['server']))

            host = list(answers)[0].address
        else:
            host = network['server']
        port = network['port']

        if network.get('ssl', False):
            reactor.connectSSL(host, port, bbf, ssl.ClientContextFactory())
        else:
            reactor.connectTCP(host, port, bbf)

    # Enter the event-loop
    reactor.run()
