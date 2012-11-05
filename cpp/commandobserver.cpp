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


#include "commandobserver.hpp"
#include "serialwatcher.hpp"
#include "tools.hpp"
#include <cstddef>

void thread_func(void * p)
{
	static_cast<CommandObserver *>(p)->run();
}


CommandObserver::CommandObserver()
	:	_thread(NULL),
	  _timeout(0),
	  _service(NULL),
	  _response(NULL),
	  _return_code(0)
{
}

CommandObserver::CommandObserver(std::auto_ptr<Packet> response)
	: _thread(NULL),
	  _timeout(0),
	  _service(NULL),
	  _response(response),
	  _return_code(0)
{
}

CommandObserver::CommandObserver(const CommandRequest & request, int timeout, SerialWatcher & service)
	:	_thread(NULL),
		_request(request),
		_timeout(timeout),
		_service(&service),
		_response(NULL),
		_return_code(0)
{
}

CommandObserver::~CommandObserver()
{
	if (_thread != NULL) {
		_thread->join();
	}

	delete _thread;
}

void CommandObserver::start()
{
	if (_response.get() == NULL) // If already has a response then skips executing the command
	{
		_thread = new tthread::thread(&::thread_func, this);
	}
}

void CommandObserver::run()
{
	logger->info() << "Run command: " << _request.command();

	if (!_request.module().isValid()) {
		logger->err() << "Invalid module:" << _request.module().alias();
        	result_.exit_code = 1;
		_service->sendLater(*Packet::createWithAuthResponse(_request.guid()));
		return;
	}

	// TODO: integrate logger
	logger->debug() << "[" << _request.guid() << "] Running '" << _request.module()
					<< "' with timeout " << _timeout << "(s)";

	result_ = ::launchProcess(_request.module().fullPath(),
                                _request.command(), !_request.isUpdateSoftware());

	_service->sendLater(*Packet::createWithAuthResponse(_request.guid()));
}

bool CommandObserver::isRunning() const
{
	return _thread != NULL && _thread->joinable();
}

const CommandRequest & CommandObserver::request() const
{
	return _request;
}

std::auto_ptr<Packet>& CommandObserver::responsePacket()
{
	if (_response.get() == NULL) // Builds the response
	{
		std::string rm = "";
		std::string os = "";
		Packet::ResponseType rt;
		if (result_.result == LaunchResult::timeout)
		{
			rt = Packet::TimeOut;
		}
		else if (result_.exit_code == 0)
		{
			rt = Packet::Success;
			os = result_.output;
		}
		else
		{
			rt = Packet::Error;
			rm = result_.output;
		}
		_response = Packet::createWithResponse(_request.guid(), rt, _request.command(), os, _return_code, rm);
	}
	return _response;
}
// vim: set ft=cpp noet ts=4 sts=4 sw=4:
