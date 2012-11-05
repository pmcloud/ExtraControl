#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib, base64

from xml.etree import ElementTree
from fabric import api

HOSTNAME_MAP = {
    'DC1_ARU-1265_Win2008Hv_1354': 'ddhvc01s02.dcloud.local',
}

FREENAS_RW = 'test -f /etc/version.freenas && mount -uw / || true'
FREENAS_RO = 'test -f /etc/version.freenas && mount -ur / || true'


def _callRpcCommand(command, body, base64_body):
    proxy = xmlrpclib.ServerProxy(api.env.aruba_configuration.xmlrpc_url)

    if body is not None:
        base64_body = base64.b64encode(body)

    if api.env.aruba_host.vm_name not in HOSTNAME_MAP:
        hostname = proxy.GetVmHost(api.env.aruba_host.vm_name)

        HOSTNAME_MAP[api.env.aruba_host.vm_name] = hostname


    host = HOSTNAME_MAP[api.env.aruba_host.vm_name]

    if base64_body is not None:
        result = proxy.Send(api.env.aruba_host.vm_name, "",
                            HOSTNAME_MAP[api.env.aruba_host.vm_name],
                            'COMMAND', command, base64_body)
    else:
        result = proxy.Send(api.env.aruba_host.vm_name, "",
                            HOSTNAME_MAP[api.env.aruba_host.vm_name],
                            'COMMAND', command, "")

    # remove trailing ExceptionCode if present
    exc_code = result.rfind('ExceptionCode=', -30, -1)
    if exc_code != -1:
        result = result[:exc_code]

    if api.env.aruba_xmlrpc_verbose:
        print 'XML-RPC result: ', result

    try:
        return ElementTree.fromstring(result)
    except ElementTree.ParseError:
        raise Exception('Could not parse result string as XML: "%s"' % result)


# call a command, expecting a success response; returns the content
# of <outputString> as an ElementTree.Element; command must be
# valid XML text, data (if present) will be Base64-encoded
def callRpcCommand(command, body=None, base64_body=None, no_xml=False):
    tree = _callRpcCommand(command, body, base64_body)

    if tree.findtext('responseType') != 'Success':
        raise Exception("Command failure, reponse type '%s' message '%s'" % (
                        tree.findtext('responseType'),
                        tree.findtext('resultMessage')))

    output = tree.findtext('outputString')

    if no_xml:
        return output

    try:
        return ElementTree.fromstring(output)
    except ElementTree.ParseError:
        raise Exception('Could not parse output string as XML: "%s"' % output)


# call a command, expecting a failure response; returns the content
# of <resultMessage> as a plain string
def callRpcCommandError(command, body=None, base64_body=None):
    tree = _callRpcCommand(command, body, base64_body)

    if tree.findtext('responseType') != 'Error':
        raise Exception("Expected failure, got '%s' instead" %
                        tree.findtext('responseType'))

    return tree.findtext('resultMessage')


def checkModuleAndVersion(module, version=None):
    tree = callRpcCommand("modulemng get %s" % module)

    if tree.findtext('module/name') != module:
        raise Exception('Module %s not found' % module)

    if version is not None:
        modversion = float(tree.findtext('module/version'))

        if modversion < version:
            raise Exception('Module %s version %f, required %f' %
                            (module, modversion, version))

    return True


def uploadUserModule(module, content):
    deleteUserModule(module)
    callRpcCommand("upload usermodule %s" % module, content, no_xml=True)
    checkModuleAndVersion(module)


def deleteUserModule(module):
    lst = callRpcCommand("modulemng list")

    if module in [n.text for n in lst.findall('module/name')]:
        callRpcCommand("remove usermodule %s" % module, no_xml=True)


def savePristineState():
    if not api.env.aruba_host.install_path:
        raise Exception('Install path not set')

    attrs = {
        'ro':   FREENAS_RO,
        'rw':   FREENAS_RW,
        'path': api.env.aruba_host.install_path,
    }

    api.run("test -f '%(path)s/plugins.tar' || ((%(rw)s) && tar -C '%(path)s' -c -f '%(path)s/plugins.tar' plugins && (%(ro)s))" % attrs)


def restorePristineState():
    if not api.env.aruba_host.install_path:
        raise Exception('Install path not set')

    attrs = {
        'ro':   FREENAS_RO,
        'rw':   FREENAS_RW,
        'path': api.env.aruba_host.install_path,
    }

    api.run("test -f '%(path)s/plugins.tar' && ((%(rw)s) && tar -C '%(path)s' -x -f '%(path)s/plugins.tar' && rm '%(path)s/plugins.tar' && (%(ro)s))" % attrs)
    api.run("(%(rw)s) && rm -f %(path)s/update/* %(path)s/usermodules/* %(path)s/plugins/*.version && (%(ro)s)" % attrs)


class FatalError(Exception):
    pass


class Assert(object):
    def assertHasChild(self, node, child):
        self.assertIsNotNone(node.find(child),
                             "node %s does not have a %s child" %
                             (node.tag, child))

    def assertChildText(self, node, child, text):
        self.assertHasChild(node, child)
        self.assertEquals(text, node.find(child).text,
                          "%s/%s text '%s' != '%s'" %
                          (node.tag, child, node.find(child).text, text))
