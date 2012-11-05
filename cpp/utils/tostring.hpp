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

#include <sstream>
#include <string>

#ifndef DEVELER_TOSTRING_GP_20120730
#define DEVELER_TOSTRING_GP_20120730

template<typename T>
std::string toString(const T & t)
{
	std::ostringstream str;
	str << t;
	return str.str();
}

#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
