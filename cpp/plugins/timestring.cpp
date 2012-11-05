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

#include "timestring.hpp"
#include <ctime>
#include <cstddef>
#include <stdexcept>

std::string timeString(const std::string & format)
{
	const time_t stamp = std::time(NULL);
	if (stamp != ((time_t)-1)) {
		const tm * b = std::localtime(&stamp);
		if (b != NULL) {
			const std::size_t max_size = 256;
			char buffer[max_size] = { 0 };
			if (std::strftime(buffer, max_size, format.c_str(), b) != 0) {
				return std::string(buffer);
			}
		}
	}

	throw std::runtime_error("time unavailable");
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
