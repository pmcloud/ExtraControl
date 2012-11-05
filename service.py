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
import logging
import serial
import struct
import binascii
import base64
from elementtree import ElementTree as et
import threading
import subprocess
from Queue import Queue
import time
import glob
from xml.sax.saxutils import unescape, escape
from tools import *
import shlex
import tempfile
import subprocess
import string

# packet type
COMMAND = "COMMAND"
ACK = "ACK"
RECEIVED = "RECEIVED"
AUTHRESPONSE = "AUTHRESPONSE"
RESPONSE = "RESPONSE"

# mn, 30 byte command, 32 byte guid, 16 byte for late use, 4 byte packet number, 4 byte packet count, 4 byte body size
PROTOCOL_HEADER = "<c30s32sII16sI"
PROTOCOL_HEADER_SIZE = struct.calcsize(PROTOCOL_HEADER)
HEADER_MAGIC_NUMBER = "\x02"

# crc32, mn
PROTOCOL_FOOTER = "<Ic"
PROTOCOL_FOOTER_SIZE = struct.calcsize(PROTOCOL_FOOTER)
FOOTER_MAGIC_NUMBER = "\x03"

PACKET_MIN_SIZE = PROTOCOL_HEADER_SIZE + PROTOCOL_FOOTER_SIZE
SERIAL_MIN_READ = 100000
IDLE_TIMEOUT    = 60 * 15

# debug
N_DEBUG_REQUEST = 1
	
