#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest, files
from utils.platform import isWindows


class TestRemove(unittest.TestCase, utils.Assert):
    def setUp(self):
        utils.uploadUserModule('remove1',
                               files.executable(isWindows(), 'xmlecho'))

    def testRemoveModule(self):
        tree = utils.callRpcCommand('remove usermodule remove1', no_xml=True)

        tree = utils.callRpcCommand("modulemng list")

        self.assertNotIn('remove1', [n.text for n in tree.findall('module/name')])

    def testRemoveSystemModule(self):
        result = utils.callRpcCommandError('remove usermodule modulemng')

    def testRemoveNonExistingModule(self):
        result = utils.callRpcCommandError('remove usermodule nonexistingmodule')
