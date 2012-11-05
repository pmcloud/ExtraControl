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

#ifndef DEVELER_TOOLS_GP_20120716
#define DEVELER_TOOLS_GP_20120716

#include <string>
#include <cstdio>
#include "logging.hpp"
#ifdef _WIN32
#include <direct.h>
#define get_current_dir _getcwd
#else
#include <unistd.h>
#define get_current_dir getcwd
#endif

extern const std::string service_restart_file;
extern char exe_directory[FILENAME_MAX];

namespace tools
{
void get_exe_dir(char* path, size_t sz);

void writePidOrDie(const std::string& pid_fn);

void daemonizeOrDie(const std::string& pid_fn);

std::string getRootDirectory();

std::string getServiceVersion();

bool saveRestartGUID(const std::string& guid);

std::string getRestartGUID(bool rm);

}

#endif
