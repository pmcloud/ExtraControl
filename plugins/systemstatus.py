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

import re
import sys
import time
from tools import *

from elementtree.ElementTree import Element, SubElement, tostring

TIME_FORMAT = '%Y%m%d%H%M%S'
DISK_MEGABYTE = 1024 * 1024


# parse the 'cpuX ...' lines from /proc/stat
def getLinuxCpuStat():
	result = []

	for line in file('/proc/stat'):
		parts = re.split(r'\s+', line.strip())

		if parts[0].startswith('cpu') and parts[0] != 'cpu':
			result.append(map(int, parts[1:]))

	return result


# computes per-core CPU usage
def getLinuxCpuUsage(interval):
	stat1 = getLinuxCpuStat()
	time.sleep(interval)
	stat2 = getLinuxCpuStat()

	result = []

	# compute tick difference between the two samples
	for i in range(len(stat1)):
		total = 0

		for j in range(len(stat1[i])):
			total += stat2[i][j] - stat1[i][j]

		idle = stat2[i][3] - stat1[i][3]

		result.append((total - idle) * 100.0 / total)

	return result


def getLinuxSystemStatus():
	result = {
		'datetime': time.localtime(),
		'cpus': [],
		'ram': {},
		'disks': [],
	}

	# CPU usage over a 1-second interval
	usage = getLinuxCpuUsage(1.0)

	# CPU number/cores
	cpuinfo_list = []

	for line in file('/proc/cpuinfo'):
		if line == '\n':
			continue

		key, value = [l.strip() for l in line.split(':', 1)]

		if key == 'processor':
			cpuinfo_list.append({'_core_use': usage[len(cpuinfo_list)]})

		cpuinfo_list[-1][key] = value

	# group CPUs by physical id, if available, otherwise assume single-core
	cpu_map = {}

	for cpu_info in cpuinfo_list:
		sock_id = int(cpu_info.get('physical id', len(cpu_map)))

		if sock_id in cpu_map:
			cpu = cpu_map[sock_id]
		else:
			cpu = cpu_map[sock_id] = {
				'value': str(len(cpu_map)),
				'used': None,
				'cores': []
			}
			result['cpus'].append(cpu)

		cpu['cores'].append({
			'value': str(len(cpu['cores'])),
			'used': '%.02f' % cpu_info['_core_use'],
		})

	for cpu in cpu_map.values():
		total = sum(float(c['used']) for c in cpu['cores'])
		cpu['used'] = '%.02f' % (total / len(cpu['cores']))

	# RAM
	mem_info = {}
	for line in file('/proc/meminfo').readlines():
		key, value = re.split(r':\s+', line)
		value = int(value.split(' ')[0])
		mem_info[key] = value

	total = mem_info['MemTotal']
	free = mem_info['MemFree']
	buffers = mem_info['Buffers']
	cache = mem_info['Cached']
	all_free = free + buffers + cache

	result['ram']['total'] = str(total // 1024)
	result['ram']['available'] = str(all_free // 1024)
	result['ram']['used'] = str((total - all_free) // 1024)

	# disks
	for line in subprocessCheckOutput(
		    ['df', '-P', '--block-size=%d' % DISK_MEGABYTE]).split('\n'):
		parts = re.split(r'\s+', line)

		if parts[0].startswith('/'):
			result['disks'].append({
				'value': parts[5],
				'total': parts[1],
				'used': parts[2],
				'available': parts[3],
			})

	return result


def callSysctl(*args):
	sysctl = {}
	for line in subprocessCheckOutput(['sysctl'] + list(args)).split('\n'):
		if ': ' not in line:
			continue

		key, val = line.split(':', 1)
		sysctl[key] = val

	return sysctl


# computes per-core CPU usage
def getBsdCpuUsage(interval):
	stat1 = callSysctl('hw.ncpu', 'kern.cp_times')
	time.sleep(interval)
	stat2 = callSysctl('hw.ncpu', 'kern.cp_times')

	result = []

	count = int(stat1['hw.ncpu'])

	parts1 = [int(v) for v in stat1['kern.cp_times'].strip().split(' ')]
	parts2 = [int(v) for v in stat2['kern.cp_times'].strip().split(' ')]

	# compute tick difference between the two samples
	for i in range(count):
		stat1 = parts1[i * 5:(i + 1) * 5]
		stat2 = parts2[i * 5:(i + 1) * 5]

		total = sum(stat2) - sum(stat1)
		idle = stat2[4] - stat1[4]

		result.append((total - idle) * 100.0 / total)

	return result


def getBsdSystemStatus():
	result = {
		'datetime': time.localtime(),
		'cpus': [],
		'ram': {},
		'disks': [],
	}

	# CPU usage over a 1-second interval
	usage = getBsdCpuUsage(5.0)

	# TODO good enough for VM, should parse
	# sysctl kern.sched.topology_spec
	# CPU usage
	for use in usage:
		used = '%.02f' % use

		result['cpus'].append({
			'value': str(len(result['cpus'])),
			'used': used,
			'cores': [{
				'value': '0',
				'used': used,
			}]})

	# RAM
	sysctl = callSysctl('-a')

	page_size = int(sysctl['hw.pagesize'])
	inactive = int(sysctl['vm.stats.vm.v_inactive_count']) * page_size
	cache = int(sysctl['vm.stats.vm.v_cache_count']) * page_size
	free = int(sysctl['vm.stats.vm.v_free_count']) * page_size
	total = int(sysctl['hw.realmem'])
	all_free = inactive + cache + free

	result['ram']['total'] = str(total // (1024 * 1024))
	result['ram']['available'] = str(all_free // (1024 * 1024))
	result['ram']['used'] = str((total - all_free) // (1024 * 1024))

	# disks
	for line in subprocessCheckOutput(['df', '-k']).split('\n'):
		parts = re.split(r'\s+', line)

		if parts[0].startswith('/') and not parts[0].startswith('/dev/md'):
			result['disks'].append({
				'value': parts[5],
				'total': str(int(parts[1]) * 1024 // DISK_MEGABYTE),
				'used': str(int(parts[2]) * 1024 // DISK_MEGABYTE),
				'available': str(int(parts[3]) * 1024 // DISK_MEGABYTE),
			})

	return result


def getWindowsSystemStatus():
	import wmi
	w = wmi.WMI()

	result = {
		'datetime': time.localtime(),
		'cpus': [],
		'ram': {},
		'disks': [],
	}

	# CPUs
	cpus = {}
	for i in w.Win32_Processor(["SocketDesignation", "LoadPercentage"]):
		if i.SocketDesignation not in cpus:
			cpus[i.SocketDesignation] = {
				'value': str(len(cpus)),
				'cores': [],
				}
			result['cpus'].append(cpus[i.SocketDesignation])

		core = len(cpus[i.SocketDesignation]['cores'])
		cpus[i.SocketDesignation]['cores'].append({
				'value': str(core),
				'used': str(i.LoadPercentage),
				})

	for cpu in result['cpus']:
		cpu['used'] = str(sum(int(c['used']) for c in cpu['cores']) / len(cpu['cores']))

	# RAM
	for i in w.Win32_OperatingSystem(["TotalVisibleMemorySize",
					  "FreePhysicalmemory"]):
		total = int(i.TotalVisibleMemorySize) // 1024
		free = int(i.FreePhysicalmemory) // 1024

		result['ram']['total'] = str(total)
		result['ram']['available'] = str(free)
		result['ram']['used'] = str(total - free)

	# disks
	for i in w.Win32_Volume(["Capacity", "FreeSpace", "Name"], DriveType=3):
		total = int(i.Capacity) // DISK_MEGABYTE
		free = int(i.FreeSpace) // DISK_MEGABYTE

		result['disks'].append({
				'value': i.Name,
				'total': str(total),
				'used': str(total - free),
				'available': str(free),
				})

	return result


def formatSystemStatus(info):
	top_node = Element('systemstatus')

	SubElement(top_node, 'datetime', {
			'value': time.strftime(TIME_FORMAT, info['datetime'])
			})

	for cpu in info['cpus']:
		cpu_node = SubElement(top_node, 'cpu', {
				'value': cpu['value'],
				'used': cpu['used'],
				});
		cores_node = SubElement(cpu_node, 'cores')

		for core in cpu['cores']:
			SubElement(cores_node, 'core', core)

	SubElement(top_node, 'ram', info['ram']);

	disks = SubElement(top_node, 'disks')
	for disk in info['disks']:
		SubElement(disks, 'disk', disk);

	return tostring(top_node)


def main():
	if sys.platform == 'win32':
		info = getWindowsSystemStatus()
	elif sys.platform == 'linux2':
		info = getLinuxSystemStatus()
	elif sys.platform.startswith('freebsd'):
		info = getBsdSystemStatus()
	else:
		raise Exception('Unsupported platform')

	print formatSystemStatus(info)
	return 0


if __name__ == "__main__":
	sys.exit(main())
