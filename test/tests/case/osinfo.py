#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import utils

from fabric import api

# TODO check real names
NAMES = {
    ('linux', 'ubuntu'): 'Ubuntu',
    ('linux', 'centos'): 'CentOS',
    ('linux', 'openfiler'): 'Openfiler',
    ('linux', 'endian'): 'Endian',
    ('windows', None):   'Windows',
    ('bsd', 'freenas'):  'FreeNAS',
    ('bsd', 'pfsense'):  'pfSense',
}


def callOsInfo():
    tree = utils.callRpcCommand('osinfo')

    return tree.findtext('name'), tree.findtext('version')


class TestOsInfo(unittest.TestCase):
    def testGet(self):
        name, version = callOsInfo()
        conf_name = NAMES[api.env.aruba_platform.os_type,
                          api.env.aruba_platform.distribution]

        self.assertEquals(conf_name, name)
        self.assertEquals(api.env.aruba_platform.os_version, version)
