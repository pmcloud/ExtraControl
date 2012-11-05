#!/usr/bin/env python
# encoding: utf-8
#
# ExtraControl - Aruba Cloud Computing ExtraControl
# Copyright (C) 2012 Aruba S.p.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import glob
import os
import re
import struct
import tempfile
import time
from tools import *
from elementtree.ElementTree import Element, SubElement, tostring

WIN32_ADAPTER_TYPES = [0]


def formatMac(address):
	return '-'.join(address.split(':'))


def textChild(parent, name, text):
	n = SubElement(parent, name)
	n.text = text
	return n


def checkMacaddress(value):
	try:
		parts = value.split('-')
		if len(parts) != 6:
			parts = value.split(':')
		if len(parts) != 6:
			raise Exception()

		for byte in [int(p, 16) for p in parts]:
			if byte < 0 or byte > 255:
				raise Exception()

		return '-'.join(p.upper() for p in parts)
	except:
		raise argparse.ArgumentTypeError("%s is not a valid MAC address" % value)


def checkIp(value):
	try:
		parts = [int(p) for p in value.split('.')]

		if len(parts) != 4:
			raise Exception()

		for byte in parts:
			if byte < 0 or byte > 255:
				raise Exception()

		return value
	except:
		raise argparse.ArgumentTypeError("%s is not a valid IP address" % value)


def checkNetmask(value):
	try:
		checkIp(value)

		parts = [int(p) for p in value.split('.')]
		mask, = struct.unpack('>L', struct.pack('4B', *parts))

		for i in range(2, 25):
			if mask == ~((1 << i) - 1) & 0xffffffff:
				return value

		raise Exception()
	except:
		raise argparse.ArgumentTypeError("%s is not a valid net mask" % value)


def formatIp(number):
	parts = struct.unpack('4B', struct.pack('>L', number))

	return '.'.join(map(str, parts))


def parseIp(ip):
	parts = [int(p) for p in ip.split('.')]

	return struct.unpack('>L', struct.pack('4B', *parts))[0]


def makeNetmask(bits):
	mask = ~((1 << (32 - bits)) - 1) & 0xffffffff

	return formatIp(mask)


def makeNetwork(ip, bits):
	mask = ~((1 << (32 - bits)) - 1) & 0xffffffff

	return formatIp(parseIp(ip) & mask)


def makeBroadcast(ip, bits):
	mask = ~((1 << (32 - bits)) - 1) & 0xffffffff

	return formatIp(parseIp(ip) & mask | ~mask & 0xffffffff)


def maskBits(netmask):
	parts = [int(p) for p in netmask.split('.')]
	mask, = struct.unpack('>L', struct.pack('4B', *parts))

	for i in range(2, 25):
		if mask == ~((1 << i) - 1) & 0xffffffff:
			return 32 - i

	raise Exception()


# Unix support code

def unixUpdateInterfaceConfiguration(iface):
	if isCentOS():
		centosUpdateNetworkCfg(iface)
	elif isDebian():
		debianUpdateInterfaces(iface)
	elif isEndian():
		endianUpdateNetworkCfg(iface)
	elif isFreeNAS():
		freenasUpdateNetworkCfg(iface)
	elif isPfSense():
		pfsenseUpdateNetworkCfg(iface)
	else:
		raise Exception('Unsupported Unix distribution')


def unixGetInterfaceList():
	ifaces = unixEnumerateInterfaces()
	if isCentOS():
		addresses = centosParseNetworkCfg()
	elif isDebian():
		addresses = debianParseInterfaces()
	elif isEndian():
		addresses = endianParseConfig()
	elif isPfSense():
		addresses = pfsenseGetNetworkCfg()
	elif isFreeNAS():
		addresses = freenasGetNetworkCfg()
	else:
		raise Exception('Unsupported Unix distribution')

	result = []

	for dev, mac in ifaces:
		iface = {
			'mac': mac,
			'adapter': dev,
			'configurations': []
		}
		result.append(iface)

		for config in addresses:
			if config['device'].startswith(dev + ':'):
				iface['configurations'].append(config)

	return result


def unixEnumerateInterfaces():
	if isLinux():
		if isEndian():
			return [i for i in linuxEnumerateInterfaces()
				    if not i[0].startswith('br')]
		else:
			return linuxEnumerateInterfaces()
	elif isBsd():
		return bsdEnumerateInterfaces()
	else:
		raise Exception('Unsupported Unix distribution')


