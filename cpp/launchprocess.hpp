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

#ifndef DEVELER_LAUNCHPROCESS_GP_20120809
#define DEVELER_LAUNCHPROCESS_GP_20120809

#include <cstdlib>

// ------------- TODO: temporary, until we'll integrate logging
#include <iostream>
#include <ostream>
// ------------------------------------------------------------

struct LaunchResult
{
	enum Result { failure = 0, success, timeout };

	LaunchResult() : result(failure), output(), exit_code(EXIT_FAILURE) {}

	Result result;
	std::string output;
	int exit_code;
};

LaunchResult launchProcess(const std::string & name, const std::string & arguments, bool capture_output, int timeout_in_seconds = 10);

#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
