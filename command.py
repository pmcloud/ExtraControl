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
import argparse
import binascii
import base64
from elementtree import ElementTree as et
from elementtree.ElementTree import tostring
from xml.sax.saxutils import unescape, escape
import xmlrpclib
from xml.dom import minidom

def prettify(elem):
	"""Return a pretty-printed XML string for the Element.
	"""
	rough_string = et.tostring(elem, 'utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="  ")

def_target = "DC1_ARU-1265_Centos56_1346"
def_target = "DC1_ARU-1265_Win2008Hv_1354"

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description='Request a command using xmlrpc', fromfile_prefix_chars='@')
	parser.add_argument('--target', help='target host (default: %(default)s)', default=def_target, dest='target')
	parser.add_argument('--command', help='command to request', dest='command', default=None)
	parser.add_argument('--data', help='path to file data', dest='binary', default=None)
	parser.add_argument('--verbose', help='verbose', action='store_const', default=False, const=True)
	parser.add_argument('--vmware', help='specify a vmware virtual machine as target', action='store_const', default=False, const=True)
	args = parser.parse_args()
	
	if args.command == None:
		parser.print_help()
		sys.exit(0)
	
	server = xmlrpclib.ServerProxy("http://95.110.152.14/Services/SCPProvider/xmlrpc", verbose=args.verbose)
	try:
		data = open(args.binary).read()
		data = base64.b64encode(data)
	except:
		data = ""
		
	if args.vmware:
		request = server.Send(args.target, "", "", "COMMAND", args.command, data)
	else:
		request = server.Send(args.target, "", "ddhvc01s02.dcloud.local", "COMMAND", args.command, data)
		
	if args.verbose:
		print "\n\n"
		print repr(request)
		print "\n\n"
	# clean
	extra = request[request.rfind('>')+1:]
	request = request[:request.rfind('>')+1]
	try:
		# for commands returning XML, pretty-print both response
		# and output
		x = et.fromstring(unescape(request))
	except et.ParseError:
		# for commands returning plain text, display output as-is
		# (it also works for commands returning invalid XML)
		x = et.fromstring(request)
	print unescape(prettify(x))
	if args.verbose:
		print 'Extra at the end: %r' % extra
	
	