# Linux support code

def linuxEnumerateInterfaces():
	output = subprocessCheckOutput(["ip", "link"])
	result = {}

	for line in output.split('\n'):
		if not line:
			continue

		if not line.startswith(' '):
			iface = re.split(r':\s+', line)[1]
		else:
			type, address, rest = re.split(r'\s+', line.strip(), 2)

			if type == 'link/ether':
				result[iface] = '-'.join(address.upper().split(':'))

	return sorted(result.items(), key=lambda kv: kv[1])


# Debian support code

def debianParseInterfaces():
	result = []
	dev = None

	for line in file(DEBIAN_INTERFACES_FILE):
		line = line.strip()
		parts = re.split(r'\s+', line)

		if parts[0] == 'iface':
			if parts[2] == 'inet' and parts[3] == 'static':
				dev = parts[1]
				if ':' not in dev:
					dev = dev + ':0'

				result.append({
					'device': dev,
					'ip': None,
					'netmask': None,
					'gateway': None,
				})
		elif parts[0] in ['mapping', 'auto', 'source'] or \
			    parts[0].startswith('allow-'):
			dev = None
		elif not dev:
			continue
		else:
			parts = re.split(r'\s+', line, 1)

			if parts[0].startswith('#') or len(parts) != 2:
				continue

			if parts[0] == 'address':
				result[-1]['ip'] = parts[1]
			elif parts[0] == 'netmask':
				result[-1]['netmask'] = parts[1]
			elif parts[0] == 'gateway':
				result[-1]['gateway'] = parts[1]

	return sorted(result, key=lambda r: r['device'])


def debianRemoveInterface(lines, name):
	result = []
	skip_current = False

	for line in file(DEBIAN_INTERFACES_FILE):
		parts = re.split(r'\s+', line.strip())

		if parts[0] == 'iface':
			skip_current = False
			if parts[2] == 'inet' and parts[3] == 'static':
				if parts[1] == name or parts[1].startswith(name + ':'):
					skip_current = True

			if not skip_current:
				result.append(line)
		elif parts[0] == 'auto':
			parts = [p for p in parts
				     if p != name and
				        not p.startswith(name + ':')]

			if len(parts) > 1:
				result.append(' '.join(parts) + '\n')
		elif parts[0] in ['mapping', 'auto', 'source'] or \
			    parts[0].startswith('allow-'):
			skip_current = False
			result.append(line)
		else:
			if not skip_current:
				result.append(line)
			elif parts[0] not in ['address', 'netmask', 'gateway']:
				result.append('#serclient-save:%s:%s' % (name, line))

	return result


def debianAddInterface(lines, iface, name):
	result = list(lines)

	prefix = '#serclient-save:%s:' % name
	restore = [l for l in result if l.startswith(prefix)]
	if restore and len(iface['configurations']):
		result = [l for l in result if not l.startswith(prefix)]

	for i, config in enumerate(iface['configurations']):
		if i == 0:
			dev = name
		else:
			dev = '%s:%d' % (name, i)

		result.append('auto %s\n' % dev)
		result.append('iface %s inet static\n' % dev)
		result.append('        address %s\n' % config['ip'])
		result.append('        netmask %s\n' % config['netmask'])
		if config['gateway']:
			result.append('        gateway %s\n' % config['gateway'])
		if i == 0 and restore:
			for l in restore:
				result.append(l[len(prefix):])

	return result


def debianUpdateInterfaces(iface):
	lines = file(DEBIAN_INTERFACES_FILE).readlines()
	lines = debianRemoveInterface(lines, iface['adapter'])
	lines = debianAddInterface(lines, iface, iface['adapter'])

	# using restart does not work if some interface/alias has been
	# removed: do a stop with the old configuration and start
	# with the new one
	subprocessCheckCall(['/etc/init.d/networking', 'stop'])

	fh = file(DEBIAN_INTERFACES_FILE, 'w')
	fh.write(''.join(lines))
	fh.close()

	if isUbuntu():
		subprocessCheckCall(['/usr/sbin/service', 'networking',
				     'start'])
	else:
		subprocessCheckCall(['/etc/init.d/networking', 'start'])


# CentOS support code

