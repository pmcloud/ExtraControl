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
import subprocess
import urllib
import logging

# Enable writing on some file systems
beforeFileUpdate()

# Set logging to stdout and to a file so we can read it from the service and send it back with the response
logging.basicConfig()
root = logging.getLogger()
root.setLevel(logging.DEBUG)
logger = logging.getLogger('updateSoftware')
fh = logging.FileHandler(filename=getUpdateSoftwareLOGFileName(), encoding='utf-8', mode='w')
root.addHandler(fh)

def main():
	parser = argparse.ArgumentParser(add_help=True, prog='updateSoftware')
	parser.add_argument("version", help="new software version")
	parser.add_argument("installer", help="path to installer binary", nargs='+')
	parser.add_argument("--force", help="force update (ignore the version)", action='store_const', default=False, const=True)
	args = parser.parse_args()
		
	v= float(args.version)
	if args.force == False:
		if v <= getServiceVersion():
			logger.fatal("Current service version is same or newer")
			return 1
		
	installer = args.installer[0]

	if installer.lower().startswith('http'):
		def logTransfer(count, block, size):
			pass
		logger.info("Downloading: %r" % installer)
		try:
			filename, headers = urllib.urlretrieve(installer, reporthook=logTransfer)
			installer = filename
		except IOError, msg:
			logger.error("%s" % msg)
			return 1
		except:
			logger.error("File too short")
			return 1
		logger.info("Downloaded: %r" % filename)
		logger.debug('Headers:\n%s' % headers)
	else:
		if not os.path.exists(installer):
			logger.error("Update file not found")
			return 1
		
	# we execute the installer and leave any problems to him
	try:
		if isWindows():
			p = runExternal([installer, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-']) #, '/LOG=c:\\innosetup.txt'])
		elif isOpenFiler():
			p = runExternal(['tar -C / -x -z -f %s && chkconfig --add serclient && /etc/init.d/serclient restart' % installer], shell=True)
		elif isCentOS():
			p = runExternal(['rpm', '--force', '-i', '--oldpackage', installer])
		elif isDebian():
			p = runExternal(['dpkg', '-i', installer])
		elif isBsd():
			p = runExternal(['pkg_add', '-f', installer])
		else:
			raise Exception('Unsupported platform')
		output, error = p.communicate()
	except OSError, oe:
		logger.error("Error executing command: %s" % oe)
		return 1

	if p.returncode != 0:
		logger.error("Non-zero exit status for command: %r" % installer)
		return p.returncode
		
	logger.info("Done")
	logger.debug("%r" % output)
	return 0
	
if __name__ == "__main__":
	v = main()
	afterFileUpdate()
	sys.exit(v)
