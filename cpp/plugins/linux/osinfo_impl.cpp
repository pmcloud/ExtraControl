// ===========================================================================
//
//	Copyright 2012 xxxxxxxx - TODO
//	License: TODO
// ___________________________________________________________________________

#include "osinfo.hpp"
#include "utils/count.hpp"
#include "utils/launchprocess.hpp"
#include "utils/canreadfile.hpp"

#include <string>
#include <fstream>
#include <stdexcept>
#include <cstddef>
#include <utility>
#include <sstream>

// info files, for when we don't have lsb_release or can't run it successfully
//
const struct entry { const char * distro; const char * file; }
    distro_map[] =
        { {"Redhat",    "/etc/redhat-release"}, // includes CentOS
          {"OpenFiler", "/etc/distro-release"} };


std::pair<std::string, std::string> parseLsbLine(const std::string & line)
{
	const std::string sep= ":\t";
	const std::string::size_type sep_len = sep.length();
	const std::string::size_type pos = line.find(sep);
	if (pos != line.npos && (pos + sep_len) < line.size()) {
		return std::make_pair(line.substr(0, pos),
		                      line.substr(pos + sep_len));
	} else {
		throw std::runtime_error("parsing error");
	}
}

// Strategy:
//
// First try launching lsb_release and parse its output (which has a documented form).
// If that fails try reading a suitable file from /etc/.
//
info getOSInfo()
{
	info result;

	try {
		const LaunchResult & lr = launchProcess("/usr/bin/lsb_release", "-irc", true);
		if (lr.result == LaunchResult::success) {

			std::istringstream iss(lr.output);
			std::string line;
			while (std::getline(iss, line)) {
				try {
					const std::pair<std::string, std::string> fields = parseLsbLine(line);
					if (fields.first == "Distributor ID") {
						result.name = fields.second;
					}
					if (fields.first == "Release") {
						result.version = fields.second;
					}
					if (fields.first == "Codename") {
						result.details = fields.second;
					}
				} catch (const std::exception & ex) {
					// TODO: log error parsing LSB file
				}
			}

			return result;
		}
	} catch (const std::exception & ex) {
		// probably not LSB compliant: go on and try with the files
	}


	bool found = false;
	std::string filename;
	for (std::size_t i = 0; i < count(distro_map); ++i) {
		filename = distro_map[i].file;
		if (canReadFile(filename)) {
			found = true;
			break;
		}
	}

	if (!found) {
		throw std::runtime_error("unknown OS distribution");
	}


	std::ifstream f(filename.c_str());
	if (!f.fail()) {
		// assume the format is "distro_name release version"
		std::string tmp;
		f >> result.name;
		f >> tmp;
		if (tmp == "release") {
			f >> result.version >> result.details;
		} else {
			result.version = tmp;
			f >> result.details;
		}
	}

	return result;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
