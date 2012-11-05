#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, re
from fabric import api

import utils
from utils.platform import *


def callSystemStatus():
    tree = utils.callRpcCommand('systemstatus')
    res = {
        'cpu': [],
        'disk': [],
    }

    date = tree.find('datetime')
    ram = tree.find('ram')

    for cpu in tree.findall('cpu'):
        index = int(cpu.attrib['value'])

        while index >= len(res['cpu']):
            res['cpu'].append(None)

        res['cpu'][index] = item = {
            'used': float(cpu.attrib['used']),
            'core': [],
        }

        for core in cpu.findall('cores/core'):
            index = int(core.attrib['value'])

            while index >= len(item['core']):
                item['core'].append(None)

            item['core'][index] = float(core.attrib['used'])

    disks = []

    for disk in tree.findall('disks/disk'):
        disks.append({
                'name': disk.attrib['value'],
                'used': int(disk.attrib['used']),
                'total': int(disk.attrib['total']),
                'available': int(disk.attrib['available']),
        })

    res['disk'] = sorted(disks, key=lambda d: d['name'].lower())
    res['date'] = int(date.attrib['value'])
    res['ram'] = {
        'used': float(ram.attrib['used']),
        'total': float(ram.attrib['total']),
        'available': float(ram.attrib['available']),
    }

    return res


def getLinuxMemoryInfo():
    lines = api.run('free -m').split('\n')

    parts = re.split(r'\s+', lines[1])
    total = int(parts[1])

    parts = re.split(r'\s+', lines[2])
    used = int(parts[2])
    all_free = int(parts[3])

    return {
        'total': total,
        'available': all_free,
        'used': total - all_free,
    }


def getBsdMemoryInfo():
    lines = api.run('sysctl -a').split('\n')
    sysctl = {}

    for line in lines:
        if ': ' not in line:
            continue

        key, val = line.split(':', 1)
        sysctl[key] = val

    page_size = int(sysctl['hw.pagesize'])
    inactive = int(sysctl['vm.stats.vm.v_inactive_count']) * page_size
    cache = int(sysctl['vm.stats.vm.v_cache_count']) * page_size
    free = int(sysctl['vm.stats.vm.v_free_count']) * page_size
    total = int(sysctl['hw.realmem'])
    all_free = inactive + cache + free

    return {
        'total': total // (1024 * 1024),
        'available': all_free // (1024 * 1024),
        'used': (total - all_free) // (1024 * 1024),
    }


def getWindowsMemoryInfo():
    info = utils.callWmic('os get FreePhysicalMemory,TotalVisibleMemorySize')
    total = int(info[0]['TotalVisibleMemorySize'])
    free = int(info[0]['FreePhysicalMemory'])

    return {
        'total': total / 1024,
        'available': free / 1024,
        'used': (total - free) / 1024,
    }


def getMemoryInfo():
    if isWindows():
        return getWindowsMemoryInfo()
    elif isLinux():
        return getLinuxMemoryInfo()
    elif isBsd():
        return getBsdMemoryInfo()
    else:
        raise Exception('Unsupported platform')


def getWindowsCpuInfo():
    info = utils.callWmic('cpu list')
    cpus = {}

    for cpu_info in info:
        sock_id = cpu_info['SocketDesignation']

        if sock_id in cpus:
            cpu = cpus[sock_id]
        else:
            cpu = cpus[sock_id] = {
                'used': None,
                'core': []
            }

        cpu['core'].append(float(cpu_info['LoadPercentage']))

    for cpu in cpus.values():
        cpu['used'] = sum(cpu['core']) / len(cpu['core'])

    return cpus.values()


def getLinuxCpuInfo():
    info = []

    for line in api.run('cat /proc/cpuinfo').split('\n'):
        if not line:
            continue

        key, value = [l.strip() for l in line.split(':', 1)]

        if key == 'processor':
            current_cpu = {}
            info.append(current_cpu)

        current_cpu[key] = value

    cpus = {}

    for cpu_info in info:
        sock_id = int(cpu_info.get('physical id', len(cpus)))

        if sock_id in cpus:
            cpu = cpus[sock_id]
        else:
            cpu = cpus[sock_id] = {
                'used': None,
                'core': []
            }

        # could collect usage from /proc/stat, but it's too volatile
        # to test reliably
        cpu['core'].append(0.0)

    for cpu in cpus.values():
        cpu['used'] = sum(cpu['core']) / len(cpu['core'])

    return cpus.values()


def getBsdCpuInfo():
    info = []

    for line in api.run('top -P -u -I -d 2 -b').split('\n'):
        if line.startswith('CPU'):
            parts = line.split(',')
            idle = float(parts[-1].split('%')[0])
            used = 100 - idle

            # TODO good enough for VM, should parse
            # sysctl kern.sched.topology_spec
            info.append({
                    'value': len(info),
                    'used': used,
                    'core': [{
                            'value': 0,
                            'used': used,
            }]})

    # for single-CPU top outputs a single 'CPU: ...' line, for multi-CPU
    # it outputs both the aggregate line and a 'CPU X: ...' per-CPU line
    if len(info) > 1:
        del info[0]

    return info


def getCpuInfo():
    if isWindows():
        return getWindowsCpuInfo()
    elif isLinux():
        return getLinuxCpuInfo()
    elif isBsd():
        return getBsdCpuInfo()
    else:
        raise Exception('Unsupported platform')


def getWindowsDiskInfo():
    info = utils.callWmic('volume where DriveType=3 get Capacity,FreeSpace,Name')
    disks = []

    for disk in info:
        total = int(disk['Capacity']) / (1024 * 1024)
        free = int(disk['FreeSpace']) / (1024 * 1024)

        disks.append({
                'name': disk['Name'],
                'total': total,
                'used': total - free,
                'available': free,
        })

    return sorted(disks, key=lambda d: d['name'].lower())


def getLinuxDiskInfo():
    info = []

    for line in api.run('df -P --block-size=1048576').split('\n'):
        parts = re.split(r'\s+', line)

        if parts[0].startswith('/'):
            info.append({
                    'name': parts[5],
                    'total': int(parts[1]),
                    'used': int(parts[2]),
                    'available': int(parts[3]),
            })

    return sorted(info, key=lambda d: d['name'].lower())


def getBsdDiskInfo():
    info = []

    for line in api.run('df -k').split('\n'):
        parts = re.split(r'\s+', line)

        if parts[0].startswith('/'):
            info.append({
                    'name': parts[5],
                    'total': int(parts[1]) // 1024,
                    'used': int(parts[2]) // 1024,
                    'available': int(parts[3]) // 1024,
            })

    return sorted(info, key=lambda d: d['name'].lower())


def getDiskInfo():
    if isWindows():
        return getWindowsDiskInfo()
    elif isLinux():
        return getLinuxDiskInfo()
    elif isBsd():
        return getBsdDiskInfo()
    else:
        raise Exception('Unsupported platform')


class TestSystemStatus(unittest.TestCase):
    MEMORY_DELTA = 50 # MB
    DISK_DELTA = 20 # MB

    def testGet(self):
        memory = getMemoryInfo()
        cpus = getCpuInfo()
        disks = getDiskInfo()

        status = callSystemStatus()

        # test memory values
        self.assertEquals(memory['total'], status['ram']['total'])
        self.assertAlmostEqual(memory['available'], status['ram']['available'],
                               delta=self.MEMORY_DELTA)
        self.assertAlmostEqual(memory['used'], status['ram']['used'],
                               delta=self.MEMORY_DELTA)

        # cpu cores, we do not check the returned 'used' value because it's
        # too variable to test reliably
        self.assertEquals(len(cpus), len(status['cpu']))

        for i in range(len(status['cpu'])):
            got = status['cpu'][i]
            expected = cpus[i]

            self.assertEquals(len(expected['core']), len(got['core']))

        # test disk info
        for i in range(len(status['disk'])):
            got = status['disk'][i]
            expected = disks[i]

            self.assertEquals(expected['name'], got['name'])
            self.assertAlmostEqual(expected['used'], got['used'],
                                   delta=self.DISK_DELTA)
            self.assertAlmostEqual(expected['available'], got['available'],
                                   delta=self.DISK_DELTA)
            self.assertAlmostEqual(expected['total'], got['total'],
                                   delta=self.DISK_DELTA)
