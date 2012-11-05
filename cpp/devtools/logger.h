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
 * \brief Log file manager (interface)
 *
 * \version $Id: logger.h 576 2012-10-15 18:21:29Z stefano.brilli $
 * \author Bernie Innocenti <bernie@codewiz.org>
 */
#ifndef LOGGER_H
#define LOGGER_H

#if defined (_MSC_VER) && (_MSC_VER >= 1000)
#pragma once
#endif

// STL headers
#include <string>
#include <vector>
#include <ostream>
#include <sstream>

// This commonly used definition clashes with Log::DEBUG
#ifdef DEBUG
#undef DEBUG
#endif

// fwd decl
class LogLine;
class Logger;
extern Logger* logger;

/**
 * \brief Encapsulate application logging for errors and diagnostic output.
 *
 * Error messages are categorized by the 7 syslog levels.
 *
 * Usually a single logger instance shall be created at application
 * startup time and passed around to all subsystems that can generate
 * diagnostic output.
 *
 * The Logger instance tracks the total number of errors ever occurred,
 * which can be used to conditionally abort program execution.
 *
 * This base class is not very useful by itself.  You usually need
 * one of its subclasses such as FileLogger to pipe logs to some physical
 * destination.
 *
 * Here's a simple "hello world" application using the logger:
 *
 * \code
 *		int main(void)
 *		{
 *			FileLogger my_log("hello.log");
 *
 *			my_log.warn() << "Hello, heartlings!";
 *		}
 * \endcode
 *
 * \see FileLogger SyslogLogger
 * \todo Add a loglevel mask and reimplement verbosity on top of it
 */
class Logger
{
// definitions
public:
	/**
	 * \name Syslog-like importance levels
	 * \{
	 */
	enum Level
	{
		EMERG,   ///< System is unusable.
		ALERT,   ///< Action must be taken immediately.
		CRIT,    ///< Critical conditions.
		ERR,     ///< Error conditions.
		WARNING, ///< Warning conditions.
		NOTICE,  ///< Normal, but significant, condition.
		INFO,    ///< Informational message (default level).
		DEBUG,   ///< Debug-level message.

		LEVEL_CNT
	};
	/* \} */


// construction
public:
	/**
	 * \brief Construct a Logger using an open output stream.
	 *
	 * \note	Trimming an ostream is not possible.
	 *
	 * \arg file    Output stream where all messages are redirected,
	 *		usually open in append mode.
	 *		This constructor takes a reference to the parameter.
	 *		The provided stream might be initialized or opened
	 *		at a later time, but \b before calling Logger::log().
	 * \arg prefix  String to prepend to every log message, usually
	 *		the name of the application or subsystem.
	 */
	explicit Logger(std::ostream &file, const std::string &prefix = "");

	// vdtor
	virtual ~Logger();

// derived class interface
protected:
	// def ctor
	Logger();


// public methods
public:
	/// Return the log output stream (overridable).
	virtual LogLine msg(Level level = INFO);

	/// Output an emergency message.
	LogLine emerg();

	/// Output an alert message.
	LogLine alert();

	/// Output a critical message.
	LogLine crit();

	/// Output an error message.
	LogLine err();

	/// Output a warning message.
	LogLine warn();

	/// Output a notice message.
	LogLine notice();

	/// Output an informative message.
	LogLine info();

	/// Output a debug message.
	LogLine debug();

	/// Output a run-time error message.
	LogLine runtime();

	/// Output an internal consistency error message.
	LogLine bug(const char *file, int line);

	/// Report memory allocation failure.
	void nomem();

	/// Print hex-dump of a data buffer.
	LogLine dump(const void *data, size_t len);

// public accessors
	/**
	 * Return the current verbosity level.
	 *
	 * The logger filters out all message levels above
	 * the current verbosity.
	 */
	Level verbosity() const { return _verbosity; }

	/**
	 * Set the current verbosity to \a level.
	 *
	 * \see verbosity
	 */
	void setVerbosity(Level level) { _verbosity = level; }

	/// Return true if the \a level is enabled for logging.
	bool levelEnabled(Level level) const { return level <= verbosity(); }

// public data members
public:
	/// Output stream.
	std::ostream &output;

	/// Log prefix.
	std::string prefix;

