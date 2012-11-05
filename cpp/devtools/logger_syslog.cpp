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
 * Copyright 2006 Develer S.r.l. (http://www.develer.com/)
 *
 * -->
 *
 * \brief Syslog output for Logger (implementation)
 *
 * \version $Id: logger_syslog.cpp 412 2012-07-20 13:07:28Z gennaro.prota $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */

#include "logger_syslog.h"

#include <stdio.h>
#include <fstream>
#include <cassert>

// ctor
SyslogLogger::SyslogLogger(const std::string &pfx, int facility) :
	Logger(*static_cast<std::ostringstream *>(NULL), pfx) // WARNING: out is not used
{
	ident = pfx;
	::openlog(ident.c_str(), LOG_PID, facility);
}

// dtor
SyslogLogger::~SyslogLogger()
{
	::closelog();
}

void SyslogLogger::printOneLine(Level level, const std::string &s)
{
	syslog(static_cast<int>(level), "%s", s.c_str());
}


#include <map>

#ifndef countof
	/// Return the number of elements in a static array
#	define countof(a) (sizeof(a) / sizeof(*(a)))
#endif

typedef std::pair<const char *, int> FacilityToId;
typedef std::map<std::string, int>   FacilityMap;

static FacilityToId facility_map_init[] =
{
	FacilityToId("auth", LOG_AUTH),
	FacilityToId("authpriv", LOG_AUTHPRIV),
	FacilityToId("cron", LOG_CRON),
	FacilityToId("daemon", LOG_DAEMON),
	FacilityToId("ftp", LOG_FTP),
	FacilityToId("kern", LOG_KERN),
	FacilityToId("lpr", LOG_LPR),
	FacilityToId("mail", LOG_MAIL),
	FacilityToId("news", LOG_NEWS),
	FacilityToId("security", LOG_AUTH),		/* DEPRECATED */
	FacilityToId("syslog", LOG_SYSLOG),
	FacilityToId("user", LOG_USER),
	FacilityToId("uucp", LOG_UUCP),
	FacilityToId("local0", LOG_LOCAL0),
	FacilityToId("local1", LOG_LOCAL1),
	FacilityToId("local2", LOG_LOCAL2),
	FacilityToId("local3", LOG_LOCAL3),
	FacilityToId("local4", LOG_LOCAL4),
	FacilityToId("local5", LOG_LOCAL5),
	FacilityToId("local6", LOG_LOCAL6),
	FacilityToId("local7", LOG_LOCAL7),
};

static FacilityMap facility_map(facility_map_init, facility_map_init + countof(facility_map_init));


int SyslogLogger::facilityId(const std::string &name)
{
	FacilityMap::iterator it;
	if ((it = facility_map.find(name)) != facility_map.end())
		return it->second;

	return -1;
}