def centosParseNetworkCfg():
	result = []

	for path in glob.glob(CENTOS_NETWORK_SCRIPTS + '/ifcfg-*'):
		dev = os.path.basename(path).split('-', 1)[1]
		if ':' not in dev:
			dev = dev + ':0'

		result.append({
			'device': dev,
			'ip': None,
			'netmask': None,
			'gateway': None,
		})

		for line in file(path):
			line = line.strip()

			if line.startswith('#'):
				continue

			key, value = line.split('=', 1)

			if key == 'IPADDR':
				result[-1]['ip'] = value
			elif key == 'NETMASK':
				result[-1]['netmask'] = value
			elif key == 'GATEWAY':
				result[-1]['gateway'] = value

	return sorted(result, key=lambda r: r['device'])


def centosUpdateNetworkCfg(iface):
	files = glob.glob(CENTOS_NETWORK_SCRIPTS + '/ifcfg-%s*' % iface['adapter'])
	new_files = {}

	for i, cfg in enumerate(iface['configurations']):
		if not cfg['ip']:
			continue
		if i == 0:
			alias = iface['adapter']
		else:
			alias = '%s:%s' % (iface['adapter'], i)

		lines = []
		lines.append('TYPE=Ethernet')
		lines.append('BOOTPROTO=none')
		lines.append('ONBOOT=yes')
		lines.append('DEVICE=%s' % alias)
		lines.append('IPADDR=%s' % cfg['ip'])
		lines.append('NETMASK=%s' % cfg['netmask'])

		if cfg['gateway']:
			lines.append('GATEWAY=%s' % cfg['gateway'])

		lines.append('')

		new_files[CENTOS_NETWORK_SCRIPTS + '/ifcfg-%s' % alias] = \
		    '\n'.join(lines)

	for name, text in new_files.items():
		fh = file(name, 'w')
		fh.write(text)
		fh.close()

	for f in files:
		if f not in new_files:
			os.unlink(f)

	subprocessCheckCall(['/etc/init.d/network', 'reload'])

	# force the inteface down if there is no associated IP
	if not iface['configurations']:
		subprocessCheckCall(['/sbin/ifconfig', iface['adapter'],
				     'down'])


# Endian support code

def endianParseBridgeMap():
	bridge_map = {}

	for path in glob.glob(ENDIAN_BRIDGE_CONFIG + '/br*'):
		card = open(path, 'rt').readline().strip()
		if card:
			bridge_map[os.path.basename(path)] = card

	# add a static mapping for missing bridges/cards
	for card in ['eth1', 'eth2']:
		if card in bridge_map.values():
			continue

		for bridge in ['br0', 'br1', 'br2']:
			if bridge not in bridge_map:
				bridge_map[bridge] = card
				break

	return bridge_map


# used when an interface does not have a configured ip but is still
# associated with a zone (has been associated in the past)
def endianFindZone(iface, bridge_map):
	# assume eth0 is always an external interface
	if iface == 'eth0':
		return 'RED'

	bridge = bridge_map.get(iface)
	if not bridge:
		return None

	for line in open(ENDIAN_BRIDGE_CONFIG + '/settings', 'rt'):
		line = line.strip()

		if '=' not in line:
			continue
		key, value = line.split('=', 1)

		if key.endswith('_DEV') and value == bridge:
			zone = key.split('_', 1)[0]
			if zone in ['GREEN', 'ORANGE', 'BLUE']:
				return zone

	return None


def endianParseConfig():
	result = []
	bridge_map = endianParseBridgeMap()
	zone_map = {}
	gateway = None

	for path in [ENDIAN_BRIDGE_CONFIG + '/settings',
		     ENDIAN_UPLINK_CONFIG + '/settings']:
		for line in open(path, 'rt'):
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

		for i, ip in enumerate(data['ips']):
			address, bits = ip.split('/')

			result.append({
				'device': '%s:%d' % (dev, i),
				'ip': address,
				'zone': zone,
				'netmask': makeNetmask(int(bits)),
				'gateway': None,
			})

			if zone == 'RED' and i == 0:
				result[-1]['gateway'] = gateway

	return sorted(result, key=lambda r: r['device'])


ENDIAN_DATA = [
	('cidr', '%(bits)s'),
	('gateway', '%(gateway)s'),
	('interface', '%(device)s'),
	('ip_address', '%(address)s'),
	('ips', '%(iplist)s'),
	('network_number', '%(network)s'),
]

