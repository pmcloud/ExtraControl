#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, unittest, tempfile, sqlite3, struct, os

import utils, files
from utils.platform import *

from fabric import api
from xml.etree import ElementTree


def makeNetmask(bits):
    mask = ~((1 << (32 - bits)) - 1) & 0xffffffff
    parts = struct.unpack('4B', struct.pack('>L', mask))

    return '.'.join(map(str, parts))


def endianLiveConfig():
    addrs = api.run('ip addr')
    bridges = api.run("brctl show | tr -s '\\t' ' '")
    bridge_map = {}
    res = {}

    for line in bridges.split('\r\n'):
        if not line:
            continue
        parts = line.split(' ')

        if parts[0].startswith('br') and parts[-1].startswith('eth'):
            bridge_map[parts[0]] = parts[-1]

    for line in addrs.split('\n'):
        if not line:
            continue

        if not line.startswith(' '):
            iface = re.split(r':\s+', line)[1]
            item = None

            if iface != 'eth0' and not iface.startswith('br'):
                continue
            if iface != 'eth0':
                iface = bridge_map.get(iface)
                if not iface:
                    continue

            res[iface] = item = {
                    'MACAddress': None,
                    'Up': ',UP,' in line or ',UP>' in line,
                    'IPAddress': [],
                    'IPSubnet': []
                }
        elif item:
            type, address, rest = re.split(r'\s+', line.strip(), 2)

            if type == 'link/ether':
                item['MACAddress'] = '-'.join(address.upper().split(':'))
            elif type == 'inet':
                address, bits = address.split('/')

                item['IPAddress'].append(address)
                item['IPSubnet'].append(makeNetmask(int(bits)))

    for name, iface in res.items():
        if not iface['Up']:
            if ':' not in name:
                iface['IPAddress'] = iface['IPSubnet'] = []
            else:
                del res[name]
        del iface['Up']

    return res


def callLinuxIfconfig(args):
    string = api.run('LC_ALL=C ifconfig %s' % args)
    res = {}

    for line in string.split('\n'):
        if not line:
            continue
        parts = re.split(r'\s+', line)

        if parts[0]:
            if parts[3] == 'HWaddr' and not parts[0].startswith('br'):
                res[parts[0]] = item = {
                    'MACAddress': '-'.join(parts[4].upper().split(':')),
                    'Up': False,
                    'IPAddress': [],
                    'IPSubnet': []
                }
            else:
                item = None
        elif item and not parts[0] and parts[1] == 'inet' and \
                len(parts) > 4 and parts[2].startswith('addr') and \
                parts[4].startswith('Mask'):
            addr = parts[2].split(':')[1]
            mask = parts[4].split(':')[1]

            item['IPAddress'].append(addr)
            item['IPSubnet'].append(mask)
        elif item and not parts[0] and parts[1] == 'UP':
            item['Up'] = True

    for name, iface in res.items():
        if not iface['Up']:
            if ':' not in name:
                iface['IPAddress'] = iface['IPSubnet'] = []
            else:
                del res[name]
        del iface['Up']

    return res


def callBsdIfconfig(args):
    # use shell=True by default, except on pfSense where the shell is a menu
    string = api.run('ifconfig %s' % args, shell=not isPfSense())
    res = {}

    for line in string.split('\n'):
        if not line:
            continue

        if not line.startswith('\t'):
            parts = re.split(r'\s+', line.strip())

            iface = parts[0][:-1] # strip trailing colon
            flags = parts[1].split('<')[1].split('>')[0].split(',')
            item = None
        else:
            parts = re.split(r'\s+', line.strip())

            if parts[0] == 'ether':
                res[iface] = item = {
                    'MACAddress': '-'.join(parts[1].upper().split(':')),
                    'Up': 'UP' in flags,
                    'IPAddress': [],
                    'IPSubnet': []
                }
            elif parts[0] == 'inet' and item:
                addr = parts[1]
                maskbits = int(parts[3], 16)
                mask = '.'.join(map(str, struct.unpack('4B', struct.pack('>L', maskbits))))

                item['IPAddress'].append(addr)
                item['IPSubnet'].append(mask)

    for name, iface in res.items():
        if not iface['Up']:
            if ':' not in name:
                iface['IPAddress'] = iface['IPSubnet'] = []
            else:
                del res[name]
        del iface['Up']

    return res


def callIfconfig():
    if isLinux():
        return callLinuxIfconfig('-a')
    elif isBsd():
        return callBsdIfconfig('')


def parseInterfaces(args):
    string = api.run('cat %s' % args)
    res = {}

    for line in string.split('\n'):
        if not line:
            continue
        parts = re.split(r'\s+', line)

        if parts[0]:
            if parts[0] == 'iface' and \
                    parts[2] == 'inet' and \
                    parts[3] == 'static':
                if ':' in parts[1]:
                    # interface alias
                    item = res[parts[1].split(':')[0]]
                else:
                    # primary interface
                    item = {
                        'IPAddress': [],
                        'DefaultIPGateway': [],
                        'IPSubnet': []
                        }
                    res[parts[1]] = item
            else:
                item = None

        if not item:
            continue

        if parts[1] == 'address':
            item['IPAddress'].append(parts[2])
        if parts[1] == 'netmask':
            item['IPSubnet'].append(parts[2])
        if parts[1] == 'gateway':
            item['DefaultIPGateway'].append(parts[2])

    return res


def parseNetworkScripts(args):
    res = {}

    for path in api.run('ls -1 %s/ifcfg-*' % args).split('\n'):
        values = {}

        for line in api.run('cat %s' % path.strip()).split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
            parts = [f.strip() for f in line.split('=', 1)]
            if len(parts) != 2:
                continue

            values[parts[0]] = parts[1]

        if values.get('BOOTPROTO') not in ['static', 'none'] or \
                values.get('ONBOOT') != 'yes':
            continue

        dev = values.get('DEVICE')

        if not dev:
            continue

        if ':' in dev:
            item = res[dev.split(':')[0]]
        else:
            res[values.get('DEVICE')] = item = {
                'IPAddress': [],
                'DefaultIPGateway': [],
                'IPSubnet': []
            }

        if values.get('IPADDR'):
            item['IPAddress'].append(values.get('IPADDR'))
        if values.get('NETMASK'):
            item['IPSubnet'].append(values.get('NETMASK'))
        if values.get('GATEWAY'):
            item['DefaultIPGateway'].append(values.get('GATEWAY'))

    return res


def parseEndianConfig(uplink, ifaces):
    res = {}
    bridge_map = {}
    zone_map = {}
    gateway = None

    for line in api.run('grep eth %s/br*' % ifaces).split('\n'):
        line = line.strip()
        bridge, card = line.split(':', 1)
        bridge = os.path.basename(bridge)
        bridge_map[bridge] = card

    for line in api.run('cat %s/settings %s/settings' % (uplink, ifaces)).split('\n'):
        line = line.strip()

	if line.startswith('DEFAULT_GATEWAY='):
		gateway = line.split('=', 1)[1]

	for prefix in ['RED', 'GREEN', 'BLUE', 'ORANGE']:
            if not line.startswith(prefix):
                continue

            key, value = line.split('=', 1)
            key = key[len(prefix) + 1:]

            if not value:
                continue

            if prefix not in zone_map:
                zone_map[prefix] = {
                    'dev': None,
                    'ips': [],
                }

            if key == 'IPS':
                zone_map[prefix]['ips'] = value.split(',')
            elif key == 'DEV':
                zone_map[prefix]['dev'] = bridge_map.get(value, value)

    for zone, data in zone_map.items():
        if not data['dev'] or not data['ips']:
            continue

        dev = data['dev']
        if dev not in res:
            item = res[dev] = {
                'IPAddress': [],
                'DefaultIPGateway': [],
                'IPSubnet': []
            }
        else:
            item = res[dev]

        for i, ip in enumerate(data['ips']):
            address, bits = ip.split('/')

            item['IPAddress'].append(address)
            item['IPSubnet'].append(makeNetmask(int(bits)))

            if zone == 'RED' and i == 0:
                item['DefaultIPGateway'].append(gateway)
            else:
                item['DefaultIPGateway'].append(None)

    return res


