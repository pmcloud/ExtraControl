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

#include "commandline.hpp"
#include "logging.hpp"
#include "third-party/optparse/optparse.h"
#include "serialwatcher.hpp"
#include "tools.hpp"

#include <string>
#include <cstdlib>
#include <exception>

const std::string application_name("serclient");
const std::string service_restart_file("serclient.service");

int main(int argc, char * argv[])
{
	logger = new FileLogger(application_name + ".log", application_name);
	tools::get_exe_dir(exe_directory, sizeof(exe_directory));
	// Default values for command-line options (these ones come into
	// effect if the corresponding options are NOT specified)
	// -------------------------------------------------------------
    int daemonize = 0;
    std::string pid = "pid";
	int baud_rate = 57600;
	int byte_size = 8;
	// note that CTB uses an int for the port parity; it would be nicer
    // to have something more type-safe here
	int parity = 0;
	int stop_bits = 1;
	int command_timeout = 20;
	bool stop_flag = false;

	Options opt;
	std::string port;
	opt.addOption("", "--port",     ::help_and_default("serial port", "<none>"), OPT_NEEDARG, NULL);
	opt.addOption("", "--baudrate", ::help_and_default("serial port baudrate", baud_rate),  OPT_NEEDARG, NULL);
	opt.addOption("", "--bytesize", ::help_and_default("serial port bytesize", byte_size),  OPT_NEEDARG, NULL);
	opt.addOption("", "--parity",   ::help_and_default("serial port parity", "none"),       OPT_NEEDARG, NULL);
	opt.addOption("", "--stopbits", ::help_and_default("serial port stopbits", stop_bits),  OPT_NEEDARG, NULL);

	//opt.addOption("", "--exec", "exec any python script using the current interpreter"); //TODO: check this
	opt.addOption("", "--command-timeout",
		                            ::help_and_default("debug: command execution timeout in seconds", command_timeout), OPT_NEEDARG, NULL);
	opt.addOption("", "--debug-command",
		                            ::help_and_default("debug: send a command packet", "none"), OPT_NEEDARG, NULL);
	opt.addOption("", "--send-raw", ::help_and_default("send raw packet", "none"),              OPT_NEEDARG, NULL);
	opt.addOption("", "--log",      ::help_and_default("log file", "stdout"),                   OPT_NEEDARG, NULL);
    opt.addOption("", "--daemon",   ::help_and_default("daemonize", daemonize),                 OPT_NEEDARG, NULL);
    opt.addOption("", "--pid",      ::help_and_default("PID file path", pid),                   OPT_NEEDARG, NULL);
	opt.addOption("", "--help",     "show this help and exit\n", OPT_HELP, NULL);

	Parser p;
	if (p.parse(argc, argv, opt) != E_OK) {
        fprintf(stderr, "Error parsing the command line\n");
        return EXIT_FAILURE;
	}

	option_getter getter(opt);
	getter.to_var(_T("--port"), port);
	getter.to_var(_T("--baudrate"), baud_rate);
	getter.to_var(_T("--bytesize"), byte_size);
	getter.to_var(_T("--parity"), parity);
	getter.to_var(_T("--stopbits"), stop_bits);
    getter.to_var(_T("--daemon"), daemonize);
    getter.to_var(_T("--pid"), pid);
	command_timeout *= 1000; // sec to msec

    if (port.empty()) // Check for required params
    {
        fprintf(stderr, "Missing one or more required options: see %s --help for usage\n", argv[0]);
        exit(EXIT_FAILURE);
    }

	// TODO: manage exec_script?

	// TODO: encapsulate

	try {
		SerialWatcher watcher(port, command_timeout);

        if (daemonize != 0)
        {
            tools::daemonizeOrDie(pid);
        }
        else if (!pid.empty())
        {
            tools::writePidOrDie(pid);
        }
		watcher.start(baud_rate, byte_size, parity, stop_bits, stop_flag);
	} catch (const std::exception & ex) {
		logger->emerg()/*std::cerr*/ << "Terminating due to exception ("
            << ex.what() << ")" << std::endl;
		fprintf(stderr, "%s has been terminated due to an exception. See %s for details.\n", application_name.c_str(), static_cast<FileLogger*>(logger)->filename().c_str());
		return EXIT_FAILURE;
	}

}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
