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

#include "module.hpp"
#include "tools.hpp"


const char * const
Module::type_names[] = { "Internals", "Plugins", "UserModules" };

Module::Module()
	:	_type(Internals),
		_upgradeable(false),
		_blocking(false)
{
}

Module::Module(Module::Type t, const std::string & full_path, const std::string & version,
               bool upgradeable, bool blocking, const std::string & alias)
	:	_type(t),
		_full_path(full_path),
		_version(version),
		_upgradeable(upgradeable),
		_blocking(blocking),
		_alias(alias)
{
}

bool Module::isValid() const
{
	return !_full_path.empty();
}

std::string Module::fullPath() const
{
	return _full_path;
}

std::string Module::version() const
{
	return _version;
}

bool Module::isUpgradeable() const
{
	return _upgradeable;
}

bool Module::isBlocking() const
{
	return _blocking;
}

std::string Module::alias() const
{
	return _alias;
}

Module::Type Module::type() const
{
	return _type;
}

std::string Module::typeString() const
{
	return type_names[static_cast<int>(_type)];
}

// TODO: browse filesystem for real executables
Module Module::getModuleFromAlias(const std::string & alias)
{
	if (alias == "restart") {
        return Module(Internals, tools::getRootDirectory() + "/internals/restart", "1.0", false, true, "restart");
	} else if (alias == "modulemng") {
        return Module(Internals, tools::getRootDirectory() + "/internal/modulemng", "1.0", false, false, "modulemng");
	} else if (alias == "osinfo") {
        return Module(Plugins, tools::getRootDirectory() + "/plugins/osinfo", "1.0", true, false, "osinfo");
	} else {
		return Module();
	}
}

