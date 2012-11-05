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

#include "utils/launchprocess.hpp"
#include <cstdlib>
#include <string>
#include <iostream>
#include <ostream>

const std::string program_name = "exec";
const std::string sub_command = "script";

void print_usage()
{
	std::cerr << "usage: " << program_name << ' ' << sub_command << " NAME_AND_ARGS" << std::endl;
}


int main(int argc, char *argv[])
{
	const int min_arg_count = 3;
	if (argc < min_arg_count || std::string(argv[1]) != sub_command) {
		print_usage();
		exit(EXIT_FAILURE);
	}

	const std::string script_name = argv[min_arg_count - 1];
	std::string arguments;
	for (int i = min_arg_count; i < argc; ++i) {
		// TODO: doesn't handle arguments containing spaces
		arguments += argv[i];
		arguments += " ";
	}
	const LaunchResult result = launchProcess(script_name, arguments, true);
	return result.result == LaunchResult::success
		? EXIT_SUCCESS
		: EXIT_FAILURE;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
