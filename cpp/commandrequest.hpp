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

#ifndef DEVELER_COMMANDREQUEST_GP_20120802
#define DEVELER_COMMANDREQUEST_GP_20120802

#include "module.hpp"
#include <string>
#include <vector>

class CommandRequest
{
public:
	CommandRequest();
	CommandRequest(const std::string & command, const std::string & guid,
                   const std::string & binary_data);

	bool isBlocking() const;
	bool isUpdateSoftware() const;
	const Module & module() const;
	std::string guid() const;
	std::string command() const;

private:
	std::string _command;
	std::string _guid;
    std::string _binary_data;
	Module _module;
};


#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
