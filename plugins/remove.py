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
	parser = argparse.ArgumentParser(add_help=True, prog='remove')
	subparsers = parser.add_subparsers(title='subcommands', help='valid subcommands', dest="sub_command")
	
	usermodule = subparsers.add_parser('usermodule')
	usermodule.add_argument("module", help="module name")
	
	help = subparsers.add_parser('help')
	args = parser.parse_args()
	
	if args.sub_command == 'help':
		usermodule.print_help()
		return 0
	
	m = moduleFromNameAndType(args.module, MODULE_CUSTOMS)
	
	if m == None:
		print "Module not found"
		return 1
		
	beforeFileUpdate()

	try:
		os.remove(m.fullPath())
	except OSError, oe:
		afterFileUpdate()
		print oe
		return 1

	afterFileUpdate()

	print 'Done'
	return 0
	
	
if __name__ == "__main__":
	sys.exit(main())
