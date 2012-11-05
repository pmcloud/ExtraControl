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
 * Copyright 2003, 2004, 2005 Develer S.r.l. (http://www.develer.com/)
 * Copyright 2000 Bernie Innocenti <bernie@codewiz.org>
 *
 * -->
 *
 * \brief Log file manager (interface)
 *
 * \version $Id: logger_syslog.h 412 2012-07-20 13:07:28Z gennaro.prota $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */

#ifndef LOGGER_SYSLOG_H
#define LOGGER_SYSLOG_H

#if defined (_MSC_VER) && (_MSC_VER >= 1000)
#pragma once
#endif

#include "logger.h"

#include <syslog.h> // LOG_*


/**
 * Log to the syslog service.
 */
class SyslogLogger : public Logger
{
public:
	/**
	 * \brief Construct a Logger writing to the syslog service.
	 *
	 * \arg filename  Filename to use.
	 * \arg prefix  String to prepend to every log message, usually
	 *		the name of the application or subsystem.
	 */
	explicit SyslogLogger(const std::string &prefix = "", int facility = LOG_LOCAL6);

	~SyslogLogger();

// Base class overrides
	virtual void printOneLine(Level level, const std::string &msg);


	/// Helper to retrieve facility IDs from user friendly names
	static int facilityId(const std::string &name);

private:
	/// Ident string for openlog()
	std::string ident;
};

#endif // LOGGER_FILE_H
