#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest, os, files

from utils.platform import isWindows, shellExt


class TestModuleLifeCycle(unittest.TestCase, utils.Assert):
    def setUp(self):
        utils.deleteUserModule(shellExt("thisisatestmodule"))

    def testCustomModuleLifeCycle(self):
        name = shellExt("thisisatestmodule")

        tree = utils.callRpcCommand("upload usermodule %s" % name,
                                    files.executable(isWindows(), 'thisisatest'),
                                    no_xml=True)

        # check upload worked
        tree = utils.callRpcCommand("modulemng list")

        self.assertIn(name,
                      [n.text for n in tree.findall('module/name')])

        tree = utils.callRpcCommand("modulemng get %s" % name)

        module = tree.find('module')
        self.assertEquals('modules', tree.tag)
        self.assertChildText(module, 'name', name)
        self.assertChildText(module, 'version', '0')
        self.assertChildText(module, 'type', 'Custom')
        self.assertChildText(module, 'upgradable', 'true')

        # try calling the command
        tree = utils.callRpcCommand("exec script %s" % name)

        self.assertEquals('test', tree.tag)
        self.assertEquals('this is a test', tree.text)

        # remove module
        tree = utils.callRpcCommand("remove usermodule %s" % name, no_xml=True)

        # check module not in the list after remove
        tree = utils.callRpcCommand("modulemng list")

        self.assertNotIn(name,
                         [n.text for n in tree.findall('module/name')])