def queryFreeNASDB(path):
    res = {}
    handle, local_db = tempfile.mkstemp()

    api.get(path, os.fdopen(handle, 'w'))
    conn = sqlite3.connect(local_db)
    os.unlink(local_db)

    gw = conn.execute('SELECT gc_ipv4gateway FROM network_globalconfiguration')
    gateway = gw.fetchone()[0]

    ifaces = conn.execute('''
SELECT id, int_interface, int_ipv4address, int_v4netmaskbit
	FROM network_interfaces
	WHERE int_dhcp = 0''')

    for iface_id, device, address, bits in ifaces:
        res[device] = item = {
            'IPAddress': [address],
            'DefaultIPGateway': [None],
            'IPSubnet': [makeNetmask(int(bits))]
        }

        if gateway:
            res[device]['DefaultIPGateway'][0] = gateway
            gateway = None

        aliases = conn.execute('''
SELECT alias_v4address, alias_v4netmaskbit
	FROM network_alias
	WHERE alias_interface_id = ?''', str(iface_id))

        for alias_address, alias_bits in aliases:
            item['IPAddress'].append(alias_address)
            item['IPSubnet'].append(makeNetmask(int(alias_bits)))
            item['DefaultIPGateway'].append(None)

    conn.close()

    return res


def parsePfSenseConfig(path):
    res = {}
    handle, local_xml = tempfile.mkstemp()

    api.get(path, os.fdopen(handle, 'w'))
    tree = ElementTree.parse(local_xml)
    os.unlink(local_xml)

    for iface in tree.find('interfaces'):
        if ElementTree.iselement(iface):
            if iface.find('disabled') is not None:
                continue

            device = iface.findtext('if')
            addr = iface.findtext('ipaddr')
            if addr == 'dhcp':
                continue

            res[device] = item = {
                'IPAddress': [addr],
                'DefaultIPGateway': [None],
                'IPSubnet': [makeNetmask(int(iface.findtext('subnet')))]
            }

            for gw in tree.find('gateways'):
                if gw.findtext('name') == iface.findtext('gateway'):
                    item['DefaultIPGateway'][0] = gw.findtext('gateway')
                    break

            for vip in tree.findall('virtualip/vip'):
                if vip.findtext('mode') == 'ipalias' and \
                        vip.findtext('type') == 'single' and \
                        vip.findtext('interface') == iface.tag:
                    item['IPAddress'].append(vip.findtext('subnet'))
                    item['IPSubnet'].append(makeNetmask(int(vip.findtext('subnet_bits'))))
                    item['DefaultIPGateway'].append(None)

    return res


def _parseInterfaceList(tree):
    res = []

    for adapter in tree.findall('NetworkAdapter'):
        item = {
            'MACAddress': None,
            'IPAddress': [],
            'DefaultIPGateway': [],
            'IPSubnet': []
        }
        res.append(item)

        item['MACAddress'] = adapter.findtext('Mac')

        for conf in adapter.findall('IpConfigurations/IpConfiguration'):
            item['IPAddress'].append(conf.findtext('Ip'))
            item['IPSubnet'].append(conf.findtext('SubnetMask'))
            if conf.findtext('Gateway'):
                item['DefaultIPGateway'].append(conf.findtext('Gateway'))
            else:
                item['DefaultIPGateway'].append(None)

    return res


def callNetconfList():
    return _parseInterfaceList(utils.callRpcCommand('netconf list'))


def callNetconfGet(mac):
    return _parseInterfaceList(utils.callRpcCommand('netconf get %s' % mac))


def sortInterfaces(ifaces):
    return sorted([a for a in ifaces if a['MACAddress']],
                 key=lambda a: a['MACAddress'])


def getWindowsConfig():
    macs = ['-'.join(i['MACAddress'].split(':'))
                for i in utils.callWmic('NIC where AdapterTypeID=0 get MACAddress')]
    nics = utils.callWmic('NICconfig get MACAddress,DNSServerSearchOrder,IPAddress,DefaultIPGateway,IPSubnet')
    for nic in nics:
        if nic['MACAddress']:
            nic['MACAddress'] = '-'.join(nic['MACAddress'].split(':'))

        # for Windows 2003
        if nic['IPAddress'] == ['0.0.0.0']:
            nic['IPAddress'] = []
        if nic['IPSubnet'] == ['0.0.0.0']:
            nic['IPSubnet'] = []

    lan = sortInterfaces(macs)

    return lan


