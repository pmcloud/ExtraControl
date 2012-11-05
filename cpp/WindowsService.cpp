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
#include "serialwatcher.hpp"
#include "tools.hpp"

#include <string>
#include <cstdlib>
#include <exception>

#include <windows.h>
#include <tchar.h>


#define SERVICE_NAME _T("SerialService")
#define SERVICE_INI _T("serclient.ini")

const std::string application_name("serclient");
const std::string service_restart_file("serclient.service");
SERVICE_STATUS serviceStatus;
SERVICE_STATUS_HANDLE serviceStatusHandle = 0;
bool stop_flag = false;

void WINAPI ServiceControlHandler( DWORD controlCode )
{
	switch ( controlCode )
	{
		case SERVICE_CONTROL_INTERROGATE:
			break;
		case SERVICE_CONTROL_SHUTDOWN:
		case SERVICE_CONTROL_STOP:
			serviceStatus.dwCurrentState = SERVICE_STOP_PENDING;
			SetServiceStatus( serviceStatusHandle, &serviceStatus );
            stop_flag = true;
			return;
		case SERVICE_CONTROL_PAUSE:
			break;
		case SERVICE_CONTROL_CONTINUE:
			break;
		default:
			break;
	}
	SetServiceStatus( serviceStatusHandle, &serviceStatus );
}

void WINAPI ServiceMain( DWORD /*argc*/, TCHAR* /*argv*/[] )
{
	// initialise service status
	serviceStatus.dwServiceType = SERVICE_WIN32;
	serviceStatus.dwCurrentState = SERVICE_STOPPED;
	serviceStatus.dwControlsAccepted = 0;
	serviceStatus.dwWin32ExitCode = NO_ERROR;
	serviceStatus.dwServiceSpecificExitCode = NO_ERROR;
	serviceStatus.dwCheckPoint = 0;
	serviceStatus.dwWaitHint = 0;

	serviceStatusHandle = RegisterServiceCtrlHandler( SERVICE_NAME, ServiceControlHandler );

	if ( serviceStatusHandle )
	{
		// service is starting
		serviceStatus.dwCurrentState = SERVICE_START_PENDING;
		SetServiceStatus( serviceStatusHandle, &serviceStatus );

		// running
		serviceStatus.dwControlsAccepted |= (SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN);
		serviceStatus.dwCurrentState = SERVICE_RUNNING;
		SetServiceStatus( serviceStatusHandle, &serviceStatus );

        tools::get_exe_dir(exe_directory, sizeof(exe_directory));
        std::string base_dir(exe_directory);
        
        logger = new FileLogger(base_dir + "\\serclient.log", application_name);
        
        std::string ini_path(base_dir);
        ini_path += "\\";
        ini_path += SERVICE_INI;
        
        int baud_rate = GetPrivateProfileInt(SERVICE_NAME, _T("baud_rate"), 57600, ini_path.c_str());
        int byte_size = GetPrivateProfileInt(SERVICE_NAME, _T("byte_size"), 8, ini_path.c_str());
        int parity = GetPrivateProfileInt(SERVICE_NAME, _T("parity"), 0, ini_path.c_str());
        int stop_bits = GetPrivateProfileInt(SERVICE_NAME, _T("stop_bits"), 1, ini_path.c_str());
        int command_timeout = GetPrivateProfileInt(SERVICE_NAME, _T("command_timeout"), 20, ini_path.c_str());
    
        TCHAR port[FILENAME_MAX];
        GetPrivateProfileString(SERVICE_NAME, _T("port"), _T("COM1"), port, sizeof(port), ini_path.c_str());
        
        SerialWatcher watcher(std::string(port), command_timeout);
        watcher.start(baud_rate, byte_size, parity, stop_bits, stop_flag);
    
		// service was stopped
		serviceStatus.dwCurrentState = SERVICE_STOP_PENDING;
		SetServiceStatus( serviceStatusHandle, &serviceStatus );
		serviceStatus.dwControlsAccepted &= ~(SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN);
		serviceStatus.dwCurrentState = SERVICE_STOPPED;
		SetServiceStatus( serviceStatusHandle, &serviceStatus );
	}
}

void RunService()
{
	SERVICE_TABLE_ENTRY serviceTable[] =
	{
		{ SERVICE_NAME, ServiceMain },
		{ 0, 0 }
	};

	if (StartServiceCtrlDispatcher( serviceTable ) == 0) // Not run as a service
    {
        printf("This program must be run as a Service\n"
               "Available options are:\n"
               "    install\n"
               "    uninstall\n"
               "    start\n"
               "    stop\n"
               "    query\n");
    }
}

void InstallService()
{
	SC_HANDLE serviceControlManager = OpenSCManager( 0, 0, SC_MANAGER_CREATE_SERVICE );

	if ( serviceControlManager )
	{
		TCHAR path[ _MAX_PATH + 1 ];
		if ( GetModuleFileName( 0, path, sizeof(path)/sizeof(path[0]) ) > 0 )
		{
			SC_HANDLE service = CreateService( serviceControlManager,
							SERVICE_NAME, SERVICE_NAME,
							SERVICE_ALL_ACCESS, SERVICE_WIN32_OWN_PROCESS,
							SERVICE_AUTO_START, SERVICE_ERROR_IGNORE, path,
							0, 0, 0, 0, 0 );
			if ( service )
				CloseServiceHandle( service );
		}

		CloseServiceHandle( serviceControlManager );
	}
}

void UninstallService()
{
	SC_HANDLE serviceControlManager = OpenSCManager( 0, 0, SC_MANAGER_CONNECT );

	if ( serviceControlManager )
	{
		SC_HANDLE service = OpenService( serviceControlManager,
			SERVICE_NAME, SERVICE_QUERY_STATUS | DELETE );
		if ( service )
		{
			SERVICE_STATUS serviceStatus;
			if ( QueryServiceStatus( service, &serviceStatus ) )
			{
				if ( serviceStatus.dwCurrentState == SERVICE_STOPPED )
					DeleteService( service );
			}

			CloseServiceHandle( service );
		}

		CloseServiceHandle( serviceControlManager );
	}
}

int _tmain( int argc, TCHAR* argv[] )
{
	if ( argc > 1 && lstrcmpi( argv[1], TEXT("install") ) == 0 )
	{
		InstallService();
	}
	else if ( argc > 1 && lstrcmpi( argv[1], TEXT("uninstall") ) == 0 )
	{
		UninstallService();
	}
    else if ( argc > 1 && lstrcmpi( argv[1], TEXT("start") ) == 0 )
	{
		system(_T("sc start " )
               SERVICE_NAME);
	}
    else if ( argc > 1 && lstrcmpi( argv[1], TEXT("stop") ) == 0 )
	{
		system(_T("sc stop ")
               SERVICE_NAME);
	}
    else if ( argc > 1 && lstrcmpi( argv[1], TEXT("query") ) == 0 )
	{
		system(_T("sc query ")
               SERVICE_NAME);
	}
	else
	{
		RunService();
	}

	return 0;
}