# CONFIG_TYPE:
# blue:   4, 5, 6, 7
# orange: 1, 3, 5, 7
# green:  ?
# modem:  0, 1, 4, 5
ENDIAN_SETTINGS = [
	('%(zone)s_ADDRESS', '%(address)s'),
	('%(zone)s_BROADCAST', '%(broadcast)s'),
	('%(zone)s_CIDR', '%(bits)s'),
	('%(zone)s_IPS', '%(iplist)s'),
	('%(zone)s_NETADDRESS', '%(network)s'),
	('%(zone)s_NETMASK', '%(netmask)s'),
]

ENDIAN_SETTINGS_RED = ENDIAN_SETTINGS + [('DEFAULT_GATEWAY', '%(gateway)s')]


def updateEndianFile(path, template, values):
	formatted = {}
	lines = []

	for key_patt, value_patt in template:
		key = key_patt % values
		value = value_patt % values

		formatted[key] = value

	for line in file(path, 'rt'):
		if '=' in line:
			key, value = line.split('=', 1)
			key = key.strip()

			if key in formatted:
				lines.append('%s=%s\n' % (key, formatted[key]))
			else:
				lines.append(line)
		else:
			lines.append(line)

	fh = open(path + '.new', 'wt')
	for line in lines:
		fh.write(line)
	fh.close()

	# copy owner from old to new file
	attrs = os.stat(path)
	os.chown(path + '.new', attrs.st_uid, attrs.st_gid)
	os.rename(path + '.new', path)


def endianUpdateNetworkCfg(iface):
	bridge_map = dict((v, k) for k, v in endianParseBridgeMap().items())
	zone = None

	# - if the adapter is associated to a zone, keep the association
	#   (both for active and inactive associations)
	# - assume eth0 is always in the RED zone
	#   (uplink/external card)
	# - try to map eth1 to br0 and eth2 to br1
	# - map the card to the first available bridge

	for config in iface['configurations']:
		if 'zone' in config:
			zone = config['zone']
			break

	if not zone:
		zone = endianFindZone(iface['adapter'], bridge_map)
	if not zone:
		# should never happen
		raise Exception('Unknown interface zone')
	if zone != 'RED' and iface['adapter'] not in bridge_map:
		raise Exception('Unable to determine interface for bridge %s' %
				iface['adapter'])

	if iface['configurations']:
		first = iface['configurations'][0]
		bits = maskBits(first['netmask'])
		iplist = ','.join('%s/%d' % (c['ip'], maskBits(c['netmask']))
				      for c in iface['configurations'])

		value_map = {
			'zone': zone,
			'bits': bits,
			'netmask': first['netmask'],
			'gateway': first['gateway'] or '',
			'device': iface['adapter'],
			'address': first['ip'],
			'iplist': iplist,
			'network': makeNetwork(first['ip'], bits),
			'broadcast': makeBroadcast(first['ip'], bits),
		}
	else:
		value_map = {
			'zone': zone,
			'bits': '',
			'netmask': '',
			'gateway': '',
			'device': '',
			'address': '',
			'iplist': '',
			'network': '',
			'broadcast': '',
		}

	if zone == 'RED':
		updateEndianFile(ENDIAN_UPLINK_CONFIG + '/data',
				 ENDIAN_DATA, value_map)
		updateEndianFile(ENDIAN_UPLINK_CONFIG + '/settings',
				 ENDIAN_SETTINGS_RED, value_map)
	else:
		updateEndianFile(ENDIAN_BRIDGE_CONFIG + '/settings',
				 ENDIAN_SETTINGS, value_map)

		bridge = bridge_map[iface['adapter']]
		fh = open(ENDIAN_BRIDGE_CONFIG + '/' + bridge, 'wt')
		fh.write(iface['adapter'])
		fh.close()

	start = time.time()

	# the interface reload runs asynchronously, and there does not
	# seem to be any way to check when it completes (other than
	# log parsing) so just wait for jobengine status to settle
	subprocessCheckCall(['/etc/rc.d/rc.netwizard.reload'])

	while time.time() - start < 60:
		mod1 = os.stat('/var/run/jobsengine.status')
		time.sleep(5)
		mod2 = os.stat('/var/run/jobsengine.status')

		if mod1.st_mtime != mod2.st_mtime:
			break


# FreeBSD support code

def bsdEnumerateInterfaces():
	output = subprocessCheckOutput(["ifconfig"])
	result = {}

	for line in output.split('\n'):
		if not line:
			continue

		if not line.startswith('\t'):
			iface = re.split(r':\s+', line)[0]
		else:
			parts = re.split(r'\s+', line.strip(), 2)

			if parts[0] == 'ether':
				result[iface] = '-'.join(parts[1].upper().split(':'))

	return sorted(result.items(), key=lambda kv: kv[1])


