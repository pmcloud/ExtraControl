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

#include "packet.hpp"
#include <cstddef>
#include <ostream>
#include <cctype>

std::ostream &
operator <<(std::ostream & out, const Packet & p)
{
	// do not output more than limit body characters; also give
	// a visual hint for truncation
	//
	const std::size_t limit = 300;
	const std::string limited_body = p.body().length() > limit
		? p.body().substr(0, limit) + " ..."
		: p.body();

	return out << "Packet("
	      "guid=" << p.guid()
	    << ", type=" << Packet::commandTypeToString(p.command()) // TODO: improve?
	    << ", body=" << limited_body
	    << ", number =" << p.number()
	    << ", count =" << p.count()
	    << ")";
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