class Packet(object):
	"""
	Simple class to serialize/deserialize a packet to/from string
	"""
	
	def __init__(self, guid, type, body="", number=1, count=1):
		assert type in (COMMAND, ACK, RECEIVED, AUTHRESPONSE, RESPONSE), "Unrecognize packet type: %r" % type
		assert isinstance(guid, str) and len(guid) == 32, "Packet id is required to be a string of len 32"
		assert number <= count, "Packet number is bigger of packet count"
		self.guid = guid
		self.type = type
		self.body = body
		self.number = number
		self.count = count
		
	def _toStringNoFooter(self):
		return struct.pack(PROTOCOL_HEADER, HEADER_MAGIC_NUMBER, self.type, self.guid, self.number, self.count, "", len(self.body)) + self.body
				
	def toString(self):
		hb = self._toStringNoFooter()
		crc = binascii.crc32(hb) & 0xffffffff
		f = struct.pack(PROTOCOL_FOOTER, crc, FOOTER_MAGIC_NUMBER)
		return hb + f

	def isSinglePacket(self):
		return self.number == 1 and self.count == 1
		
	def __len__(self):
		return PROTOCOL_HEADER_SIZE + len(self.body) + PROTOCOL_FOOTER_SIZE

	def __repr__(self):
		if len(self.body) > 300:
			return "Packet(guid=%r, type=%r, body=%r ..., number=%d, count=%d)" % (self.guid, self.type, self.body[:300], self.number, self.count)
		return "Packet(guid=%r, type=%r, body=%r, number=%d, count=%d)" % (self.guid, self.type, self.body, self.number, self.count)

	def crc(self):
		crc = binascii.crc32(self._toStringNoFooter()) & 0xffffffff
		return crc

	@staticmethod
	def unpackHeader(buffer):
		# TODO: PLEASE use named tuple to unpack the struct
		mn, t, guid, packet_number, packet_count, _, bs = struct.unpack(PROTOCOL_HEADER, buffer[:PROTOCOL_HEADER_SIZE])
		t = t.split('\x00')[0]
		return mn, bs, t, guid, packet_number, packet_count
		
	@staticmethod
	def unpackFooter(string):
		crc, mn = struct.unpack(PROTOCOL_FOOTER, string[:PROTOCOL_FOOTER_SIZE])
		return crc, mn
		
	@staticmethod
	def fromString(string):
		_, bs, t, i, packet_number, packet_count = Packet.unpackHeader(string)
		b = string[PROTOCOL_HEADER_SIZE : PROTOCOL_HEADER_SIZE + bs]
		f = string[PROTOCOL_HEADER_SIZE + bs : PROTOCOL_HEADER_SIZE + bs + PROTOCOL_FOOTER_SIZE]
		p = Packet(i, t, b, packet_number, packet_count)
		crc, mn = Packet.unpackFooter(f)
		if mn != FOOTER_MAGIC_NUMBER:
			raise ValueError("end of packet not found")
		if crc != p.crc():
			raise ValueError("%x != %x" % (crc, p.crc()))
		return p

	@staticmethod
	def hasPacketHeader(string):
		return len(string) >= PROTOCOL_HEADER_SIZE 
	
	@staticmethod
	def hasValidPacketHeader(buffer):
		mn, body_size, t, guid, pn, pc = Packet.unpackHeader(buffer)
		return (mn == HEADER_MAGIC_NUMBER) and \
			(t in (COMMAND, ACK, RECEIVED, AUTHRESPONSE, RESPONSE)) and \
			(pn <= pc) and \
			not(False in map(lambda k: k in string.hexdigits, guid))
		
	@staticmethod
	def hasPacketBodyAndFooter(string):
		_, bs, _, _, _, _ = Packet.unpackHeader(string)
		return len(string) >= (PROTOCOL_HEADER_SIZE + bs + PROTOCOL_FOOTER_SIZE)
		
	@staticmethod
	def newWithACK(guid):
		return Packet(guid=guid, type=ACK)

	@staticmethod
	def newWithCOMMAND(guid, command, data=None):
		if data == None:
			cmd = "<command><commandString>%s</commandString></command>" % escape(command)
		else:
			data = base64.b64encode(data)
			cmd = "<command><commandString>%s</commandString><binaryData>%s</binaryData></command>" % (escape(command), data)
		return Packet(guid=guid, type=COMMAND, body=cmd)

	@staticmethod
	def newWithRECEIVED(guid, number=1, count=1, timeout=False):
		if timeout: 
			body = "<responseType>TimeOut</responseType>"
		else:
			body = "<responseType>Success</responseType>"
		return Packet(guid=guid, type=RECEIVED, body=body, number=number, count=count)
		
	@staticmethod
	def newWithAUTHRESPONSE(guid):
		return Packet(guid=guid, type=AUTHRESPONSE)

	@staticmethod
	def newWithRESPONSE(guid, response_type, command_name="", output_string="", return_code=0, result_message=""):
		assert response_type in ("Success", "Error", "TimeOut"), "Response type '%s' not supported" % response_type
		# todo: use elementree
		rt = "<responseType>%s</responseType>" % response_type
		rc = "<resultCode>%d</resultCode>" % return_code
		if result_message == None: result_message = ""
		rm = "<resultMessage>%s</resultMessage>" % escape(result_message)
		cn = "<commandName>%s</commandName>" % escape(command_name)
		if output_string == None: output_string = ""
		os = "<outputString>%s</outputString>" % escape(output_string)
		body = "<response>" + rt + rc + rm + cn + os + "</response>"
		return Packet(guid=guid, type=RESPONSE, body=body)