def getUnixConfig():
    nics = callIfconfig()
    if isUbuntu():
        cfgs = parseInterfaces('/etc/network/interfaces')
    elif isCentOS():
        cfgs = parseNetworkScripts('/etc/sysconfig/network-scripts')
    elif isFreeNAS():
        cfgs = queryFreeNASDB('/data/freenas-v1.db')
    elif isPfSense():
        cfgs = parsePfSenseConfig('/conf/config.xml')
    elif isEndian():
        cfgs = parseEndianConfig('/var/efw/uplinks/main', '/var/efw/ethernet')
    else:
        raise Exception('Unknown Unix platform')

    res = []
    for dev, attrs in nics.items():
        res.append(attrs)
        if 'DefaultIPGateway' not in res[-1]:
            res[-1]['DefaultIPGateway'] = []
        res[-1].update(cfgs.get(dev, {}))

    lan = sortInterfaces(res)

    return lan


def getConfig():
    if isWindows():
        return getWindowsConfig()
    else:
        return getUnixConfig()


def getSafeInterfaces():
    connection_ip = api.env.host_string
    if '@' in connection_ip:
        connection_ip = connection_ip.split('@')[1]
    os_config = callNetconfList()
    os_config_safe = [c for c in os_config
                          if connection_ip not in c['IPAddress']]

    if os_config_safe == os_config:
        raise Exception("Can't determine the interface we are connecting from")

    return os_config_safe


class TestNetconf(unittest.TestCase, utils.Assert):
    def testList(self):
        os_config = getConfig()
        config = callNetconfList()

        # not returned by list
        for c in os_config:
            if 'DNSServerSearchOrder' in c:
                c.pop('DNSServerSearchOrder')

        self.assertEquals(os_config, config)

    def testGet(self):
        os_config = getConfig()

        # not returned by get
        for c in os_config:
            if 'DNSServerSearchOrder' in c:
                c.pop('DNSServerSearchOrder')

        for nic in os_config:
            config = callNetconfGet(nic['MACAddress'])

            self.assertEquals(1, len(config))
            self.assertEquals(nic, config[0])

    def testGetInvalidMac(self):
        utils.callRpcCommandError('netconf get FF-FF-CA-FE-BA-BE')


