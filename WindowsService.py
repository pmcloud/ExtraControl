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
import service
import pythoncom
import win32serviceutil
import win32service
import win32event
import win32evtlogutil
import win32api
import pywintypes
import winerror
import servicemanager
import os
import shlex
import argparse
import serial
import time
# for plugins
import wmi 
import platform
from tools import *
import shlex
import signal
import tempfile

def win32rename(src, dest):
	try:
		val = win32api.MoveFile(src, dest)
	except pywintypes, msg:
		pass

class WindowsService(win32serviceutil.ServiceFramework):
	_svc_name_ = "SerialService"
	_svc_display_name_ = "Serial Communication Manager Service"
	_svc_deps_ = ["EventLog", "winmgmt"]

	def __init__(self,args):
		win32serviceutil.ServiceFramework.__init__(self,args)
		self.hWaitStop = win32event.CreateEvent(None,0,0,None)

	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		# Write a 'started' event to the event log...
		win32evtlogutil.ReportEvent(self._svc_name_,
									servicemanager.PYS_SERVICE_STARTED,
									0, # category
									servicemanager.EVENTLOG_INFORMATION_TYPE,
									(self._svc_name_, ''))
		self.main()
		# and write a 'stopped' event to the event log.
		win32evtlogutil.ReportEvent(self._svc_name_,
									servicemanager.PYS_SERVICE_STOPPED,
									0, # category
									servicemanager.EVENTLOG_INFORMATION_TYPE,
									(self._svc_name_, ''))

	def main(self):
		# wait for beeing stopped...
		configuration = getConfigurationFromINI()
		#os.rename = win32rename
		service.logger = configureLogging(configuration)
		# create a temporary file where to copy the executable itself
		if getattr(sys, 'frozen', True):
			for i in range(10):
				fp = os.path.join(getRoot(), "serclient%d.exe" % i)
				if os.path.exists(fp):
					for attempt in range(10):
						try:
							os.remove(fp)
							break
						except:
							service.logger.debug("Sleeping 1 sec waiting for the operative system to unlock %r.." % fp)
							time.sleep(1)
				service.logger.debug("Creating temp file: %s" % fp)
				try:
					win32api.CopyFile(getPythonBin(), fp)
					setPythonBin(fp)
					break
				except pywintypes, msg:
					pass
			service.logger.debug("New python exe: %r" % getPythonBin())
		# start the service
		s = service.Service(configuration)
		try:
			s.start()
		except serial.serialutil.SerialException, msg:
			service.logger.critical(str(msg))
			return 1
		s.run(check=lambda stop=self.hWaitStop: win32event.WaitForSingleObject(stop, 50) == win32event.WAIT_TIMEOUT)

# pyinstaller service
if __name__ == "__main__":
	# invoked as a python interpreter
	if len(sys.argv) > 2 and "--exec" == sys.argv[1]:
		sys.path = ['.'] + sys.path
		module = sys.argv[2]
		sys.argv = sys.argv[2:]
		execfile(module, globals())
	else:
		servicemanager.Initialize(WindowsService._svc_name_, None)
		servicemanager.PrepareToHostSingle(WindowsService)
		if len(sys.argv) == 1:
			try:
				servicemanager.StartServiceCtrlDispatcher()
			except win32service.error, details:
				if details[0] == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
					win32serviceutil.usage()
		else:
			# invoked to setup the service
			win32serviceutil.HandleCommandLine(WindowsService)