# FreeNAS support code

def freenasGetNetworkCfg():
	import sqlite3

	result = []
	conn = sqlite3.connect(FREENAS_DB)

	gw = conn.cursor()
	gw.execute('SELECT gc_ipv4gateway FROM network_globalconfiguration')
	gateway = gw.fetchone()[0]

	ifaces = conn.cursor()
	aliases = conn.cursor()

	ifaces.execute('''
SELECT id, int_interface, int_ipv4address, int_v4netmaskbit
	FROM network_interfaces
	WHERE int_dhcp = 0
	ORDER BY int_interface''')

	for iface_id, device, address, bits in ifaces:
		result.append({
			'device': '%s:0' % device,
			'ip': address,
			'netmask': makeNetmask(int(bits)),
			'gateway': gateway,
		})
		gateway = None

		aliases.execute('''
SELECT alias_v4address, alias_v4netmaskbit
	FROM network_alias
	WHERE alias_interface_id = ?''', str(iface_id))

		count = 1
		for alias_address, alias_bits in aliases:
			result.append({
				'device': '%s:%d' % (device, count),
				'ip': alias_address,
				'netmask': makeNetmask(int(alias_bits)),
				'gateway': None,
			})
			count += 1

	conn.close()

	return result


def freenasUpdateNetworkCfg(iface):
	import sqlite3

	conn = sqlite3.connect(FREENAS_DB)

	# delete aliases and configuration
	conn.execute('''
DELETE FROM network_alias
	WHERE alias_interface_id IN (SELECT id
					FROM network_interfaces
					WHERE int_interface = ?)
''', [iface['adapter']])
	conn.execute('''
DELETE FROM network_interfaces
	WHERE int_interface = ?
''', [iface['adapter']])

	# add new configuration
	for i, cfg in enumerate(iface['configurations']):
		if i == 0:
			cursor = conn.cursor()
			cursor.execute('''
INSERT INTO network_interfaces
	(int_dhcp, int_ipv6auto, int_ipv6address, int_options,
	 int_ipv4address, int_v4netmaskbit, int_name, int_interface)
	VALUES (0, 0, '', '', ?, ?, ?, ?)
''', [cfg['ip'], maskBits(cfg['netmask']), iface['adapter'], iface['adapter']])
			iface_id = cursor.lastrowid
		else:
			conn.execute('''
INSERT INTO network_alias
	(alias_interface_id, alias_v4address, alias_v4netmaskbit)
	VALUES (?, ?, ?)
''', [iface_id, cfg['ip'], maskBits(cfg['netmask'])])

	conn.commit()

	# they exit with non-zero value even when they succeed
	subprocess.call(['/etc/rc.d/netif', 'restart'])
	subprocess.call(['/etc/rc.d/routing', 'restart'])


# pfSense support code

# dumps network config as a list of <key>=<value> lines, associating
# gateways with the main interfaces and listing aliases in a format
# similar to "normal" addresses
PFSENSE_READ = """
<?php
require_once('functions.inc');
require_once('globals.inc');
require_once('config.inc');

$config = parse_config();

foreach ($config['interfaces'] as $name => $iface) {
	echo "name=$name\n";
	echo "device={$iface['if']}:0\n";
	echo "ip={$iface['ipaddr']}\n";
	echo "subnet={$iface['subnet']}\n";
	if (array_key_exists('enable', $iface)) {
		echo "enabled=True\n";
	} else {
		echo "enabled=False\n";
	}

	if ($config['gateways']) {
		foreach ($config['gateways'] as $iface_gw) {
			foreach ($iface_gw as $gw) {
				if ($gw['interface'] == $name) {
					echo "gateway={$gw['gateway']}\n";
				}
			}
		}
	}

	$count = 1;

	if ($config['virtualip']) {
		foreach ($config['virtualip'] as $iface_vip) {
			foreach ($iface_vip as $vip) {
				if ($vip['interface'] == $name && $vip['type'] == 'single') {
					echo "name=$name\n";
					echo "device={$iface['if']}:$count\n";
					echo "ip={$vip['subnet']}\n";
					echo "subnet={$vip['subnet_bits']}\n";
				}
			}
		}
	}

	echo "\n";
}
?>
"""

