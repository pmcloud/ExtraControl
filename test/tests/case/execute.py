#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest, files
from utils.platform import isWindows, shellExt


class TestExec(unittest.TestCase, utils.Assert):
    def setUp(self):
        utils.uploadUserModule(shellExt("xmlecho"),
                               files.executable(isWindows(), 'xmlecho'))

    def testExecInternalModule(self):
        result = utils.callRpcCommandError("exec script modulemng list")

    def testExecPlugin(self):
        result = utils.callRpcCommandError("exec script systemstatus")

    def testExecNoArgs(self):
        tree = utils.callRpcCommand("exec script %s" % shellExt("xmlecho"))

        self.assertEquals('test', tree.tag)
        self.assertEquals(0, len(list(tree)))

    def testExecArgs(self):
        tree = utils.callRpcCommand("exec script %s arg1 arg2" % shellExt("xmlecho"))

        self.assertEquals('test', tree.tag)
        self.assertEquals(2, len(list(tree)))
        self.assertEquals(['arg1', 'arg2'],
                          [n.text for n in list(tree)])
