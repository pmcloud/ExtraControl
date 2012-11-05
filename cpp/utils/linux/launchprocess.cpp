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
#include "utils/launchprocess.hpp"
#include "utils/local_buffer.hpp"

#include <stdexcept>
#include <sstream>
#include <vector>
#include <string>
#include <cstring>
#include <cstddef>
#include <ctime>
#include <cassert>

#include <unistd.h>
#include <errno.h>
#include <sys/wait.h>
#include <wordexp.h>
#include <signal.h>
#include <stdio.h>// TEMP!!!
//#include <stdlib.h>
#include <iostream> // gps temp!!!

class Pipe
{
public:
	Pipe()
	{
		int file_descr[2];
		if (pipe(file_descr) != 0) {
			throw std::runtime_error("cannot create pipe");
		}
		_read_fd = file_descr[0];
		_write_fd = file_descr[1];
	}

	Pipe(int read_fd, int write_fd)
		:	_read_fd( (assert(read_fd  != -1), read_fd)),
		  _write_fd((assert(write_fd != -1), write_fd))
	{
	}

	~Pipe()
	{
		close(_write_fd);
		close(_read_fd);
	}

	std::vector<char> read(std::size_t count)
	{
		assert(count > 0);

		std::vector<char> buffer(count);
		const ssize_t res = ::read(_read_fd, &buffer[0], count);
		if (res < 0) {
			throw std::runtime_error("Pipe::read() failed");
		}

		buffer.resize(res);
		return buffer;
	}

	int readDescriptor() const
	{
		return _read_fd;
	}

	int writeDescriptor() const
	{
		return _write_fd;
	}

private:
	int _read_fd;
	int _write_fd;
	
};

class WordExp
		:	public wordexp_t
{
public:
	explicit WordExp(const char * line, int offset = 1)
	{
		we_offs = offset;
		if (wordexp(line, this, WRDE_DOOFFS) != 0) { // TODO: tweak the flags
			throw std::runtime_error("can't expand arguments");
		}
	}
	size_t count() { return we_offs + we_wordc + 1; }
	char ** argv() const { return we_wordv; }

	~WordExp() { wordfree(this); }

private:
	// disable copy
	WordExp(const WordExp &);
	void operator =(const WordExp &);
};


LaunchResult launchProcess(const std::string & name, const std::string & arguments, bool capture_output, int timeout_in_seconds)
{
	LaunchResult launch_result;
	int exec_result = 0;


	Pipe pipe;
	const std::time_t start_time = time(NULL);
	const pid_t pid = fork();
	if (pid == -1)
	{
		throw std::runtime_error("fork failure [" + name + "]");
	}
	else if (pid == 0)
	{
		if (capture_output) {
			if (dup2(pipe.writeDescriptor(), STDOUT_FILENO) == -1) {
				throw std::runtime_error("cannot duplicate stdout file descriptor");
			}
			close(pipe.readDescriptor());
		}
		WordExp we(arguments.c_str());
		local_buffer<char> name_buf(new char[name.length() + 1]);
		::strcpy(name_buf.get(), name.c_str());
		we.we_wordv[0] = name_buf.get();
		exec_result = execv(name.c_str(), we.argv());
		exit(exec_result);
	}
	close(pipe.writeDescriptor());


	if (capture_output) {
		// While the timeout has not elapsed read in chunks from the pipe
		//
		std::string std_output;
		std::time_t elapsed = 0;
		while ((elapsed = std::time(NULL) - start_time) < timeout_in_seconds) {
			std::vector<char> buffer;
			try {
				const std::size_t sz = 4 * 1024;
				buffer = pipe.read(sz);
				std_output.append(buffer.begin(), buffer.end());
				if (buffer.size() < sz) {
					break;
				}
			} catch (const std::exception & ex) {
				break;
			}
		}
		launch_result.result = LaunchResult::success;
		launch_result.output = std_output;
                launch_result.exit_code = 0;
	} else {
		int status;
		pid_t w_pid = waitpid(pid, &status, WUNTRACED | WNOHANG);
		std::time_t elapsed = 0;
		while ( (w_pid != pid) &&
				(elapsed = std::time(NULL) - start_time) < timeout_in_seconds) {
			w_pid = waitpid(pid, &status, WUNTRACED | WNOHANG);
		}
		if (!WIFEXITED(status) && elapsed >= timeout_in_seconds)
		{
			kill(pid, SIGKILL);
			launch_result.exit_code = 1;
			launch_result.result = LaunchResult::timeout;
		}
		else
		{
			launch_result.result = LaunchResult::success;
			launch_result.output = "";
			launch_result.exit_code = WEXITSTATUS(status);
		}
	}
	return launch_result;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
