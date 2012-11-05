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

def main():
	if len(sys.argv) < 3:
		print 'Usage: exec script module [args ...]'
		return 1
		
	module = sys.argv[2]
	args = sys.argv[3:]
	
	m = moduleFromNameAndType(module, MODULE_CUSTOMS)
	
	if m == None:
		print "Module custom does not exists"
		return 1

	try:
		p = runExternal([m.fullPath()] + args)
		output, error = p.communicate()
	except OSError, oe:
		print "Error executing command: %s" % oe
		return 1

	if p.returncode != 0:
		print output,
		return p.returncode
		
	print output,
	return 0
	
if __name__ == "__main__":
	sys.exit(main())