	/// Errors count.
	int err_cnt;

	/// Warnings count.
	int warn_cnt;

	/// Run-time errors count.
	int rt_cnt;

	/// Output a log line to the output device (splits multiple lines).
	virtual void printLine(const LogLine &line);

	/// Output a log line to the output device (one line at a time).
	virtual void printOneLine(Level level, const std::string &msg);

// private data members
private:
	/// Log messages below this level are filtered out.
	Level _verbosity;

};

#define	LOGLEVEL_EMERG    0
#define	LOGLEVEL_ALERT    1
#define	LOGLEVEL_CRIT     2
#define	LOGLEVEL_ERR      3
#define	LOGLEVEL_WARNING  4
#define	LOGLEVEL_NOTICE   5
#define	LOGLEVEL_INFO     6
#define	LOGLEVEL_DEBUG    7

/**
 * \def LOGGER_BUILD_VERBOSITY
 *
 * Specify a hard verbosity limit for the LOG_MSG() macro.
 *
 * Messages below this level are optimized away at
 * compile-time to reduce the binary size.
 *
 * \see LOG_MSG
 */
#ifndef LOGGER_BUILD_VERBOSITY
	#ifdef _DEBUG
		#define LOGGER_BUILD_VERBOSITY LOGLEVEL_DEBUG
	#else
		#define LOGGER_BUILD_VERBOSITY LOGLEVEL_WARNING
	#endif
#endif

#define LOGGER_PP_CAT(x,y)   LOGGER_PP_CAT__(x,y)
#define LOGGER_PP_CAT__(x,y) x ## y

/**
 * Log on \a log with the specified \a level.
 *
 * This macro is meant to optimize away the cost of formatting log
 * messages when not needed.
 *
 * \code
 *   LOG_EMERG(mylogger()) << "A dog has " << 4 << " legs.";
 * \endcode
 *
 * \see LOGGER_BUILD_VERBOSITY
 */
#define LOG_MSG(log, level) \
	if ((LOGGER_PP_CAT(LOGLEVEL_, level) > LOGGER_BUILD_VERBOSITY) \
			|| !log.levelEnabled(Logger::level)) \
	{/*nop*/} \
	else log.msg(Logger::level) /* user code appended here! */

#define	LOG_EMERG(logger)   LOG_MSG(logger, EMERG)
#define	LOG_ALERT(logger)   LOG_MSG(logger, ALERT)
#define	LOG_CRIT(logger)    LOG_MSG(logger, CRIT)
#define	LOG_ERR(logger)     LOG_MSG(logger, ERR)
#define	LOG_WARNING(logger) LOG_MSG(logger, WARNING)
#define	LOG_NOTICE(logger)  LOG_MSG(logger, NOTICE)
#define	LOG_INFO(logger)    LOG_MSG(logger, INFO)
#define	LOG_DEBUG(logger)   LOG_MSG(logger, DEBUG)

/**
 * A pending log line, returned by value from Logger::msg() and friends.
 *
 * There's some black magic going on that deserves a bit
 * of explanation: to output log lines transparently, we
 * rely on automatic destruction of the temporary LogLine
 * instance returned by Logger::msg() and similar functions.
 *
 * LogLine accumulates output in an internal stringstream
 * object, usually by means of calls to standard output
 * operators (operator<<).  The destructor forwards the
 * contents of the line buffer to the Logger, effectively
 * displaying the log line.
 *
 * Copies of LogLine may be made along the return path
 * of Logger::msg() wrappers.  To avoid printing spurious
 * log lines, we invalidate the original object in the
 * copy constructor, imitating auto_ptr<> semantics.
 *
 * Another problem we must deal with is that LogLine
 * objects become temporary objects when returned to
 * clients.  Because temporaries decay to const, regular
 * output operators wouldn't work on LogLine objects
 * directly.  Hence, we declare our data members as
 * mutable and redefine output operators in LogLine
 * to work with a constant object.
 *
 * \see Logger::msg()
 */
class LogLine
{
	typedef std::ostringstream Base;
public:
	LogLine(Logger &_logger, Logger::Level lvl) :
		logger(&_logger),
		_level(lvl)
	{ /* nop */ }

