/**
 * \file
 * <!--
 * This file is part of BeRTOS.
 *
 * Bertos is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * As a special exception, you may use this file as part of a free software
 * library without restriction.  Specifically, if other files instantiate
 * templates or use macros or inline functions from this file, or you compile
 * this file and link it with other files to produce an executable, this
 * file does not by itself cause the resulting executable to be covered by
 * the GNU General Public License.  This exception does not however
 * invalidate any other reasons why the executable file might be covered by
 * the GNU General Public License.
 *
 * Copyright 2003,2004,2005,2006 Develer S.r.l. (http://www.develer.com/)
 * Copyright 2000 Bernie Innocenti <bernie@codewiz.org>
 *
 * -->
 *
 * \brief Log file manager (implementation)
 *
 * \version $Id: logger.cpp 576 2012-10-15 18:21:29Z stefano.brilli $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */
#include "logger.h"
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <time.h>

#ifdef _WIN32
	#define WIN32_LEAN_AND_MEAN
	#include <windows.h>
#else
	#include <sys/time.h>
#endif

using std::string;
using std::endl;

Logger* logger = NULL;

static const char *const level_table[] =
{
	"emerg",
	"alert",
	"crit",
	"err",
	"warning",
	"notice",
	"info",
	"debug"
};


// ctor
Logger::Logger(std::ostream &_output, const std::string &_prefix) :
	output(_output),
	prefix(_prefix),
	err_cnt(0),
	warn_cnt(0),
	rt_cnt(0),
	_verbosity(Logger::DEBUG)
{
	// nop
}

// vdtor
Logger::~Logger()
{
}

LogLine Logger::msg(Level level)
{
	return LogLine(*this, level);
}

void Logger::printLine(const LogLine &line)
{
	Level level = line.level();

	// Skip lines below current verbosity level
	if (!levelEnabled(level))
		return;

	// Fetch log message
	const string s = line.str();

	// Print each log line separately
	string::const_iterator first = s.begin(), last;
	while (first != s.end())
	{
		last = find(first, s.end(), '\n');
		printOneLine(level, string(first, last));

		// Handle lines not terminated with '\n'
		if (last == s.end())
			break;

		first = ++last; // Skip '\n'
	}
}

void Logger::printOneLine(Level level, const std::string &s)
{
	// Add date prefix
#ifdef _WIN32
	SYSTEMTIME tm;
	GetLocalTime(&tm);
	output << std::setfill('0')
		<< tm.wYear << "-"
		<< std::setw(2) << tm.wMonth << "-"
		<< std::setw(2) << tm.wDay << " "
		<< std::setw(2) << tm.wHour << ":"
		<< std::setw(2) << tm.wMinute << ":"
		<< std::setw(2) << tm.wSecond << "."
		<< std::setw(3) << tm.wMilliseconds << " "
		<< std::setfill(' ');
#else
	struct timeval tv;
	gettimeofday(&tv, 0);
	time_t now = tv.tv_sec;
	struct tm tm = *localtime(&now);
	output << std::setfill('0')
		<< tm.tm_year + 1900 << "-"
		<< std::setw(2) << tm.tm_mon + 1 << "-"
		<< std::setw(2) << tm.tm_mday << " "
		<< std::setw(2) << tm.tm_hour << ":"
		<< std::setw(2) << tm.tm_min << ":"
		<< std::setw(2) << tm.tm_sec << "."
		<< std::setw(3) << (tv.tv_usec / 1000) << " "
		<< std::setfill(' ');
#endif

	// Append severity and user message.
	output << level_table[level] << ": ";
	if (!prefix.empty())
		output << "[" << prefix << "] ";
	output << s << endl;
}

LogLine Logger::emerg()
{
	err_cnt++;
	return msg(EMERG);
}

LogLine Logger::alert()
{
	err_cnt++;
	return msg(ALERT);
}

LogLine Logger::crit()
{
	err_cnt++;
	return msg(CRIT);
}

LogLine Logger::err()
{
	err_cnt++;
	return msg(ERR);
}

LogLine Logger::warn()
{
	warn_cnt++;
	return msg(WARNING);
}

LogLine Logger::notice()
{
	return msg(NOTICE);
}

LogLine Logger::info()
{
	return msg(INFO);
}

LogLine Logger::debug()
{
	return msg(DEBUG);
}

LogLine Logger::runtime()
{
	rt_cnt++;
	return msg(INFO);
}

LogLine Logger::bug(const char *file, int line)
{
	rt_cnt++;
	return msg(CRIT) << "internal error (" << file << ":" << line << ")" << std::endl;
}

LogLine Logger::dump(const void *data, size_t len)
{
	return msg() << hexDump(data, len) << std::flush;
}

void Logger::nomem()
{
	err_cnt++;
	msg(EMERG) << "virtual memory exhausted" << std::endl;
}


std::string hexDump(const void *data, size_t len)
{
	const int BYTES_PER_ROW = 16; // Number of bytes per row
	const int PACKING = 4; // Number of bytes to pack together

	std::stringstream out;
	char ascii_buf[BYTES_PER_ROW + 1];
	unsigned char byte;
	size_t i;
	int row;

	out << std::hex << std::setfill('0') << std::uppercase;

	for (i = 0; i < len; ++i)
	{
		row = static_cast<int>(i % BYTES_PER_ROW);
		byte = (reinterpret_cast<const unsigned char *>(data))[i];

		// NOTE: setw() resets itself each time
		out << std::setw(2) << static_cast<unsigned int>(byte);

		ascii_buf[row] = isprint(byte) ? byte : '.';

		// Print ASCII values on each row and on last iteration
		if ((row == BYTES_PER_ROW - 1) || (i == len - 1))
		{
			// Last iteration?
			if (i == len - 1)
			{
				int tail = static_cast<int>(len % BYTES_PER_ROW);
				int pad_bytes = BYTES_PER_ROW - tail;

				pad_bytes %= BYTES_PER_ROW;	// handle case where pad_bytes == BYTES_PER_ROW
				pad_bytes *= 2;
				pad_bytes += BYTES_PER_ROW/PACKING - tail/PACKING;
				if (tail % PACKING != 0)
					pad_bytes--;

				// Add padding
				for (int j = 0; j < pad_bytes; ++j)
					out << " ";
			}

			ascii_buf[row + 1] = '\0';
			out << "  " << ascii_buf << std::endl;
		}
		else if (i % PACKING == PACKING - 1)
			out << ' ';
	}

	// out << std::dec << std::setw(0) << std::setfill(' ') << std::lowercase;

	return out.str();
}