PFSENSE_WRITE = """
<?php
require_once('functions.inc');
require_once('globals.inc');
require_once('config.inc');
require_once('interfaces.inc');
require_once('vpn.inc');
require_once('captiveportal.inc');

$name = %s;
$iface = %s;
$ips = array(%s);
$masks = array(%s);
$gateway = %s;

$config = parse_config();

# remove old configuration
function filter_vip($it) {
	global $name;

	return ($it['interface'] != $name ||
		$it['mode'] != 'ipalias' || $it['type'] != 'single') &&
		$it['interface'] != '';
}

function filter_gateway($it) {
	global $name;

	return $it['interface'] != $name && $it['interface'] != '';
}

interface_bring_down($name, true);

unset($config['interfaces'][$name]);
$config['virtualip']['vip'] =
	array_filter($config['virtualip']['vip'], filter_vip);
$config['gateways']['gateway_item'] =
	array_filter($config['gateways']['gateway_item'], filter_gateway);

# add new configuration, if any
for ($i = 0; $i < count($ips); ++$i) {
	if ($i == 0) {
		$config['interfaces'][$name] = array(
			'name'     => strtoupper($name),
			'if'       => $iface,
			'ipaddr'   => $ips[$i],
			'subnet'   => $masks[$i],
			'spoofmac' => '',
			'enable'   => true,
			'gateway'  => $gateway ? strtoupper($name) . 'GW' : '',
		);
	} else {
		if (!$config['virtualip']['vip']) {
			$config['virtualip']['vip'] = array();
		}

		array_push($config['virtualip']['vip'],
			   array(
				'mode' => 'ipalias',
				'interface'   => $name,
				'descr'       => '',
				'type'        => 'single',
				'subnet_bits' => $masks[$i],
				'subnet'      => $ips[$i],
			   ));
	}
}

if ($gateway) {
	if (!$config['gateways']['gateway_item']) {
		$config['gateways']['gateway_item'] = array();
	}

	array_push($config['gateways']['gateway_item'],
		   array(
			'interface' => $name,
			'gateway'   => $gateway,
			'name'      => strtoupper($name) . 'GW',
			'weight'    => '',
			'interval'  => '',
			'descr'     => '',
		   ));
}

# mark interface disabled if there are no IP assigned
if (!count($ips)) {
	$config['interfaces'][$name] = array(
		'name'     => strtoupper($name),
		'if'       => $iface,
		'disabled' => true,
	);
}

write_config($config);

# apply new configuration
# from /usr/local/www/interfaces.php, if ($_POST['apply'])
clear_subsystem_dirty('interfaces');

if (count($ips)) {
	interface_reconfigure($name, true);
}

services_snmpd_configure();
setup_gateways_monitor();
clear_subsystem_dirty('staticroutes');
filter_configure();
?>
"""

def runPHP(code):
	script = tempfile.NamedTemporaryFile()
	if isinstance(code, list):
		script.write('\n'.join(code))
	else:
		script.write(code)
	script.flush()

	return subprocessCheckOutput(['php', '-q', script.name])


def pfsenseGetNetworkCfg():
	result = []
	config = runPHP(PFSENSE_READ)

	for line in config.split('\n'):
		if not line:
			continue

		key, value = line.split('=', 1)

		if key == 'name':
			result.append({'gateway': None})
		elif key == 'subnet' and value:
			result[-1]['netmask'] = makeNetmask(int(value))
		else:
			result[-1][key] = value

	return [r for r in result if r['ip'] and r['ip'] != 'dhcp']


def pfsenseUpdateNetworkCfg(iface):
	def quote(v):
		if v is not None:
			return "'%s'" % v
		else:
			return "''"

	def quotelist(l):
		return ', '.join(quote(v) for v in l)

	if iface['adapter'] == 'em0':
		name = 'wan'
	elif iface['adapter'] == 'em1':
		name = 'lan'
	else:
		index = int(iface['adapter'][2:])
		name = 'opt%d' % (index - 1)

	if iface['configurations']:
		gateway = iface['configurations'][0]['gateway']
	else:
		gateway = None

	script = PFSENSE_WRITE % (
		quote(name),
		quote(iface['adapter']),
		quotelist([c['ip'] for c in iface['configurations']]),
		quotelist([maskBits(c['netmask']) for c in iface['configurations']]),
		quote(gateway),
	)

	runPHP(script)


# Win32 support code

