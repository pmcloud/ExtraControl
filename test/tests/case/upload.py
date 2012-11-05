#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest, files
from utils.platform import isWindows


class TestUpload(unittest.TestCase, utils.Assert):
    def setUp(self):
        utils.deleteUserModule("upload1")
        utils.deleteUserModule("upload2")
        utils.deleteUserModule("upload3")

    def testUploadModule(self):
        utils.uploadUserModule('upload1', 'dummy content')

        # Check module info
        tree = utils.callRpcCommand('modulemng get upload1')

        self.assertEquals('modules', tree.tag)
        self.assertEquals(1, len(tree))

        module = tree[0]
        self.assertEquals('module', module.tag)
        self.assertChildText(module, 'name', 'upload1')
        self.assertChildText(module, 'version', '0')
        self.assertChildText(module, 'type', 'Custom')
        self.assertChildText(module, 'upgradable', 'true')

    def testReuploadModule(self):
        utils.uploadUserModule('upload1', 'dummy content')

        # uploading again should fail
        result = utils.callRpcCommandError('upload usermodule upload1',
                                           'dummy content')

    @unittest.skip("hangs")
    def testInvalidBase64(self):
        result = utils.callRpcCommandError('upload usermodule upload2',
                                           base64_body='ZHVt)bVudAo=')

    def testNotExecutable(self):
        utils.uploadUserModule('upload3',
                               files.executable(isWindows(), 'xmlecho'))

        result = utils.callRpcCommandError('upload3')
