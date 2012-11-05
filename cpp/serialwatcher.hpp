// ExtraControl - Aruba Cloud Computing ExtraControl
// Copyright (C) 2012 Aruba S.p.A.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#ifndef DEVELER_SERIALWATCHER_GP_20120716
#define DEVELER_SERIALWATCHER_GP_20120716

#include "logging.hpp"
#include "third-party/serial/include/serial/serial.h"
#include "third-party/tinythreadpp/source/tinythread.h"
#include "packet.hpp"
#include "commandrequest.hpp"
#include "commandobserver.hpp"
#include <map>
#include <queue>
#include <memory>
#include <string>
#include <utility>
#include <cassert>

class PacketPool
{
public:
	void add(const Packet & packet)
	{
		// TODO: sanity check (do we received a duplicate packet?)
		map_type::iterator it = _pool.find(packet.guid());
		it->second.insert(std::pair<std::size_t, Packet>(
			packet.number(), packet
			));
	}
	bool hasAllPacketsFor(const Packet & packet) const
	{
		map_type::const_iterator it = _pool.find(packet.guid());
		return it != _pool.end() && it->second.size() == packet.count();
	}
	void removeAllPacketsFor(const Packet & packet)
	{
		std::size_t count = _pool.erase(packet.guid());
		assert(count == 1);
	}

    std::auto_ptr<Packet> getFullPacketForGuid(const std::string & guid) const
	{
		map_type::const_iterator it = _pool.find(guid);
		assert(it != _pool.end());

		std::string body;
		for (nested_map_type::const_iterator iter = it->second.begin();
			iter != it->second.end();
			++iter) {
				const std::string single_body = iter->second.body();
				body.insert(body.end(), single_body.begin(), single_body.end());
		}
		const Packet first_packet = it->second.begin()->second;
        return std::auto_ptr<Packet>(new Packet(first_packet.command(), first_packet.guid(), body));
	}

private:
	// { guid, {packet_number, packet} }
	typedef std::map<std::size_t, Packet> nested_map_type;
	typedef std::map<std::string, nested_map_type> map_type;
	map_type _pool;

public:
	typedef map_type::iterator iterator;
	typedef map_type::const_iterator const_iterator;

	iterator begin();
	const_iterator begin() const;
	iterator end();
	const_iterator end() const;
};

// class SerialWatcher
// -------------------
//
// Reads from serial port and manages command execution
//
class SerialWatcher
{
public:
	SerialWatcher(const std::string & port, int command_timeout);
	
	// Starts, by opening the serial port
	// Throws? --gps
	void start(int baud_rate, int byte_size, int parity, int stop_bits, bool& stopflag);

	//Packet joinPacketsWithGuid(const std::string & guid);

	// Sends a packet through the serial port.
	void send(const Packet & packet);
	void sendLater(const Packet & packet);

private:
    std::auto_ptr<Packet> doRead(int timeout_sec=0);
	void reactToPacket(const Packet & packet);
	void processCommand(const Packet & packet);
	void processAuthResponse(const Packet & packet);
	void spawnCommand(const CommandRequest &);

private:
    static const int SERIAL_MIN_READ;
    static const int LOGIC_TIMEOUT;

	typedef std::map<std::string, CommandObserver *> thread_map_type;
	// store the port name for later, since we don't want to open the
	// port as soon as the watcher is constructed
	std::string _port_name;
	std::auto_ptr<serial::Serial> _serial_port;
	PacketPool _pool;
	thread_map_type _thread_map;
	std::queue<CommandRequest> _command_queue;
	std::queue<Packet> _output_queue;
	tthread::mutex _output_queue_mutex;
	bool _process_command_queue;
	int _command_timeout;
    std::vector<char> _buffer;

	bool isIdle() const;
};

#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