	// copy ctor
	LogLine(const LogLine &other) :
		logger(other.logger),
		_level(other._level)
	{
		stream << other.str();

		// Invalidate original, auto_ptr<>-like behavior
		other.logger = 0;
	}

	~LogLine()
	{
		if (logger)
			logger->printLine(*this);
	}

	std::string str() const
	{
		return stream.str();
	}

	/// Forward output to the embedded string.
	template<typename T>
	const LogLine &operator<<(const T &value) const
	{
		stream << value;
		return *this;
	}

	/// This overload handles function pointers such as std::endl.
	const LogLine &operator<<(std::ostream & (*pf)(std::ostream &)) const
	{
		stream << pf;
		return *this;
	}

	/// This overload handles function pointers such as std::hex.
	const LogLine &operator<<(std::ios_base & (*pf)(std::ios_base &)) const
	{
		stream << pf;
		return *this;
	}

	/// Return the priority level of the message.
	Logger::Level level() const { return _level; }

protected:
	mutable std::ostringstream stream;
	mutable Logger *logger;
	Logger::Level _level;
};

/**
 * Convert a raw buffer to a formatted string containing the
 * pretty printed hexadecimal dump for debug purposes.
 */
std::string hexDump(const void *data, size_t len);


struct _Sethex { int w; };

/**
 * Handy manipulator to print 0-padded hexadecimal numbers.
 *
 * \code
 *	uint32_t foo = 0xBADF00D;
 *	log.info() << "foo=" << sethex(8) << foo << sethex(0) << endl;
 * \endcode
 *
 * Prints:
 * \code
 *	foo=0x0BADF00D;
 * \endcode
 */
inline _Sethex sethex(int width)
{
	_Sethex x;
	x.w = width;
	return x;
}

template<typename _CharT, typename _Traits>
std::basic_ostream<_CharT,_Traits>&
operator<<(std::basic_ostream<_CharT,_Traits>& os, _Sethex x)
{
	if (x.w >= 0)
	{
		// 2 == strlen("0x")
		os.width(x.w + 2);
		os.fill(' ');
		os.setf(std::ios_base::hex | std::ios_base::showbase /*| std::ios_base::uppercase*/,
			std::ios_base::basefield | std::ios_base::showbase /*| std::ios_base::uppercase*/);
	}
	else
	{
		os.width(0);
		os.fill(' ');
		os.setf(std::ios_base::dec,
			std::ios_base::basefield | std::ios_base::showbase /*| std::ios_base::uppercase*/);
	}

	return os;
}

template <class T1>
std::string tie(T1 t1)
{
	std::ostringstream ss;
	ss << "(";
	ss << t1;
	ss << ")";
	return ss.str();
}

template <class T1>
std::string tie(const std::vector<T1> &t1)
{
	std::ostringstream ss;
	ss << "(";
	if (t1.size() > 0)
		ss << t1[0];
	for (unsigned i = 1; i < t1.size(); ++i)
		ss << ", " << t1[i];
	ss << ")";
	return ss.str();
}

template <class T1, class T2>
std::string tie(T1 t1, T2 t2)
{
	std::ostringstream ss;
	ss << "(";
	ss << t1;
	ss << ", ";
	ss << t2;
	ss << ")";
	return ss.str();
}

template <class T1, class T2, class T3>
std::string tie(T1 t1, T2 t2, T3 t3)
{
	std::ostringstream ss;
	ss << "(";
	ss << t1;
	ss << ", ";
	ss << t2;
	ss << ", ";
	ss << t3;
	ss << ")";
	return ss.str();
}

template <class T1, class T2, class T3, class T4>
std::string tie(T1 t1, T2 t2, T3 t3, T4 t4)
{
	std::ostringstream ss;
	ss << "(";
	ss << t1;
	ss << ", ";
	ss << t2;
	ss << ", ";
	ss << t3;
	ss << ", ";
	ss << t4;
	ss << ")";
	return ss.str();
}

template <class T1, class T2>
std::string progress(T1 t1, T2 t2)
{
	std::ostringstream ss;
	ss << "[" << t1 << "/" << t2 << "]";
	return ss.str();
}

template <class T1>
std::string quote(T1 t1)
{
	std::ostringstream ss;
	ss << "\"" << t1 << "\"";
	return ss.str();
}

#endif // LOGGER_H
