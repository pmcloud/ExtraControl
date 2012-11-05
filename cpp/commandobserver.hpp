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

#ifndef DEVELER_COMMANDOBSERVER_GP_20120730
#define DEVELER_COMMANDOBSERVER_GP_20120730

#include "commandrequest.hpp"
#include "utils/launchprocess.hpp"
#include "third-party/tinythreadpp/source/tinythread.h"
#include <cstdlib>
#include <memory>

class SerialWatcher;
class Packet;

class CommandObserver
{
public:
	CommandObserver();
	CommandObserver(std::auto_ptr<Packet> response); // Does not exectute anything. Just provides a responsePacket
	CommandObserver(const CommandRequest & request, int timeout, SerialWatcher & service);
	~CommandObserver();

	void start();
	void run();
	bool isRunning() const;
	const CommandRequest & request() const;
	std::auto_ptr<Packet>& responsePacket();

private:

	tthread::thread * _thread;
	LaunchResult result_;
	CommandRequest _request;
	int _timeout;
	SerialWatcher * _service;
	std::auto_ptr<Packet> _response;
	int _return_code;
};




#endif
// vim: set ft=cpp noet ts=4 sts=4 sw=4:
