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
import os
import platform

from tools import *
from elementtree.ElementTree import Element, SubElement, tostring


NAMES = {
	'Openfiler ESA': 'Openfiler',
	'Endian Firewall Community release': 'Endian',
}

def windowsInfo():
	winver = sys.getwindowsversion()

	if winver[0] == 6:
		version = '2008'
	elif winver[0] == 5:
		version = '2003'
	else:
		version = 'unknown'

	return {
		'name': 'Windows',
		'version': version,
		'details': platform.machine(),
	}


def linuxInfo():
	if sys.version_info[0] > 2 or sys.version_info[1] > 5:
		distribution, version, _ = platform.linux_distribution()
	else:
		distribution, version, _ = platform.dist()

		# platform.dist() on Python 2.4 misdiagnoses CentOS as a
		# generic redhat, try to compensate using lsb_release
		if os.path.exists('/usr/bin/lsb_release'):
			for line in subprocessCheckOutput(['/usr/bin/lsb_release', '-i', '-r']).split('\n'):
				if not line:
					continue

				key, value = [p.strip() for p in line.split(':', 1)]
				if key == 'Distributor ID':
					distribution = value
				elif key == 'Release':
					version = value

	if not distribution and not version:
		for path in ['/etc/distro-release', '/etc/release']:
			if os.path.exists(path):
				line = open(path, 'rt').readline().strip()
				distribution, version = line.rsplit(' ', 1)
				distribution = NAMES.get(distribution, distribution)

	return {
		'name': distribution,
		'version': version,
		'details': platform.machine(),
	}


def bsdInfo():
	if os.path.exists('/etc/version.freenas'):
		distribution = 'FreeNAS'
		parts = file('/etc/version.freenas').readline().split('-')
		version = parts[1]
	elif os.path.exists('/etc/platform'):
		distribution = file('/etc/platform').readline().strip()
		parts = file('/etc/version').readline().split('-')
		version = parts[0]
	else:
		distribution = os.uname()[0]
		version = os.uname()[3]

	return {
		'name': distribution,
		'version': version,
		'details': platform.machine(),
	}


def main():
	top_node = Element('osinfo')

	if sys.platform == 'win32':
		info = windowsInfo()
	elif sys.platform == 'linux2':
		info = linuxInfo()
	elif sys.platform.startswith('freebsd'):
		info = bsdInfo()

	SubElement(top_node, 'name').text = info['name']
	SubElement(top_node, 'version').text = info['version']
	SubElement(top_node, 'details').text = info['details']
	
	print tostring(top_node)
	return 0

if __name__ == "__main__":
	sys.exit(main())
