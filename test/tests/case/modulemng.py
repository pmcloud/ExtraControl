#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils, unittest

INTERNAL = ['modulemng']
PLUGINS =  ['updateModule']


def checkModuleFormat(self, module):
    self.assertHasChild(module, 'name')
    self.assertHasChild(module, 'type')
    self.assertIn(module.findtext('type'), ['Internal', 'Plugin', 'Custom'])
    self.assertHasChild(module, 'version')
    self.assertGreaterEqual(float(module.findtext('version')), 0)
    self.assertHasChild(module, 'upgradable')
    self.assertIn(module.findtext('upgradable'), ['true', 'false'])

    if module.findtext('name') in INTERNAL:
        self.assertEquals(module.findtext('type'), 'Internal')
        self.assertEquals(module.findtext('upgradable'), 'false')

    if module.findtext('name') in PLUGINS:
        self.assertEquals(module.findtext('type'), 'Plugin')


class TestModuleMngList(unittest.TestCase, utils.Assert):
    def testList(self):
        tree = utils.callRpcCommand("modulemng list")

        self.assertEquals('modules', tree.tag)

        for module in tree.findall('module'):
            self.assertHasChild(module, 'name')

        for builtin in INTERNAL + PLUGINS:
            self.assertIn(builtin,
                          [n.text for n in tree.findall('module/name')])

    def testDetailedList(self):
        tree = utils.callRpcCommand("modulemng list -d")

        self.assertEquals('modules', tree.tag)
        self.assertGreater(len(tree.findall('module')), 1)

        for module in tree.findall('module'):
            checkModuleFormat(self, module)


class TestModuleMngGet(unittest.TestCase, utils.Assert):
    def testGet(self):
        for builtin in INTERNAL + PLUGINS:
            tree = utils.callRpcCommand("modulemng get %s" % builtin)

            modules = [n.text for n in tree.findall('module/name')]

            self.assertEquals('modules', tree.tag)
            self.assertEquals(1, len(tree.findall('module')))

            module = tree.find('module')
            self.assertChildText(module, 'name', builtin)
            checkModuleFormat(self, module)

    def testGetInvalid(self):
        result = utils.callRpcCommandError("modulemng get thismoduledoesnotexist")


if __name__ == '__main__':
    utils.main()
