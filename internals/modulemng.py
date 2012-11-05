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
from elementtree.ElementTree import Element, tostring
from tools import *

def main():
	parser = argparse.ArgumentParser(add_help=False, prog='modulemng')
	subparsers = parser.add_subparsers(title='subcommands', help='valid subcommands', dest="sub_command")
	get = subparsers.add_parser('get')
	get.add_argument("module", help="module", default=None)
	list = subparsers.add_parser('list')
	list.add_argument("-d", help="module details", dest="details", action="store_true", default=False)
	help = subparsers.add_parser('help')
	args = parser.parse_args()
	
	if args.sub_command == "help":
		parser.print_help()
		return 0

	# retrieve all modules from file system
	top = Element('modules')
	
	# get
	if args.sub_command == "get":
		m = searchModule(args.module)
		if m != None:
			top.append(m.toElementTree(True))
			print tostring(top)
			return 0
		print 'module not found'
		return 1

	# list
	all_modules = browseModules()
	for type, modules in all_modules.items():
		for module in modules.values():
			em = module.toElementTree(args.details)
			top.append(em)

	print tostring(top)
	return 0

if __name__ == "__main__":
	sys.exit(main())