class Command(object):
	"""
	Simple class that store the logic behind a COMMAND request.
	"""
	
	def __init__(self, command, guid, binary_data):
		"""
		@param command: command as extracted from the PACKET 
		@param guid: PACKET guid
		"""
		split = shlex.split(command)
		self.command = command
		self.guid = guid
		self.binary_data = binary_data
		module_name = os.path.basename(split[0])
		self.cmd_line = None
		for type, upgradable, dirs in MODULE_TYPES.values():
			if type == MODULE_CUSTOMS: 
				# custom module must be called using 'exec script'
				continue
			self.module = moduleFromNameAndType(module_name, type)
			if self.module:
				self.cmd_line = [self.module.fullPath()] + split[1:]
				if self.binary_data:
					self.cmd_line.extend([self.binary_data])
				break
		
	def __repr__(self):
		return "Command(%r, %r, %r)" % (self.command, self.guid, self.binary_data)

	def isValid(self):
		"""
		Return True if the command refers to a proper one available on the file system
		"""
		return self.module != None
		
	def isBlocking(self):
		"""
		Returns True if the command is valid and blocking.
		"""
		if self.module == None: return False
		return self.module.isBlocking()
		
	def spawn(self, timeout, service):
		"""
		Returns a CommandObserver that takes care of spawning and controlling the process .
		"""
		return CommandObserver(self, timeout, service)
		
	def useServiceAsPythonInterpreter(self):
		return self.module.type() in [MODULE_INTERNALS, MODULE_PLUGINS] and self.module.isPythonScript()
		
	def isUpdateSoftware(self):
		return self.command.startswith('updateSoftware')
		
	def moduleName(self):
		"""
		Return the module name as seen from the user (ie restat, updateSoftware, remove..)
		"""
		return self.module.aliasName()
		
class CommandObserver(threading.Thread):
	"""
	Simple class that spawn and observe the running process.
	
	The process itself is spawned by a secondary thread that is join-ed with a timeout
	by this one. This is used to implement a timeout on the process itself.
	Process stdout and stderr are merged together.
	"""
	
	def __init__(self, command, timeout, service, *args, **kwargs):
		assert isinstance(command, Command), "object of type Command expteced"
		threading.Thread.__init__(self, *args, **kwargs)
		self._command = command
		self._service = service
		self._process = None
		self._timeout = timeout
		self._kill = False
		self.return_code = 0
		self.timedout = 0
		self.output = ""

	def run(self):
		"""
		Handle the generic external command
		"""
		# first we don't want to execute an arbitrary script/command, just the ones we have selected
		if self._command.module == None:
			logger.info("[%s] Command not found '%s'" % (self._command.guid, self._command.command))
			self.return_code = 1
			self.output = "Command not found"
			self._service.sendLater(Packet.newWithAUTHRESPONSE(self._command.guid))
			return
			
		logger.info("[%s] Running '%r' with timeout %d sec" % (self._command.guid, self._command.module, self._timeout))
		
		# if the external command is an internal/plugin python script we use ourself as python interpreter
		if self._command.useServiceAsPythonInterpreter():
			logger.debug("[%s] Python script detected, using service as python interpreter" % (self._command.guid))
			cmd_line = [getPythonBin(), '--exec'] + self._command.cmd_line
			if not IS_FROZEN and IS_WINDOWS:
				# in this case we cant Popen .py script because we still need an interpreter to be used
				cmd_line = [sys.executable] + cmd_line
			logger.debug("[%s] >> %r" % (self._command.guid, cmd_line))
		else:
			cmd_line = self._command.cmd_line

		def target():
			try:
				self._process = runExternal(cmd_line, close_handles=self._command.isUpdateSoftware())
				self.output, _ = self._process.communicate()
			except OSError, oe:
				logger.debug("error executing command: %s" % oe)
				self.output = str(oe)
				del oe
			
		thread = threading.Thread(target=target)
		thread.start()
		
		# watch the process and for the request to kill it
		start_time = time.time()
		while (time.time() - start_time) < self._timeout:
			thread.join(0.5)
			if thread.isAlive() == False or self._kill == True: break
		
		if thread.isAlive():
			if self._kill == False:
				# in this case we don't log it to avoid misunderstandings
				logger.error("[%s] process timeout" % self._command.guid)
			self._process.terminate()
			thread.join()
			self.timedout = True
		else:
			self.timedout = False
		
		# remove the restart token because it means it didnt work
		getRestartGUID(remove=True)
		
		# read the output of the failed updateSoftware command (we should have been killed if the attempt was a success)
		if self._command.isUpdateSoftware():
			self.output = getUpdateSoftwareLOG(remove=True)
			logger.debug("Detected failed updateSoftware attempt with log:\n%s" % self.output)
			
		if self._kill: return
		
		if self._process != None:
			if self._process.returncode != 0:
				logger.debug("[%s] Non-zero exit status for command: %s" % (self._command.guid, self._command.command))
			else:
				logger.debug("[%s] Command completed." % self._command.guid)
			self.return_code = self._process.returncode
		else:
			# oserror exception
			self.return_code = 1
			
		self._service.sendLater(Packet.newWithAUTHRESPONSE(self._command.guid))
	
	def responsePacket(self):
		"""
		Return a packet of type RESPONSE properly filled with the process return code and output
		"""
		rm = ""
		os = ""
		if self.timedout:
			rt = "TimeOut"
		elif self.return_code == 0:
			rt = "Success"
			os = self.output
		else:
			rt = "Error"
			rm = self.output
			
		p = Packet.newWithRESPONSE(guid=self._command.guid,
			response_type=rt,
			command_name=self._command.command,
			output_string=os,
			return_code=self.return_code,
			result_message=rm)
		return p

	def kill(self):
		"""
		Kill the current process and watcher. Can not be called from the process thread.
		"""
		self._kill = True
		self.join()
		
class ReplyResponseObserver(object):
	"""
	Simple class to delivery a Response Packet without breaking the CommandObserver interface
	"""
	def __init__(self, response):
		self._response = response
		
	def responsePacket(self):
		return self._response

class Service(object):
	"""
	service class.
	Read from the serial port and manage the commands execution.
	"""
	
	def __init__(self, args, serial_class=serial.Serial):
		"""
		Create a service instance ready to be used calling -L{start} and then -L{run}
		
		@param args: Arguments from ArgumentParser, are passed to the serial class constructor
		@param serial_class: Serial class, default to serial.Serial can be changed for testing
							 purpose. The class must respond to -B{read} and -B{write}.
		"""
		assert isinstance(args, dict), "args must be a dictionary"
		self._args = args
		self._serial_class = serial_class
		self._buffer = ""
		self._threads = {}
		self._out_queue = Queue()
		self._command_timeout = int(args['PLUGINS']['command_timeout'])
		self._timers = []
		self._command_queue = []
		self._command_queue_process = True
		self._quit = False
		self._packet_pool = dict()
		self._logic_timeout = None
		self._last_data = time.time()

	def idleTime(self):
		return time.time() - self._last_data

	def send(self, p):
		"""
		Send a packet by writing its string form on the serial port
		
		@param p: Instance of packet
		"""
		assert isinstance(p, Packet), "Not a Packet"
		self._last_data = time.time()
		logger.info("Sending packet: %r" % p)
		k = p.toString()
		logger.debug("Writing: %d %r" % (len(k), k))
		tot = len(k)
		if chr(255) in k:
			logger.debug("IAC FOUND")
		done = 0
		# chunk write
		cs = 8192
		while len(k) != 0:
			e = k[:cs]
			k = k[cs:]
			done += len(e)
			logger.debug("Writing to serial port: %d/%d bytes" % (done, tot))
			self.sp.write(e)
			#time.sleep(20)
		
	def sendLater(self, p):
		"""
		Add the packet in a queue and send it as soon as possible
		"""
		assert isinstance(p, Packet), "Not a Packet"
		self._out_queue.put(p)
		
	def addToPacketPool(self, packet):
		"""
		Add a packet in pool of packets for waiting all of them
		"""
		self._packet_pool.setdefault(packet.guid, dict())[packet.number] = packet
		print self._packet_pool
		
	def isPacketPoolCompleteForPacket(self, packet):
		"""
		Return True if we have all packets of that group
		"""
		return len(self._packet_pool.get(packet.guid, dict()).keys()) == packet.count
		
	def aggregatePacketsFromGUID(self, guid):
		"""
		Merge all packets together in a big huge packet
		"""
		np = len(self._packet_pool.get(guid, dict()).keys())
		print np
		up = []
		for i in range(1, np+1):
			try:
				p = self._packet_pool.get(guid)[i]
			except KeyError:
				logger.error("Error decoding a sequence of packets: %r" % self._packet_pool.get(guid).keys())
				return None
			up.append(p.body)
		return Packet(p.guid, p.type, ''.join(up), np, np)
		
	def removeFromPacketPoolForGUID(self, guid):
		"""
		Remove and clean the packet pool for the requested guid
		"""
		del self._packet_pool[guid]
		
	def read(self, timeout=None):
		"""
		Return a packet received from the serial port or None if timeout is elapsed
		
		@param timeout: timeout in seconds
		"""
		started = time.time()
		while 1:
			if timeout and (time.time() - started) > timeout:
				return None
			if Packet.hasPacketHeader(self._buffer):
				if Packet.hasValidPacketHeader(self._buffer):
					if self._logic_timeout == None:
						self._logic_timeout = time.time()
					else:
						if (time.time() - self._logic_timeout) > 30.0:
							logger.debug("LOGIC TIMEOUT detected, looking for new packet")
							_, _, _, guid, pn, pc = Packet.unpackHeader(self._buffer)
							self.send(Packet.newWithRECEIVED(guid, pn, pc, timeout=True))
							self._buffer = self._buffer[1:]
							self._logic_timeout = None
							return None
					
					if Packet.hasPacketBodyAndFooter(self._buffer):
						logger.debug("Valid footer received")
						try:
							last_packet = Packet.fromString(self._buffer)
							logger.debug("Packet received: %r" % last_packet)
							self._buffer = self._buffer[len(last_packet):]
							if last_packet.isSinglePacket():
								return last_packet
							else:
								# we store this packet in the pool for later aggregation
								self.addToPacketPool(last_packet)
								if self.isPacketPoolCompleteForPacket(last_packet):
									# aggregation
									p = self.aggregatePacketsFromGUID(last_packet.guid)
									# remove
									self.removeFromPacketPoolForGUID(last_packet.guid)
									if p:
										logging.debug("[%r] Aggregate multiple packets" % p.guid)
										return p
								else:
									# send the received packet to keep reading the new ones, at this point
									# we can't check if the XML is valid or the BASE64 data are ok, we wait to
									# have all of them
									self.send(Packet.newWithRECEIVED(last_packet.guid, last_packet.number, last_packet.count))
						except ValueError, ve:
							logger.critical("Error decoding packet: %s" % ve)
							# todo: send a response with error crc not valid
							self._buffer = self._buffer[1:]
							del ve
					else:
						# wait for more bytes
						p = len(self._buffer)
						v = self.sp.read(SERIAL_MIN_READ)
						self._buffer += v 
						if v:
								self._last_data = time.time()
						if p != len(self._buffer):
							logger.debug("Reading: buffer size %d - %r" % (len(self._buffer), v))
				else:
					# skip bytes looking for a new magic number
					self._buffer = self._buffer[1:]
					s = 0
					while len(self._buffer) > 0 and self._buffer[0] != chr(0x02) and s < 5000:
						self._buffer = self._buffer[1:]
						s = s + 1
					logger.debug("Header not found: skipped %d byte from read buffer" % s)
			else:
				# wait for more bytes
				self._logic_timeout = None
				p = len(self._buffer)
				v = self.sp.read(SERIAL_MIN_READ)
				self._buffer += v
				if v:
						self._last_data = time.time()
				if p != len(self._buffer):
					logger.debug("Reading: buffer size %d - %r" % (len(self._buffer), v))

	def start(self):
		"""
		Start the service by opening the serial port.
		"""
		logger.info("Opening serial")
		c = self._args['SERIAL']
		if c['port'] == '0': 
			port = 0
		else:
			port = c['port']
		try:
			self.sp = self._serial_class(port=port,
										 baudrate=c['baudrate'],
										 bytesize=int(c['bytesize']),
										 parity=c['parity'],
										 stopbits=float(c['stopbits']),
										 timeout=1)
										 
		except AttributeError:
			# happens when the installed pyserial is older than 2.5. use the
			# Serial class directly then.
			logger.critical("Serial attribute Error")
		logger.info("Serial port open with success: %r", self.sp)

	def run(self, check=lambda: 1):
		"""
		Start reading from serial port managing any requested command.
		"""
		logger.info("Service version: %s" % getServiceVersion())
		# Recovering from a restart ?
		rg = getRestartGUID(remove=True)
		if rg != None:
			logger.info("Sending restart/updateSofware response")
			t = getUpdateSoftwareLOG(remove=True)
			p = Packet.newWithAUTHRESPONSE(rg)
			self._threads[p.guid] = ReplyResponseObserver(Packet.newWithRESPONSE(p.guid, "Success", "", t))
			self.send(p)
		
		# we store the number of threads before starting accepting any requer
		# because we monitor its value to undertand when a blocking task can start
		# Normal values is 1 but under windows services its 2.
		base_threads = threading.activeCount()
		while not self._quit and check():
			# read from the serial waiting for a packer or timeout
			p = self.read(timeout=1.0)
			if p: 
				self.processPacket(p)
			elif self.idleTime() > IDLE_TIMEOUT:
				self.send(Packet.newWithACK(guidFromInt(0)))
			# process AUTHRESPONSE commands generated by running threads
			while not self._out_queue.empty():
				p = self._out_queue.get()
				self.send(p)
				#self._out_queue.task_done()
			# are all done ?
			done = threading.activeCount() == base_threads
			# if all done and the queue processig is stopped we can restart it
			if done and self._command_queue_process == False:
				self._command_queue_process = True
				logger.debug("Leaving blocking mode")
			# if enabled, process queued COMMAND
			if self._command_queue_process == True:
				while self._command_queue:
					if self._command_queue[0].isBlocking():
						self._command_queue_process = False
						if done == False:
							logger.debug("Entering blocking mode")
						else:
							logger.debug("Spawning blocking command")
							c = self._command_queue.pop(0)
							self.spawnCommand(c)
						break
					else:
						c = self._command_queue.pop(0)
						self.spawnCommand(c)
						done = False
			else:
				logger.debug("Waiting for non blocking process to terminate: %d" % threading.activeCount())
		return self._quit

	def processCommand(self, p):
		"""
		Process Packet with type COMMAND.
		The request is ignored in case of errors with the packed body xml.
		
		@param p: Instance of Packet
		"""
		assert p.type == COMMAND, "Packet with type COMMAND expected"
		
		# parse the body looking for commandString and binaryData
		logger.debug("XML: %r" % p.body)
		if p.body.startswith('?'): p.body = p.body[1:]
		try:
			xml = et.fromstring(p.body)
		except et.ParseError, pe:
			logger.critical("Malformed xml: %s" % pe)
			self._threads[p.guid] = ReplyResponseObserver(Packet.newWithRESPONSE(p.guid, "Error"))
			self.send(Packet.newWithAUTHRESPONSE(p.guid))
			return
		if xml.tag != "command":
			logger.critical("Malformed command xml received: expected tag 'command' received '%s'" % xml.tag)
			self._threads[p.guid] = ReplyResponseObserver(Packet.newWithRESPONSE(p.guid, "Error"))
			self.send(Packet.newWithAUTHRESPONSE(p.guid))
			return
		cs = list(xml.findall("commandString"))
		if len(cs) != 1:
			logger.critical("Malformed command xml received: expected 1 tag 'commandString' received %d tags" % len(cs))
			self._threads[p.guid] = ReplyResponseObserver(Packet.newWithRESPONSE(p.guid, "Error"))
			self.send(Packet.newWithAUTHRESPONSE(p.guid))
			return
		cmd = cs[0].text
		bd = list(xml.findall("binaryData"))
		
		if len(bd) == 1:
			try:
				bd = base64.b64decode(bd[0].text)
			except TypeError, te:
				logger.critical("Malformed base64encoded binary data: %s" % te)
				self._threads[p.guid] = ReplyResponseObserver(Packet.newWithRESPONSE(p.guid, "Error"))
				self.send(Packet.newWithAUTHRESPONSE(p.guid))
				return
			# Save binary data in a temporary file and store its path
			tf = os.path.join(tempfile.gettempdir(), p.guid)
			open(tf, "wb").write(bd)
			bd = tf
		else:
			bd = ""
			
		# We answer that we have received it
		p = Packet.newWithRECEIVED(p.guid)
		self.send(p)

		# Add the new request in a queue processed by the main loop
		c  = Command(cmd, p.guid, bd)
		self._command_queue.append(c)

	def processAuthResponse(self, p):
		"""
		Process Packet with type AUTHRESPONSE.
		
		@param p: Instance of Packet
		"""
		assert p.type == AUTHRESPONSE, "Packet with type AUTHRESPONSE expected"
		try:
			co = self._threads[p.guid]
			reply = co.responsePacket()
			self.send(reply)
			del self._threads[p.guid]
		except KeyError:
			logger.error("Response requested for an unknow packet id: %s" % p.guid)
			reply = Packet.newWithRESPONSE(p.guid, "Error")
			self.send(reply)

	def processPacket(self, p):
		"""
		Parse and process Packet p
		
		@param p: Instance of Packet
		"""
		if p.type == ACK:
			logger.info("[%s] ACK Received" % p.guid)
			p = Packet.newWithACK(p.guid)
			self.send(p)
		if p.type == COMMAND:
			logger.info("[%s] COMMAND Received" % p.guid)
			self.processCommand(p)
		if p.type == RECEIVED:
			pass
		if p.type == AUTHRESPONSE:
			logger.info("[%s] AUTHRESPONSE Received for request" % p.guid)
			self.processAuthResponse(p)
		if p.type == RESPONSE:
			logger.error("[%s] RESPONSE Received for request" % p.guid)

	def spawnCommand(self, cmd):
		"""
		Spawn the command and register it for later query
		"""
		assert isinstance(cmd, Command), "Expected an instance of type command" 
		if cmd.command == 'restart' or cmd.command.startswith('updateSoftware'):
			saveRestartGUID(cmd.guid)
		timeout = self._args['TIMEOUT'].get(cmd.moduleName(), self._command_timeout)
		try:
			timeout = int(timeout)
		except ValueError:
			timeout = self._command_timeout
		co = cmd.spawn(timeout, self)
		self._threads[cmd.guid] = co
		co.start()

	def simulate(self, command, binary_data):
		"""
		Enter simulation mode: basically it sends a small amount of command packets waiting and validating 
		the answer sent back from another instance of service.
		
		Used for development and debugging only.
		"""
		logger.debug("Simulating requests")
		if binary_data != None:
			bd = open(binary_data).read()
		else:
			bd = None
		
		if 0:
			self.send(Packet.newWithACK(guidFromInt(0)))
			r = self.read()
			assert r.type == ACK
		
		test = [guidFromInt(k+1) for k in range(N_DEBUG_REQUEST)]
		for k in test:
			self.send(Packet.newWithCOMMAND(k, command, bd))

		while len(test) != 0:
			r = self.read()
			if r.type == RECEIVED:
				pass
			if r.type == AUTHRESPONSE:
				self.send(Packet.newWithAUTHRESPONSE(r.guid))
			if r.type == RESPONSE:
				assert r.guid in test, "Request already cleaned"
				test.remove(r.guid)


