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
 * \version $Id: logger_file.cpp 542 2012-10-09 12:41:50Z gennaro.prota $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */

#include "logger_file.h"

#include <stdio.h>
#include <fstream>

// ctor
FileLogger::FileLogger(const std::string &name, const std::string &pfx) :
	Logger(out, pfx), // WARNING: out is not yet constructed here!
	max_size(static_cast<size_t>(-1L)),
	_filename(name),
	out(_filename.c_str(), std::ios::out | std::ios::app)
{
	// nop
}


LogLine FileLogger::msg(Level level)
{
	// Rotate log
	if (static_cast<size_t>(output.tellp()) > max_size)
	{
		std::string old_file = _filename + ".old";
		out.close();
		// For Win32 only: old_file must must not exists in
		// order to be created by the rename function. So remove
		// it first.
		remove(old_file.c_str());
		rename(_filename.c_str(), old_file.c_str());
		out.open(_filename.c_str(), std::ios::app);
	}

	return Logger::msg(level);
}