# Returns a list of NetworkAdapter objects whose type is contained
# in the array defined above
#
# the list is sorted by MAC address
def win32EnumerateInterfaces():
	import wmi

	w = wmi.WMI()
	res = []

	for i in w.Win32_NetworkAdapter():
		if i.AdapterTypeID in WIN32_ADAPTER_TYPES:
			res.append(i)

			res.sort(key=lambda o: o.MACAddress)

	return res


def win32GetInterface(mac):
	for interface in win32EnumerateInterfaces():
		if formatMac(interface.MACAddress) == mac:
			return interface

	return None


def win32AddressList(maybe_addresses):
	if maybe_addresses is None:
		return []

	return [a for a in maybe_addresses if a != '0.0.0.0']


def win32GetInterfaceInfo(interface):
	output = subprocessCheckOutput(
		["netsh", "interface", "ip", "dump"])

	config = {
		'mac': formatMac(interface.MACAddress),
		'configurations': [],
	}
	gateway = None

	def splitNetshLine(line, prefix):
		line = line[len(prefix) + 1:].strip() + ' '
		result = {}

		while line:
			eq_index = line.find('=')

			if eq_index == -1:
				raise Exception("Netsh output parsing error: %s" % line)

			key = line[:eq_index]
			if line[eq_index + 1] == '"':
				quote_index = line.find('"', eq_index + 2)
				value = line[eq_index + 2:quote_index]
				line = line[quote_index + 2:]
			else:
				space_index = line.find(' ', eq_index + 1)
				value = line[eq_index + 1:space_index]
				line = line[space_index + 1:]

			result[key] = value

		return result

	winver = sys.getwindowsversion()

	if winver[0] == 5: # 2003
		for line in output.split("\r\n"):
			if line.startswith("set address") or line.startswith("add address"):
				params = splitNetshLine(line, "add address")
				if params["name"] != interface.NetConnectionID:
					continue

				if 'addr' in params:
					ipcfg = {
						'ip': params['addr'],
						'netmask': params['mask'],
					}

					config['configurations'].append(ipcfg)
				elif 'gateway' in params:
					gateway = params['gateway']
	else:
		for line in output.split("\r\n"):
			if line.startswith("add route"):
				params = splitNetshLine(line, "add route")
				if params["interface"] != interface.NetConnectionID:
					continue

				gateway = params["nexthop"]
			elif line.startswith("add address"):
				params = splitNetshLine(line, "add address")
				if params["name"] != interface.NetConnectionID:
					continue

				ipcfg = {
					'ip': params['address'],
					'netmask': params['mask'],
				}

				config['configurations'].append(ipcfg)

	if gateway and config['configurations']:
		config['configurations'][0]['gateway'] = gateway

	return config


def win32AddIpAddress(interface, ip, netmask, gateway):
	# TODO error message/output
	subprocessCheckCall(
		["netsh", "interface", "ip", "add", "address",
		 interface.NetConnectionID, ip, netmask],
		stdout=file('NUL'))
	if gateway:
		subprocessCheckCall(
			["netsh", "interface", "ip", "add", "address",
			 interface.NetConnectionID, "gateway=%s" % gateway,
			 "gwmetric=1"],
			stdout=file('NUL'))


def win32RemoveIpAddress(interface, ip, remove_gateway):
	args = [interface.NetConnectionID, ip]
	if remove_gateway:
		args += ["gateway=all"]

	# TODO error message/output
	subprocessCheckCall(
		["netsh", "interface", "ip", "delete", "address"] + args,
		stdout=file('NUL'))


def win32EnableDHCP(interface):
	# TODO error message/output
	subprocessCheckCall(
		["netsh", "interface", "ip", "set", "address",
		 interface.NetConnectionID, "source=dhcp"],
		stdout=file('NUL'))


# utility functions

def getInterfaceInfo(macaddress):
	if isWindows():
		interface = win32GetInterface(macaddress)
		if interface:
			return win32GetInterfaceInfo(interface)
	elif isLinux() or isBsd():
		result = unixGetInterfaceList()

		for r in result:
			if r['mac'] == macaddress:
				return r
	else:
		raise Exception('Unsupported operating system')

	return None


def formatNetworkAdapterConfig(parent_node, adapter):
	adapter_node = SubElement(parent_node, 'NetworkAdapter')
	textChild(adapter_node, 'Mac', adapter['mac'])
	configs_node = SubElement(adapter_node, 'IpConfigurations')

	for config in adapter['configurations']:
		config_node = SubElement(configs_node, 'IpConfiguration')
		textChild(config_node, 'Ip', config['ip'])
		textChild(config_node, 'SubnetMask', config['netmask'])
		if 'gateway' in config:
			textChild(config_node, 'Gateway', config['gateway'])