def parseArgs(command_line, silent=False):
	"""
	Return a tuple with:
		configuration dictionary generated by parsing passed arguments using ArgumentParser
		ArgumentParser.Namespace
	"""
	parser = argparse.ArgumentParser(
		description='Execute commands received through the serial port', fromfile_prefix_chars='@')
		
	if silent:
		# by default orgparse will exit if one argument is not valid, we don't want that 
		# when we run as a windows service (we trap it properly)
		def myerror(self, message):
			self.error_triggered = True
			self.print_usage(_sys.stderr)
		parser.error = myerror
		
	conf_from_ini = getConfigurationFromINI()

	# serial port arguments
	parser.add_argument('--port', help='serial port (default: open first serial port)', dest='serial_port', default=conf_from_ini['SERIAL']['port'])
	parser.add_argument('--baudrate', help='serial port baudrate (default: %(default)s)', dest='baudrate', type=int, default=conf_from_ini['SERIAL']['baudrate'])
	parser.add_argument('--bytesize', help='serial port bytesize (default: %(default)s)', dest='bytesize',
		choices=[serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS], default=conf_from_ini['SERIAL']['bytesize'])
	parser.add_argument('--parity', help='serial port parity (default: %(default)s)', dest='parity',
		choices=[serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE], default=conf_from_ini['SERIAL']['parity'])
	parser.add_argument('--stopbits', help='serial port stopbits (default: %(default)s)', dest='stopbits',
		choices=[serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO], default=conf_from_ini['SERIAL']['stopbits'])

	# extra
	parser.add_argument('--exec', help='exec any python script using the current interpreter', dest='exec_script', default=None)
	parser.add_argument('--command-timeout', help='debug: command execution timeout in seconds(default: %(default)s sec)', dest='command_timeout', type=int, default=conf_from_ini['PLUGINS']['command_timeout'])
	parser.add_argument('--debug-command', help='debug: send a command packet', dest='debug_command', default=None)
	parser.add_argument('--debug-command-binary-data', help='debug: add binary data to the command packet', dest='debug_command_bd', default=None)
	parser.add_argument('--send-raw', help='send raw packet', dest='send_raw', default=None)
	parser.add_argument('--log', help='enable logging to file (default: %(default)s)', dest='log', default=conf_from_ini['LOG']['file'])
	parser.add_argument('--log-level', help='log level (default: %(default)s)', dest='log_level', default=conf_from_ini['LOG']['level'])
	parser.add_argument('--log-syslog', help='enable logging to syslog server', dest='syslog_address', default=conf_from_ini['LOG']['syslog_address'])
	parser.add_argument('--pid', help='PID file path', dest='pid', metavar='PATH')
	parser.add_argument('--daemon', help='daemonize', dest='daemon', action='store_true')
	
	args = parser.parse_args(command_line)
	if getattr(parser, 'error_triggered', False):
		return None
		
	return (getConfigurationDictFromArgparse(args), args)
	
def shellRun(config, args):
	"""
	Run the service as a shell script, no daemon, no service
	"""
	global logger
	logger = configureLogging(config)
	
	# start the service
	s = Service(config)
	try:
		s.start()

		if args.daemon:
				daemonize(args.pid)
		elif args.pid:
				pidfile = file(args.pid, 'w')
				pidfile.write(str(os.getpid()))
				pidfile.close()
	except serial.serialutil.SerialException, msg:
		logging.critical(str(msg))
		return 1
		
	if args.send_raw != None:
		e = eval("'"+args.send_raw+"'")
		print 'Sending:', repr(e)
		s.sp.write(e)
		p = s.read()
		print repr(p)
		return 0
		
	if args.debug_command == None:
		s.run()
	else:
		s.simulate(args.debug_command, args.debug_command_bd)

	return 0
	
if __name__ == "__main__":
	# if we get passed --exec it means we just play the role of a python interpreter
	if len(sys.argv) > 2 and "--exec" == sys.argv[1]:
		sys.path = ['.'] + sys.path
		module = sys.argv[2]
		sys.argv = sys.argv[2:]
		execfile(module, globals())
	else:
		config, args = parseArgs(sys.argv[1:])
		sys.exit(shellRun(config, args))