class TestNetconfChange(unittest.TestCase, utils.Assert):
    def _deconfigureInterfaces(self):
        need_check = False

        self.safe_interfaces = getSafeInterfaces()
        for nic in self.safe_interfaces:
            for ip in nic['IPAddress']:
                utils.callRpcCommand('netconf remove %s %s' %
                                     (nic['MACAddress'], ip), no_xml=True)
                need_check = True

        if not need_check:
            return

        self.safe_interfaces = getSafeInterfaces()
        for nic in self.safe_interfaces:
            if nic['IPAddress'] or nic['IPSubnet'] or \
                    nic['DefaultIPGateway']:
                raise Exception('Could not restore network interface to a clean configuration')

    def setUp(self):
        self._deconfigureInterfaces()

        if isFreeNAS() or isEndian():
            self.gw_set1 = self.gw_set2 = ''
            self.gw_check1 = self.gw_check2 = None
        else:
            self.gw_set1 = self.gw_check1 = '192.168.42.14'
            self.gw_set2 = self.gw_check2 = '192.168.8.1'

    def testAddRemoveSingle(self):
        mac1 = self.safe_interfaces[0]['MACAddress']
        mac2 = self.safe_interfaces[1]['MACAddress']

        tree = utils.callRpcCommand('netconf add %s %s %s %s' %
                                    (mac1, '192.168.42.1', '255.255.255.240',
                                     self.gw_set1), no_xml=True)

        tree = utils.callRpcCommand('netconf add %s %s %s' %
                                    (mac2, '192.168.8.8', '255.255.255.0'),
                                    no_xml=True)

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': ['192.168.42.1'],
                'IPSubnet': ['255.255.255.240'],
                'DefaultIPGateway': [self.gw_check1]
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': ['192.168.8.8'],
                'IPSubnet': ['255.255.255.0'],
                'DefaultIPGateway': [None]
            }
        ]

        self.assertEquals(expected, nics)

        tree = utils.callRpcCommand('netconf remove %s %s' %
                                    (mac1, '192.168.42.1'), no_xml=True)

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': [],
                'DefaultIPGateway': [],
                'IPSubnet': []
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': ['192.168.8.8'],
                'IPSubnet': ['255.255.255.0'],
                'DefaultIPGateway': [None]
            }
        ]

        self.assertEquals(expected, nics)

        if isLinux() or isBsd():
            if isEndian():
                live_config = sortInterfaces(endianLiveConfig().values())
            else:
                live_config = sortInterfaces(callIfconfig().values())
            os_config = callNetconfList()

            for iface in os_config:
                if 'DefaultIPGateway' in iface:
                    del iface['DefaultIPGateway']

            self.assertEquals(os_config, live_config)

    def testAddRemoveMultiple(self):
        mac1 = self.safe_interfaces[0]['MACAddress']

        tree = utils.callRpcCommand('netconf add %s %s %s %s' %
                                    (mac1, '192.168.42.1', '255.255.255.240',
                                     self.gw_set1), no_xml=True)

        tree = utils.callRpcCommand('netconf add %s %s %s' %
                                    (mac1, '192.168.8.8', '255.255.255.0'),
                                    no_xml=True)

        tree = utils.callRpcCommand('netconf add %s %s %s' %
                                    (mac1, '192.168.8.9', '255.255.255.0'),
                                    no_xml=True)

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': ['192.168.42.1', '192.168.8.8', '192.168.8.9'],
                'IPSubnet': ['255.255.255.240', '255.255.255.0', '255.255.255.0'],
                'DefaultIPGateway': [self.gw_check1, None, None]
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': [],
                'IPSubnet': [],
                'DefaultIPGateway': []
            }
        ]

        self.assertEquals(expected, nics)

        tree = utils.callRpcCommand('netconf remove %s %s' %
                                    (mac1, '192.168.42.1'), no_xml=True)
        tree = utils.callRpcCommand('netconf remove %s %s' %
                                    (mac1, '192.168.8.9'), no_xml=True)

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': ['192.168.8.8'],
                'IPSubnet': ['255.255.255.0'],
                'DefaultIPGateway': [self.gw_check1]
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': [],
                'DefaultIPGateway': [],
                'IPSubnet': []
            }
        ]

        self.assertEquals(expected, nics)

        if isLinux() or isBsd():
            if isEndian():
                live_config = sortInterfaces(endianLiveConfig().values())
            else:
                live_config = sortInterfaces(callIfconfig().values())
            os_config = callNetconfList()

            for iface in os_config:
                if 'DefaultIPGateway' in iface:
                    del iface['DefaultIPGateway']

            self.assertEquals(os_config, live_config)

    def testAddInvalidMac(self):
        result = utils.callRpcCommandError('netconf add FF-FF-CA-FE-BA-BE 192.168.42.1 255.255.255.240 192.168.42.14')

    def testRemoveInvalidMac(self):
        result = utils.callRpcCommandError('netconf remove FF-FF-CA-FE-BA-BE 0.0.0.0')

    def testAddDuplicateAddress(self):
        mac1 = self.safe_interfaces[0]['MACAddress']

        tree = utils.callRpcCommand('netconf add %s %s %s %s' %
                                    (mac1, '192.168.42.1', '255.255.255.240',
                                     self.gw_set1), no_xml=True)

        result = utils.callRpcCommandError('netconf add %s %s %s %s' %
                                           (mac1, '192.168.42.1', '255.255.255.240',
                                            self.gw_set1))

        tree = utils.callRpcCommand('netconf add %s %s %s %s' %
                                    (mac1, '192.168.8.8', '255.255.255.0',
                                     self.gw_set2), no_xml=True)

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': ['192.168.42.1', '192.168.8.8'],
                'IPSubnet': ['255.255.255.240', '255.255.255.0'],
                'DefaultIPGateway': [self.gw_check2, self.gw_check2]
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': [],
                'IPSubnet': [],
                'DefaultIPGateway': []
            }
        ]

    def testRemoveInvalidAddress(self):
        mac1 = self.safe_interfaces[0]['MACAddress']

        tree = utils.callRpcCommand('netconf add %s %s %s %s' %
                                    (mac1, '192.168.42.1', '255.255.255.240',
                                     self.gw_set1), no_xml=True)

        result = utils.callRpcCommandError('netconf remove %s %s' %
                                           (mac1, '192.168.42.2'))

        nics = getSafeInterfaces()
        expected = [
            {
                'MACAddress': nics[0]['MACAddress'],
                'IPAddress': ['192.168.42.1'],
                'IPSubnet': ['255.255.255.240'],
                'DefaultIPGateway': [self.gw_check1]
            },
            {
                'MACAddress': nics[1]['MACAddress'],
                'IPAddress': [],
                'DefaultIPGateway': [],
                'IPSubnet': []
            }
        ]
