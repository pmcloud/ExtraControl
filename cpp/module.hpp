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

#ifndef DEVELER_MODULE_GP_20120802
#define DEVELER_MODULE_GP_20120802

#include <string>
#include <iosfwd>

class Module
{
public:
	// NOTE: keep in sync with the type_names array
	enum Type { Internals, Plugins, UserModules };

	// constructs an invalid module
	Module();

	Module(Type t, const std::string & full_path, const std::string & version,
	       bool upgradeable, bool blocking, const std::string & alias_name);

	bool isValid() const;

	std::string fullPath() const;
	std::string version() const;
	bool isUpgradeable() const;
	bool isBlocking() const;
	std::string alias() const;
	Type type() const;
	std::string typeString() const;

	static Module getModuleFromAlias(const std::string & alias);

private:
	static const char * const type_names[];

	Type _type;
	std::string _full_path;
	std::string _version;
	bool _upgradeable;
	bool _blocking;
	std::string _alias;
};

std::ostream &
operator <<(std::ostream & out, const Module & p);

#endif

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
