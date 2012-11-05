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

#include "split.hpp"
#include <sstream>

std::vector<std::string> split(const std::string & s, char delimiter)
{
	std::vector<std::string> result;

	std::istringstream strm(s);
	std::string element;
	while (std::getline(strm, element, delimiter)) {
		result.push_back(element);	
	}
	return result;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
