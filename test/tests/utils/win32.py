#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from fabric import api


def parseWmicXml(string):
    tree = ElementTree.fromstring(string)
    res = []

    for inst in tree.findall('RESULTS/CIM/INSTANCE'):
        item = {}
        res.append(item)

        for arr in inst.findall('PROPERTY.ARRAY'):
            item[arr.attrib['NAME']] = [v.text for v in arr.findall('VALUE.ARRAY/VALUE')]
        for val in inst.findall('PROPERTY'):
            item[val.attrib['NAME']] = val.findtext('VALUE')

    return res;


def callWmic(args):
    # the < /dev/null redirection is required on Windows 2003
    string = api.run('wmic %s /format:rawxml < /dev/null' % args)

    return parseWmicXml(string)
