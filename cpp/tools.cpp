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
#include "tools.hpp"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <fstream>
#ifdef _WIN32
#include <windows.h>
#else
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#endif

char exe_directory[FILENAME_MAX];

namespace tools
{
#ifdef _WIN32
void daemonizeOrDie(const std::string& pid_fn)
{
}

void writePidOrDie(const std::string& pid_fn)
{
	// Not needed on WIN32
}

void get_exe_dir(char* path, size_t sz)
{
    HMODULE hModule = GetModuleHandleA(NULL);
    GetModuleFileNameA(hModule, path, sz);
    char* last_slash = strrchr(path, '\\');
	if (last_slash != NULL)
		*last_slash = '\0';
}

#else

#ifdef __linux__
void get_exe_dir(char* path, size_t sz)
{
	char fn[256];
	sprintf(fn, "/proc/%d/exe", getpid());
	readlink(fn, path, sz);
	char* last_slash = strrchr(path, '/');
	if (last_slash != NULL)
		*last_slash = '\0';
}
#else
void get_exe_dir(char* path, size_t sz)
{
	char fn[256];
	system("mkdir /tmp/proc");
	system("mount -t procfs proc /tmp/proc");
	sprintf(fn, "/tmp/proc/%d/file", getpid());
	readlink(fn, path, sz);
	system("umount /tmp/proc");
	system("rm -rf /tmp/proc");
	char* last_slash = strrchr(path, '/');
	if (last_slash != NULL)
		*last_slash = '\0';
}
#endif

void daemonizeOrDie(const std::string& pid_fn)
{
    pid_t p = fork();
    if (p < 0)
    {
        perror("Fork #1 failed");
        exit(1);
    }
    if (p > 0)
        exit(0); // Exits from the parent

    if (chdir("/") < 0 || setsid() < 0)
    {
        perror("Chdir or setsid failed");
        exit(1);
    }
    umask(0);

    p = fork();
    if (p < 0)
    {
        perror("Fork #2 failed");
        exit(1);
    }
    if (p > 0)
        exit(0); // Exits from the parent

    writePidOrDie(pid_fn);

    int fd = open("/dev/null", O_RDWR);
    dup2(fd, 0);
    dup2(fd, 1);
    dup2(fd, 2);
}

void writePidOrDie(const std::string& pid_fn)
{
    FILE* pid_fd = fopen(pid_fn.c_str(), "w+");
    if (pid_fd == NULL) {
        perror("Write of PID failed");
        exit(1);
    }
    fprintf(pid_fd, "%d\n", getpid());
    fclose(pid_fd);
}
#endif



std::string getServiceVersion()
{
    const std::string version_file = "";
    const std::string path = getRootDirectory() + "/../serclient.version";

    std::ifstream f(path.c_str());
    if (!f.fail()) {
        std::string result;
        std::getline(f, result);
        if (!f.fail()) {
            return result;
        }
    }

    return ""; // TODO: the Python version does this; is that ok?
}

bool saveRestartGUID(const std::string& guid)
{
    assert(guid.size() > 0);
    std::string fn = getRootDirectory() + "/" + service_restart_file;

#ifndef _WIN32
	struct stat sb;
	if (stat("/etc/version.freenas", &sb) != -1)
		system("mount -uw /");
#endif
    std::ofstream f(fn.c_str());
    bool success = !f.fail();
    if (success) {
        f << guid;
        f.close();
    }
#ifndef _WIN32
	if (stat("/etc/version.freenas", &sb) != -1)
		system("mount -ur /");
#endif
    return success;
}

std::string getRestartGUID(bool rm)
{
    std::string fn = getRootDirectory() + "/" + service_restart_file;
    std::string result = "";

    std::ifstream f(fn.c_str());
    if (!f.fail()) {
        std::getline(f, result);
        f.close();
    }
    return result;
}

std::string getRootDirectory()
{
	return ::exe_directory;
}

}
