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

#include <cstdio>
#include <cstdlib>
#include <string>
#include <iostream>
#include <ostream>

const std::string program_name = "remove";
const std::string sub_command = "usermodule";

void print_usage()
{
	std::cerr << "usage: " << program_name << ' ' << sub_command << " NAME" << std::endl;
}


int main(int argc, char *argv[])
{
	if (argc != 3 || std::string(argv[1]) != sub_command) {
		print_usage();
		exit(EXIT_FAILURE);
	}

	const std::string module_name = argv[2];


	if (std::remove(module_name.c_str()) != 0) {
		std::cerr << program_name << ": cannot remove '" << module_name << "'" << std::endl;
		return EXIT_FAILURE;
	}

	return EXIT_SUCCESS;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
