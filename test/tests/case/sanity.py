#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest

from fabric import api
from utils.platform import *


class TestSanityLinux(unittest.TestCase):
    failureException = utils.FatalError

    @onlyIf(isLinux)
    def testHostType(self):
        res = api.run('uname -s')

        self.assertEquals('Linux', res)


class TestSanityWindows(unittest.TestCase):
    failureException = utils.FatalError

    @onlyIf(isWindows)
    def setUp(self):
        pass

    def testHostType(self):
        res = api.run('uname -s')

        self.assertEquals('CYGWIN_NT-6.1-WOW64', res)


class TestSanityService(unittest.TestCase):
    def testCallService(self):
        # only tests we can reach the service and we get back a
        # well-formed response with success status
        try:
            tree = utils.callRpcCommand("modulemng list")
        except Exception as e:
            raise utils.FatalError(e)


if __name__ == '__main__':
    utils.main()
