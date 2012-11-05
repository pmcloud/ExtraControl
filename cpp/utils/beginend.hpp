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
//
// Iteration helpers
// ___________________________________________________________________________

#ifndef DEVELER_BEGINEND_GP_20120713
#define DEVELER_BEGINEND_GP_20120713

#include <cstddef>

template<typename C>
typename C::iterator
begin(C & c)
{
	return c.begin();
}

template<typename C>
typename C::const_iterator
begin(const C & c)
{
	return c.begin();
}

template<typename C>
typename C::iterator
end(C & c)
{
	return c.end();
}

template<typename C>
typename C::const_iterator
end(const C & c)
{
	return c.end();
}

template<typename T, std::size_t n>
T *
begin(T (&a)[n])
{
	return a;
}

template<typename T, std::size_t n>
T *
end(T (&a)[n])
{
	return a + n;
}

#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
