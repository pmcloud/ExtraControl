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
#include "utils/canreadfile.hpp"
#include "utils/split.hpp"

#include <string>
#include <stdexcept>
#include <fstream>

info getOSInfo()
{
	info result;

	std::string info_file = "/etc/version.freenas";
	if (canReadFile(info_file)) {
		std::ifstream f(info_file.c_str());
		std::string content;
		std::getline(f, content);
		const std::vector<std::string> & parts = split(content, '-');
		if (parts.size() < 3) {
			throw std::runtime_error("unexpected format of " + info_file);
		} else {
			result.name =    parts[0];
			result.version = parts[1];
			result.details = parts[2];
			return result;
		}
	} else {
		info_file = "/etc/platform";
		if (canReadFile(info_file)) {
			std::ifstream f(info_file.c_str());
			std::getline(f, result.name);

			info_file = "/etc/version";
			std::ifstream f2(info_file.c_str());
			std::string version_string;
			std::getline(f2, version_string);
			const std::vector<std::string> parts = split(version_string, '-');
			if (parts.size() < 2) {
				throw std::runtime_error("unexpected format of " + info_file);
			} else {
				result.version = parts[0];
				result.details = parts[1];
			}
		} else {
			throw std::runtime_error("unknown OS");
		}
		
	
	}
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
