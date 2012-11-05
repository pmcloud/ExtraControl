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
 * Copyright 2003,2004,2005 Develer S.r.l. (http://www.develer.com/)
 * Copyright 2000 Bernie Innocenti <bernie@codewiz.org>
 *
 * -->
 *
 * \brief Log file manager (interface)
 *
 * \version $Id: logger_file.h 542 2012-10-09 12:41:50Z gennaro.prota $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */

#ifndef LOGGER_FILE_H
#define LOGGER_FILE_H

#if defined (_MSC_VER) && (_MSC_VER >= 1000)
#pragma once
#endif

#include "logger.h"

#include <fstream>

/**
 * Log to a named file.
 */
class FileLogger : public Logger
{
public:
	/**
	 * \brief Construct a Logger writing to a named file.
	 *
	 * \note  Opening by name enables log rotation.
	 *
	 * \arg filename  Filename to use.
	 * \arg prefix  String to prepend to every log message, usually
	 *		the name of the application or subsystem.
	 */
	explicit FileLogger(const std::string &_filename /**< fdff */, const std::string &prefix = "");

// Base class overrides
	virtual LogLine msg(Level level = INFO);

	const std::string& filename() { return _filename; }

// Public attributes
public:
	/// Set the maximum size in bytes before splitting the log.
	size_t max_size;

private:
	/// Log file name (may be empty).
	std::string _filename;

	/// Our opened output stream.
	std::ofstream out;
};

#endif // LOGGER_FILE_H