# command handlers

def listCommand(args):
	if isWindows():
		result = [win32GetInterfaceInfo(i) for i in
			      win32EnumerateInterfaces()]
	elif isLinux() or isBsd():
		result = unixGetInterfaceList()
	else:
		raise Exception('Unsupported operating system')

	top_node = Element('NetConfigurations')

	for adapter in result:
		formatNetworkAdapterConfig(top_node, adapter)

	print tostring(top_node)
	return 0


def getCommand(args):
	result = getInterfaceInfo(args.macaddress)

	if result is None:
		print 'adapter not found'
		return 3

	top_node = Element('NetConfigurations')
	formatNetworkAdapterConfig(top_node, result)

	print tostring(top_node)
	return 0


def addCommand(args):
	# check duplicate address and gateway
	info = getInterfaceInfo(args.macaddress)

	if info is None:
		print 'adapter not found'
		return 3

	if [i for i in info['configurations'] if i['ip'] == args.ip]:
		print "duplicate IP address"
		return 5

	if args.gateway and [i for i in info['configurations'] if i.get('gateway') == args.gateway]:
		print "duplicate gateway address"
		return 6

	if isWindows():
		interface = win32GetInterface(args.macaddress)

		if interface:
			win32AddIpAddress(interface, args.ip,
					  args.netmask, args.gateway)
	elif isLinux() or isBsd():
		ifaces = unixGetInterfaceList()
		cfg = {
			'ip': args.ip,
			'netmask': args.netmask,
			'gateway': args.gateway
		}

		for i, iface in enumerate(ifaces):
			if iface['mac'] == args.macaddress:
				iface['configurations'].append(cfg)
				unixUpdateInterfaceConfiguration(iface)
				break
	else:
		raise Exception('Unsupported operating system')

	return 0


def removeCommand(args):
	# check address is configured
	info = getInterfaceInfo(args.macaddress)

	if info is None:
		print 'adapter not found'
		return 3

	if not [i for i in info['configurations'] if i['ip'] == args.ip]:
		print "address not configured"
		return 4

	last_address = len(info['configurations']) == 1

	if isWindows():
		winver = sys.getwindowsversion()
		interface = win32GetInterface(args.macaddress)

		if interface:
			# for last address on WIndows 2003, re-enable DHCP
			if winver[0] == 5 and last_address:
				win32EnableDHCP(interface)
			else:
				win32RemoveIpAddress(interface, args.ip, last_address)
	elif isLinux() or isBsd():
		ifaces = unixGetInterfaceList()

		for i, iface in enumerate(ifaces):
			if iface['mac'] == args.macaddress:
				new_cfgs = []

				for c in iface['configurations']:
					if c['ip'] != args.ip:
						new_cfgs.append(c)
					else:
						removed = c

				iface['configurations'] = new_cfgs
				if len(new_cfgs) and removed['gateway']:
					new_cfgs[0]['gateway'] = removed['gateway']

				unixUpdateInterfaceConfiguration(iface)
				break
	else:
		raise Exception('Unsupported operating system')

	return 0


def main():
	parser = argparse.ArgumentParser(add_help=False, prog='netconf')
	subparsers = parser.add_subparsers(dest="sub_command")

	helpparser = subparsers.add_parser('help')

	listparser = subparsers.add_parser("list")
	listparser.set_defaults(handler=listCommand)

	getparser = subparsers.add_parser("get")
	getparser.add_argument("macaddress", type=checkMacaddress)
	getparser.set_defaults(handler=getCommand)

	addparser = subparsers.add_parser("add")
	addparser.add_argument("macaddress", type=checkMacaddress)
	addparser.add_argument("ip", type=checkIp)
	addparser.add_argument("netmask", type=checkNetmask)
	addparser.add_argument("gateway", nargs='?', type=checkIp)
	addparser.set_defaults(handler=addCommand)

	removeparser = subparsers.add_parser("remove")
	removeparser.add_argument("macaddress", type=checkMacaddress)
	removeparser.add_argument("ip", type=checkIp)
	removeparser.set_defaults(handler=removeCommand)

	args = parser.parse_args()

	if args.sub_command == "help":
		parser.print_help()
		return 0

	return args.handler(args)


if __name__ == "__main__":
	sys.exit(main())
