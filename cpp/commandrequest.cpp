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

#include "commandrequest.hpp"
#include "module.hpp"

CommandRequest::CommandRequest()
{
}

CommandRequest::CommandRequest(const std::string & command, const std::string & guid,
                   const std::string & binary_data)
	:	_command(command),
	    _guid(guid),
		_binary_data(binary_data)
{
	const std::string alias = command.substr(0, command.find_first_of(" "));
	_module = Module::getModuleFromAlias(alias);
}

bool CommandRequest::isBlocking() const
{
	return _module.isValid() && _module.isBlocking();
}

bool CommandRequest::isUpdateSoftware() const
{
	return _command.find("updateSoftware") == 0;
}

const Module & CommandRequest::module() const
{
	return _module;
}

std::string CommandRequest::guid() const
{
	return _guid;
}

std::string CommandRequest::command() const
{
	return _command;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
