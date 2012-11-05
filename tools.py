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

__doc__ = """A set of functions and names to simplify plugins development"""
import os
import glob
import shutil
import sys
import subprocess
from elementtree.ElementTree import Element, SubElement
from ConfigParser import *
import logging
import serial
import argparse
from logging.handlers import *
import time
import urllib

EXTENSION_BLOCKING = ".blocking" 	# this extension will match for plugins that are blocking ones
EXTENSION_VERSION = ".version"		# this extension will match for plugins that have a version

MODULE_VALID_EXTENSIONS = ("", ".exe", ".py", ".sh", ".bat")

MODULE_INTERNALS = "Internal"
MODULE_PLUGINS = "Plugin"
MODULE_CUSTOMS = "Custom"

# Path to where the service is stored. TODO: when the script is frozen this may be wrong.
if getattr(sys, 'frozen', False):
	_ROOT = os.path.dirname(sys.executable)
	_SERVICE_BIN = sys.executable
	IS_FROZEN = True
else:
	_ROOT = os.path.realpath(os.path.dirname(__file__))
	_SERVICE_BIN = os.path.join(_ROOT, 'service.py')
	IS_FROZEN = False

SERVICE_VERSION_FILE = os.path.join(_ROOT, "serclient.version")
IS_WINDOWS = sys.platform.startswith('win')

# The plugins root path must be loaded from the INI file (so its the same for external process too)
_PLUGINS_ROOT = None

# Name of the file where the restart packet GUID is stored
_SERVICE_RESTART_FILE = "serclient.restart"

# Name of the file where the updateSoftware log is stored
_UPDATESOFTWARE_LOG_FILE = "updateSoftware.log"

def _getConfigurationDefaults():
	"""
	Return default values for arguments.
	
	Values depending on the operative system must be set here.
	"""
	return {
		'LOG': {
			'level': str(logging.DEBUG),
			'file': 'stdout',
			'syslog_address': '',
		}, 
		'SERIAL': {
			'port': '0', #default port for PySerial
			'baudrate':'57600',
			'bytesize': str(serial.EIGHTBITS),
			'parity': str(serial.PARITY_NONE),
			'stopbits': str(serial.STOPBITS_ONE),
		},
		'PLUGINS': {
			'command_timeout': '40',
			'root': _ROOT,
		},
		'TIMEOUT': {
			'updateSoftware': '90',
		}
	}
	
def getConfigurationDictFromArgparse(args):
	"""
	Return a configuration dictionary created by reading the argparse arguments
	"""
	assert isinstance(args, argparse.Namespace), "argparse.Namespace expected"
	v = {
		'LOG': {
			'file': args.log,
			'level': str(args.log_level),
			'syslog_address': args.syslog_address,
		},
		'PLUGINS': {
			'command_timeout': str(args.command_timeout),
			'root': _ROOT, # do not allow root changes from the command line, external process can not access it!
		},
		'SERIAL': {
			'port': str(args.serial_port),
			'baudrate': str(args.baudrate),
			'bytesize': str(args.bytesize),
			'parity': str(args.parity),
			'stopbits': str(args.stopbits),
		},
		# single timeouts can no be specified using the comand line so we set hard-code them 
		# TODO: or we could get them from the default ini function
		'TIMEOUT': {
			'updateSoftware': '90',
		}
	}
	return v

def getConfigurationFromINI():
	"""
	Return a dictionary of section with the configuration read from the ini file merged with the defaults passed.
	Various ini location are tried.
	"""
	defaults = _getConfigurationDefaults()
	ini = ConfigParser()
	x = os.path.join(_ROOT, 'serclient.ini')
	v = ini.read([x, '/opt/serclient/serclient.ini'])
	c = dict(ini._sections)
	for k, v in defaults.items():
		if k in c.keys():
			v.update(c[k])
	return defaults
	
def configureLogging(config):
	"""
	Configure logging capabilities
	"""
	logging.basicConfig()
	logger = logging.getLogger('serclient')
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	c = config['LOG']
	level = int(c['level'])
	logger.setLevel(level)
	# todo add handlers to root logger
	if c['file'] == 'stdout':
		root = logging.getLogger('')
		root.setLevel(level=level)
		logger.debug("logging to stdout")
	elif c['file'] != '':
		rf = RotatingFileHandler(filename=c['file'], encoding='utf-8', backupCount=50)
		rf.setFormatter(formatter)
		logger.addHandler(rf)
		logger.info('\n---------\nLog closed on %s.\n---------\n' % time.asctime())
		if getRestartGUID(remove=False) == None: rf.doRollover()
	address = c['syslog_address']
	if address != '':
		if '/' not in address: 
			# split address:port
			s = address.split(":")
			if len(s) == 1: 
				address = (s[0], SYSLOG_UDP_PORT)
			else: 
				address = (s[0], int(s[1]))
		s = SysLogHandler(address=address)
		s.setFormatter(formatter)
		logger.addHandler(s)
		logger.debug("logging to syslog: %s" % repr(address))
	logger.info('\n---------\nLog started on %s.\n---------\n' % time.asctime())
	logger.info('Configuration arguments: %r' % config)
	return logger

def getRoot():
	"""
	Return the plugins root directory loading it from the INI file or using its default value
	"""
	global _PLUGINS_ROOT
	if _PLUGINS_ROOT != None: return _PLUGINS_ROOT
	d = getConfigurationFromINI()
	_PLUGINS_ROOT = d['PLUGINS']['root']
	return _PLUGINS_ROOT
	
def getPluginsUpdateDirectory():
	"""
	Return the path to the directory where plugin updates are stored (by default is the same plugin folder)
	"""
	return os.path.join(getRoot(), "plugins")
	
def getCustomDirectory():
	"""
	Return the path to the directory where custom modules are stored
	"""
	return os.path.join(getRoot(), "usermodules")

# There are 3 types of modules, each one with its properties and installation dirs
MODULE_TYPES = {
	# Name, Upgradable, (Paths..)
	MODULE_INTERNALS: (MODULE_INTERNALS, False, (getRoot()+"/internals",)),
	MODULE_PLUGINS: (MODULE_PLUGINS, True, (getRoot()+"/plugins",)), 
	MODULE_CUSTOMS: (MODULE_CUSTOMS, True, (getCustomDirectory(),)),
}

def getServiceVersion():
	"""
	Return the service version.
	"""
	try:
		version = float(open(SERVICE_VERSION_FILE).readline().split("\n")[0])
	except (IOError, ValueError):
		version = 0
	return version
	
def guidFromInt(val):
	"""
	Return a generated guid from an int ie val=1 -> '00000000000000000000000000000001'
	For debug use only.
	"""
	assert type(val) == int, "need an int"
	return "%032d" % val

class Module(object):
	"""
	This class describe a module and its properties.
	"""
	
	# We assign the file path to our service internal names, so we can avoid to refer to them with the extension
	ALIAS_NAME = {
		# Service management
		'restart.py': 'restart',
		# Module management
		'modulemng.py': 'modulemng',
		'updateModule.py': 'updateModule',
		'updateSoftware.py': 'updateSoftware',
		# Custom scripts
		'remove.py': 'remove',
		'upload.py': 'upload',
		'exec.py': 'exec',
		# System scripts
		'netconf.py': 'netconf',
		'osinfo.py': 'osinfo',
		'systemstatus.py': 'systemstatus',
	}
	
	def __init__(self, type, full_path, version, upgradable, blocking, alias=None):
		self._type = type
		self._full_path = full_path
		self._name_and_extension = os.path.basename(self._full_path)
		self._version = version
		self._upgradable = upgradable
		self._blocking = blocking
		if alias == None:
			self._alias = Module.ALIAS_NAME.get(self._name_and_extension, self._name_and_extension)
		else:
			self._alias = alias
		
	def __repr__(self):
		return "Module(%r, %r, %r, %r, %r, alias=%r)" % (self._type, self._full_path, self._version, self._upgradable, self._blocking, self.aliasName())
		
	def aliasName(self):
		"""
		Returns the name of the module as it would be if specified on the COMMAND Packet
		This way we can map our dev scripts name to the name itself. 
		If the mapping is not found the name is just the executable name like for custom plugins.
		"""
		return self._alias
		
	def nameWithExtension(self):
		"""
		Returns the name of the module plus the extension needed to be execute (ie .exe, .sh)
		"""
		return self._name_and_extension
		
	def type(self):
		"""
		Returns the type of module: INTERNAL, PLUGIN, CUSTOM
		"""
		return self._type
		
	def fullPath(self):
		"""
		Returns the full path on disk to the module executable
		"""
		return self._full_path
		
	def version(self):
		"""
		Returns the module version as int
		"""
		return self._version
		
	def isUpgradable(self):
		"""
		Returns True if the module can be upgraded
		"""
		return self._upgradable
		
	def isBlocking(self):
		"""
		Returns True if the module requires no other process to be executed at the same time
		"""
		return self._blocking
		
	def toElementTree(self, details):
		"""
		Return an Element node with the XML rappresentation of this module
		"""
		c = Element('module')
		n = SubElement(c, 'name')
		n.text = self._alias
		if details:
			# version
			v = SubElement(c, 'version')
			v.text = str(self._version)
			# type
			t = SubElement(c, 'type')
			t.text = self._type
			# lock
			u = SubElement(c, 'upgradable')
			u.text = repr(self._upgradable).lower()
		return c
		
	def isAnUpgrade(self):
		"""
		Return True if the module is an upgrade of a system module
		"""
		if self._type != MODULE_PLUGINS: return False
		ud = getPluginsUpdateDirectory()
		return os.path.commonprefix([self._full_path, ud]) == ud
		
	def isPythonScript(self):
		"""
		Return True if the module is a python script
		"""
		return self._name_and_extension.endswith(".py")
		

def moduleFromPathAndType(path, type):
	"""
	Return a Module from the path and type requested.
	
	Type is not verified, so its up to you to specify the matching ones. 
	If you don't know the type call `browseModules` or `searchModule`
	"""
	assert type in [MODULE_INTERNALS, MODULE_PLUGINS, MODULE_CUSTOMS], "Type unknow"
	m = None
	_, ext = os.path.splitext(path)
	if os.path.isfile(path) and ext in MODULE_VALID_EXTENSIONS:
		full_path = path
		_, upgradable, _ = MODULE_TYPES[type]
		blocking = os.path.exists(path+EXTENSION_BLOCKING)
		try:
			version = float(open(path+EXTENSION_VERSION).readline().split("\n")[0])
		except (IOError, ValueError):
			version = 0
		m = Module(type, full_path, version, upgradable, blocking)
	return m
	
def moduleFromNameAndType(name, type):
	"""
	Return a Module if a module with that name (or alias) and type exists.
	"""
	assert type in [MODULE_INTERNALS, MODULE_PLUGINS, MODULE_CUSTOMS], "Type unknow"
	m = None
	type, upgradable, dirs = MODULE_TYPES[type]
	# inverse alias
	ia = {}
	for k, v in Module.ALIAS_NAME.items(): ia[v] = k
	name = ia.get(name, name)
	for dir in dirs:
		file = os.path.join(dir, name)
		found = moduleFromPathAndType(file, type)
		if found:
			# the first module found hides any other module (internal then plugins then customs)
			m = found
			break
	return m

def browseModules(types=[MODULE_INTERNALS, MODULE_PLUGINS, MODULE_CUSTOMS]):
	"""
	Return a dictionary with key the Modules type and value a dictionary of Modules with their name as key (so they can be searched).
	Includes hard-coded modules (ie restart)
	"""
	type_groups = [MODULE_TYPES[x] for x in types]
	modules = {MODULE_INTERNALS:{}, MODULE_PLUGINS:{}, MODULE_CUSTOMS:{}}
	
	# add restart
	for type, upgradable, dirs in type_groups:
		for dir in dirs:
			for ext in MODULE_VALID_EXTENSIONS:
				s = "%s/*%s" % (dir, ext)
				for file in glob.glob(s):
					found = moduleFromPathAndType(file, type)
					if found:
						modules[type][found.aliasName()] = found
	return modules

def searchModule(name):
	"""
	Return a Module with name, searching for it on the standard module dirs.
	"""
	all_modules = browseModules()
	for type, modules in all_modules.items():
		if name in modules.keys():
			return modules[name]
	return None
	
def runExternal(cmd_line, shell=False, close_handles=False):
	"""
	Run the external process with properly configured PIPE to work with frozen service
	"""
	e = dict(os.environ)
	e['PYTHONPATH'] = '.'
	if close_handles == False:
		process = subprocess.Popen(cmd_line,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT, 
			stdin=subprocess.PIPE,
			shell=shell,
			env=e)
	else:
		process = subprocess.Popen(cmd_line,
			stdout=None,
			stderr=None, 
			stdin=None,
			close_fds=True,
			shell=shell,
			env=e)
	return process

def copyModule(source, target):
	shutil.copy(source, target)
	os.chmod(target, 0755)

# copied from Python 2.7 subprocess.py
def subprocessCheckOutput(*popenargs, **kwargs):
	if hasattr(subprocess, "check_output"):
		return subprocess.check_output(*popenargs, **kwargs)

	if 'stdout' in kwargs:
		raise ValueError('stdout argument not allowed, it will be overridden.')
	process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
	output, unused_err = process.communicate()
	retcode = process.poll()
	if retcode:
		cmd = kwargs.get("args")
		if cmd is None:
			cmd = popenargs[0]
		raise subprocess.CalledProcessError(retcode, cmd, output=output)
	return output

