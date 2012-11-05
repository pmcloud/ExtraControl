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

#ifndef DEVELER_COMMAND_LINE_GP_20120626
#define DEVELER_COMMAND_LINE_GP_20120626

#include "third-party/optparse/optparse.h"

#include <string>
#include <sstream>
#include <stdexcept>

template< typename T >
std::string help_and_default(const std::string & help_text, const T & default_value)
{
	std::stringstream sstr;
	sstr << help_text << " (default: " << default_value << ")";
	return sstr.str();
}

// gets the value of an option in a more type-safe manner
// than what the library offers
// 
class option_getter
{
public:
	class error : public virtual std::runtime_error
	{
	public:
		explicit error(const char * p)
			: std::runtime_error(p)
		{
		}
	};
public:
	option_getter(Options & opt) : _opt(opt)
	{
	}

	template< typename T >
	bool to_var(const std::string & option_name, T & var) const
	{
		if (!_opt.isSet(option_name))
			return false;

		std::istringstream sstr(_opt.asString(option_name));
		if ( !(sstr >> var) ||
			 !(sstr >> std::ws).eof()) {
			throw error("option_getter error");
		}
		return true;
	}
private:
	/* const */ Options & _opt; // TODO: patch OptParse for
	                            //       const correctness
};

#endif
// vim: set ft=cpp noet ts=4 sts=4 sw=4:

