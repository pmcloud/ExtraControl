#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser, re
import platform


class Host(object):
    def __init__(self, address, user, platform, vm_name, install_path):
        self.address = address
        self.user = user
        self.platform = platform
        self.vm_name = vm_name
        self.install_path = install_path

    @property
    def hostString(self):
        return '%s@%s' % (self.user, self.address)


class Test(object):
    def __init__(self, hosts):
        self.hosts = hosts


class Configuration(object):
    def __init__(self):
        self.default_test = None
        self.xmlrpc_url = None
        self.tests = {}
        self.hosts = {}


def parse(path):
    parser = ConfigParser.ConfigParser()
    parser.read(path)
    config = Configuration()
    tests = []

    for section in parser.sections():
        if parser.has_option(section, 'hosts'):
            tests.append(section)
        elif parser.has_option(section, 'os'):
            # TODO validation, error messages
            config.hosts[section] = Host(
                parser.get(section, 'address'),
                parser.get(section, 'user'),
                platform.get(parser.get(section, 'os')),
                parser.get(section, 'vm-name'),
                parser.get(section, 'install-path'),
            )

    config.default_test = tests[0]
    config.xmlrpc_url = parser.get('global', 'xmlrpc-url')

    for test in tests:
        # TODO validation, error messages
        hosts = re.split(',\s*', parser.get(test, 'hosts'))

        config.tests[test] = Test(
            [config.hosts[h] for h in hosts]
        )

    return config
