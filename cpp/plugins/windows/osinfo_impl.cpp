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

#include "osinfo.hpp"

#include <string>
#include <sstream>
#include <stdexcept>
#include <utility>

#include <windows.h>

info getOSInfo()
{
	OSVERSIONINFOEX infoex = {};
	infoex.dwOSVersionInfoSize = sizeof infoex;

	if (::GetVersionEx(reinterpret_cast<LPOSVERSIONINFO>(&infoex)) == 0) {
		throw std::runtime_error("can't retrieve OS version");
	}

	const std::pair<int, int> major_minor = std::make_pair(
	            infoex.dwMajorVersion, infoex.dwMinorVersion);

	// Only Windows 2003 and Windows 2008 systems are supported:
	// the "detection" is just incorrect on systems other then these
    // which also have version 5.2 or 6.{0|1} (e.g. WinXP x64 or Vista).
	//
	info result;
	result.name = "Windows";
	if (major_minor == std::make_pair(5, 2)) {
		result.version = "2003";
	} else if (major_minor == std::make_pair(6, 0) ||
			   major_minor == std::make_pair(6, 1)) {
		result.version = "2008";
	} else {
		throw std::runtime_error("unsupported Windows version");
	}


	std::stringstream sstr;
	sstr << "build " << infoex.dwBuildNumber << ", " << infoex.szCSDVersion;
	result.details = sstr.str();

	return result;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
