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
from tools import *
import os

def main():
	parser = argparse.ArgumentParser(add_help=True, prog='updateModule')
	parser.add_argument("module", help="module")
	parser.add_argument("version", help="new module version")
	parser.add_argument("new_module", help="path to new module binary", nargs='+')
	parser.add_argument("--force", help="force update (ignore the version)", action='store_const', default=False, const=True)
	args = parser.parse_args()
	
	m = moduleFromNameAndType(args.module, MODULE_PLUGINS)
	
	if m == None:
		print "Module not found or not of type plugin"
		return 1
		
	if m.isUpgradable() == False:
		print "Module is not upgradable"
		return 1
		
	v = float(args.version)
	if args.force == False:
		if v <= m.version():
			print "Current module version is same or newer"
			return 1
			
	new_module = args.new_module[0]

	if new_module.lower().startswith('http'):
		def logTransfer(count, block, size):
			pass
		print "Downloading:", new_module
		try:
			filename, headers = urllib.urlretrieve(new_module, reporthook=logTransfer)
			new_module = filename
		except IOError, msg:
			print "Error: %s" % msg
			return 1
		except:
			print "File too short"
			return 1
		print '\nDownloaded:', filename
		print 'Headers:\n', headers
	else:
		if not os.path.exists(new_module):
			print "Update file not found"
			return 1
		
	update_dir = getPluginsUpdateDirectory()
		
	beforeFileUpdate()

	try:
		os.mkdir(update_dir)
	except OSError, msg:
		pass
	update_path = os.path.join(update_dir, m.nameWithExtension())
	try:
		os.remove(update_path)
	except OSError:
		pass
	copyModule(new_module, update_path)
	open(update_path + EXTENSION_VERSION, "w").write("%r" % v)
	if m.isBlocking():
		open(update_path + EXTENSION_BLOCKING, "w").write("")

	afterFileUpdate()
		
	print 'Done'
	return 0
	
	
if __name__ == "__main__":
	sys.exit(main())
