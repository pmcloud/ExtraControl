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
import shlex

if isWindows():
	import win32serviceutil

def main():
	if not isWindows():
		# since we're going to kill our parent (process) we need
		# to avoid writing to a closed pipe
		null = os.open("/dev/null", os.O_RDWR)
		os.dup2(null, 1)
		os.dup2(null, 2)

	if isWindows():
		win32serviceutil.RestartService("SerialService")
	elif isFreeNAS() or isPfSense():
		cmd = "/usr/local/etc/rc.d/serclient restart"
		subprocessCheckCall(shlex.split(cmd))
	elif isUbuntu():
		cmd = "initctl restart serclient"
		subprocessCheckCall(shlex.split(cmd))
	elif isDebian() or isCentOS():
		cmd = "/etc/init.d/serclient restart"
		subprocessCheckCall(shlex.split(cmd))
	else:
		print "Don't know how to restart this distribution"
	return 1
	
if __name__ == "__main__":
	sys.exit(main())
