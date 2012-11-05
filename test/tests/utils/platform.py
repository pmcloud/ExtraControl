#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from fabric import api


def shellExt(name):
    if isWindows():
        return name + '.bat'
    else:
        return name + '.sh'


def isLinux(reason=False):
    if reason:
        return api.env.aruba_platform.os_type == 'linux', 'requires Linux'
    else:
        return api.env.aruba_platform.os_type == 'linux'


def isBsd(reason=False):
    if reason:
        return api.env.aruba_platform.os_type == 'bsd', 'requires BSD'
    else:
        return api.env.aruba_platform.os_type == 'bsd'


def isWindows(reason=False):
    if reason:
        return api.env.aruba_platform.os_type == 'windows', 'requires Windows'
    else:
        return api.env.aruba_platform.os_type == 'windows'


def isUbuntu(reason=False):
    if reason:
        return api.env.aruba_platform.distribution == 'ubuntu', 'requires Ubuntu'
    else:
        return api.env.aruba_platform.distribution == 'ubuntu'


def isCentOS(reason=False):
    if reason:
        return api.env.aruba_platform.distribution == 'centos', 'requires CentOS'
    else:
        return api.env.aruba_platform.distribution == 'centos'


def isEndian(reason=False):
    if reason:
        return api.env.aruba_platform.distribution == 'endian', 'requires Endian'
    else:
        return api.env.aruba_platform.distribution == 'endian'


def isFreeNAS(reason=False):
    if reason:
        return api.env.aruba_platform.distribution == 'freenas', 'requires FreeNAS'
    else:
        return api.env.aruba_platform.distribution == 'freenas'


def isPfSense(reason=False):
    if reason:
        return api.env.aruba_platform.distribution == 'pfsense', 'requires pfSense'
    else:
        return api.env.aruba_platform.distribution == 'pfsense'


def onlyIf(cond):
    def wrap(func):
        def wrapped(*args, **kwargs):
            ok, msg = cond(True)

            if not ok:
                raise unittest.SkipTest(msg)
            else:
                func(*args, **kwargs)

        return wrapped

    return wrap


class Platform(object):
    def __init__(self, platform_id, os_type, os_version, bits, distribution=None):
        self.platform_id = platform_id
        self.os_type = os_type
        self.os_version = os_version
        self.bits = bits
        self.distribution = distribution

    def description(self):
        if self.distribution:
            return '%s %s %s (%d bit)' % (
                self.distribution,
                self.os_type,
                self.os_version,
                self.bits)
        else:
            return '%s %s (%d bit)' % (
                self.os_type,
                self.os_version,
                self.bits)


PLATFORMS = dict((p.platform_id, p) for p in [
        Platform('ubuntu-10.04-64', 'linux', '10.04', 64, 'ubuntu'),
        Platform('windows-2008-64', 'windows', '2008', 64),
        Platform('windows-2003-32', 'windows', '2003', 32),
        Platform('centos-5.6-64', 'linux', '5.6', 64, 'centos'),
        Platform('openfiler-2.99-64', 'linux', '2.99.1', 64, 'openfiler'),
        Platform('freenas-8.02-64', 'bsd', '8.0.2', 64, 'freenas'),
        Platform('pfsense-2.01-64', 'bsd', '2.0.1', 64, 'pfsense'),
        Platform('endian-2.5-32', 'linux', '2.5.0', 32, 'endian'),
])


def get(name):
    return PLATFORMS[name]
