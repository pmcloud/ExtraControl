#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest, files
from utils.platform import isWindows


class TestUpdatePlugin(unittest.TestCase, utils.Assert):
    def setUp(self):
        utils.savePristineState()

    def tearDown(self):
        utils.restorePristineState()

    def testUpdate(self):
        tree = utils.callRpcCommand('updateModule systemstatus 100',
                                    files.module('xmlecho'), no_xml=True)

        utils.checkModuleAndVersion('systemstatus', 100)

    def testUpdateLowerVersion(self):
        tree = utils.callRpcCommand('updateModule systemstatus 100',
                                    files.module('xmlecho'), no_xml=True)

        utils.checkModuleAndVersion('systemstatus', 100)

        result = utils.callRpcCommandError('updateModule systemstatus 9',
                                           files.executable(isWindows(), 'xmlecho'))

        utils.checkModuleAndVersion('systemstatus', 100)


class TestUpdateErrors(unittest.TestCase, utils.Assert):
    def testUpdateNonExistingModule(self):
        result = utils.callRpcCommandError('updateModule nonexistingmodule 2',
                                           files.module('xmlecho'))

    @unittest.skip("hangs")
    def testInvalidBase64(self):
        result = utils.callRpcCommandError('updateModule systemstatus 2',
                                           base64_body='ZHVt)bVudAo=')

    def testUpdateSystemModule(self):
        result = utils.callRpcCommandError('updateModule modulemng 100000',
                                           files.executable(isWindows(), 'xmlecho'))