def subprocessCheckCall(*popenargs, **kwargs):
	if hasattr(subprocess, "check_call"):
		return subprocess.check_call(*popenargs, **kwargs)

	retcode = subprocess.call(*popenargs, **kwargs)
	if retcode:
		cmd = kwargs.get("args")
		if cmd is None:
			cmd = popenargs[0]
		raise subprocess.CalledProcessError(retcode, cmd)
	return 0

def beforeFileUpdate():
	if sys.platform.startswith('freebsd') and os.path.exists('/etc/version.freenas'):
		subprocessCheckCall(['mount', '-uw', '/'])

def afterFileUpdate():
	if sys.platform.startswith('freebsd') and os.path.exists('/etc/version.freenas'):
		subprocessCheckCall(['mount', '-ur', '/'])

def daemonize(pid_file):
	# first fork
	try:
		pid = os.fork()
		if pid > 0:
			# exit original process
			sys.exit(0)
	except OSError, e:
		sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
		sys.exit(1)

	# decouple from parent environment
	os.chdir("/")
	os.setsid()
	os.umask(0)

	# second fork
	try:
		pid = os.fork()
		if pid > 0:
			# exit from second parent
			sys.exit(0)
	except OSError, e:
		sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
		sys.exit(1)

	# close standard file descriptors
	null = os.open("/dev/null", os.O_RDWR)
	os.dup2(null, 0)
	os.dup2(null, 1)
	os.dup2(null, 2)

	# write pidfile
	if pid_file:
		file(pid_file,'w+').write("%s\n" % os.getpid())

DEBIAN_INTERFACES_FILE = '/etc/network/interfaces'
CENTOS_NETWORK_SCRIPTS = '/etc/sysconfig/network-scripts'
ENDIAN_BRIDGE_CONFIG = '/var/efw/ethernet'
ENDIAN_UPLINK_CONFIG = '/var/efw/uplinks/main'
FREENAS_DB = '/data/freenas-v1.db'

def isWindows(): return sys.platform == 'win32'
def isLinux(): return sys.platform == 'linux2'
def isBsd(): return sys.platform.startswith('freebsd')
def isCentOS(): return isLinux() and os.path.isdir(CENTOS_NETWORK_SCRIPTS)
def isOpenFiler(): return isLinux() and os.path.isdir('/etc/conary')
def isDebian(): return isLinux() and os.path.isfile(DEBIAN_INTERFACES_FILE)
def isUbuntu(): return isLinux() and os.path.isdir('/etc/init')
def isEndian(): return isLinux() and os.path.isdir('/etc/endian')
def isPfSense(): return isBsd() and os.path.isfile('/conf/config.xml')
def isFreeNAS(): return isBsd() and os.path.isfile(FREENAS_DB)

def getRestartGUID(remove=False):
	"""
	Return the GUID for a restart packet or None if we don't have one.
	
	@param remove: True if we want to remove it (should be set if an appropiate action to send a packet is taken)
	"""
	try:
		f = os.path.join(getRoot(), _SERVICE_RESTART_FILE)
		guid = open(f).read()
		if remove:
			os.remove(f)
		return guid
	except IOError:
		pass
	return None
	
def getUpdateSoftwareLOGFileName():
	f = os.path.join(getRoot(), _UPDATESOFTWARE_LOG_FILE)
	return f
	
def getUpdateSoftwareLOG(remove=False):
	"""
	Return the LOG of latest updateSoftware command (if present)
	
	@param remove: True if we want to remove it (should be set if an appropiate action to send a packet is taken)
	"""
	try:
		f = getUpdateSoftwareLOGFileName()
		log = open(f).read()
		if remove:
			os.remove(f)
		return log
	except IOError:
		pass
	return ""
	
def saveRestartGUID(guid):
	"""
	Save the GUID for later use; this method "survive" the process restart command.
	"""
	beforeFileUpdate()
	open(os.path.join(getRoot(), _SERVICE_RESTART_FILE), 'w').write(guid)
	afterFileUpdate()
	
def setPythonBin(path):
	"""
	Set the "fake" python bin to call to execute external python scripts
	"""
	global _SERVICE_BIN
	_SERVICE_BIN = path
	
def getPythonBin():
	return _SERVICE_BIN

if __name__ == "__main__":
	# some test code
	print browseModules()
	print searchModule("restart")
	print searchModule("not found")
	print moduleFromNameAndType("modulemng", "Internal")
	print moduleFromPathAndType('/media/sf_aruba/plugins/popen', "Plugin")
	print getPluginsUpdateDirectory()
	print searchModule("sleep.py")
	print getConfigurationFromINI()