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

#include "../launchprocess.hpp"
#include <windows.h>
#include <string>
#include <algorithm>
#include <ctime>

BOOL SafeTerminateProcess(HANDLE hProcess, UINT uExitCode)
{
    DWORD dwTID, dwCode, dwErr = 0;
    HANDLE hProcessDup = INVALID_HANDLE_VALUE;
    HANDLE hRT = NULL;
    HINSTANCE hKernel = GetModuleHandle("Kernel32");
    BOOL bSuccess = FALSE;
    BOOL bDup = DuplicateHandle(GetCurrentProcess(),
                                hProcess,
                                GetCurrentProcess(),
                                &hProcessDup,
                                PROCESS_ALL_ACCESS,
                                FALSE,
                                0);
    // Detect the special case where the process is
    // already dead...
    if ( GetExitCodeProcess((bDup) ? hProcessDup : hProcess, &dwCode) &&
         (dwCode == STILL_ACTIVE) )
    {
        FARPROC pfnExitProc;
        pfnExitProc = GetProcAddress(hKernel, "ExitProcess");
        hRT = CreateRemoteThread((bDup) ? hProcessDup : hProcess,
                                 NULL,
                                 0,
                                 (LPTHREAD_START_ROUTINE)pfnExitProc,
                                 (PVOID)uExitCode, 0, &dwTID);
        if ( hRT == NULL )
            dwErr = GetLastError();
    }
    else
    {
        dwErr = ERROR_PROCESS_ABORTED;
    }
    if ( hRT )
    {
        // Must wait process to terminate to
        // guarantee that it has exited...
        WaitForSingleObject((bDup) ? hProcessDup : hProcess,
                            INFINITE);
        CloseHandle(hRT);
        bSuccess = TRUE;
    }
    if ( bDup )
        CloseHandle(hProcessDup);
    if ( !bSuccess )
        SetLastError(dwErr);
    return bSuccess;
}


LaunchResult launchProcess(const std::string & name, const std::string & arguments, bool capture_output, int timeout_in_seconds)
{
	LaunchResult result;

	STARTUPINFO si = {};
	si.cb =	sizeof(si);
	si.dwFlags = STARTF_USESTDHANDLES;
	si.hStdInput = NULL;

	PROCESS_INFORMATION pi = {};

	HANDLE child_stdout_read = NULL;
	HANDLE child_stdout_write = NULL;

	if (capture_output) {
		// Create a pipe for the process' stdout
		//
		SECURITY_ATTRIBUTES saAttr;
		saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
		saAttr.bInheritHandle = TRUE;
		saAttr.lpSecurityDescriptor = NULL;

		if(!CreatePipe(&child_stdout_read, &child_stdout_write, &saAttr, 0)) {
			return result;
		}

		si.hStdOutput = child_stdout_write;
		si.hStdError = child_stdout_write;
	}


	const std::string quoted_name = "\"" + name + "\"";
	const std::string args = quoted_name + " " + arguments.substr(0, MAX_PATH - 1);
	char args_buffer[MAX_PATH + 1] = {};
	std::copy(args.begin(), args.end(), &args_buffer[0]);

	if(!CreateProcess(NULL, &args_buffer[0], NULL, NULL,
	                  capture_output? TRUE : FALSE,
	                  0, NULL, NULL, &si, &pi))
	{
		CloseHandle(child_stdout_read);
		CloseHandle(child_stdout_write);
		return result;
	}
    
	CloseHandle(child_stdout_write);
	std::time_t elapsed = 0;
	std::string std_output;
	std::time_t start_time = time(NULL); // TODO: handle case where start == -1
	if (capture_output) {

		// While the timeout has not elapsed read in chunks from the pipe
		//

		while ((elapsed = std::time(NULL) - start_time) < timeout_in_seconds) {
			const int sz = 4 * 1024;
			char buffer[sz] = {};
			DWORD actually_read = 0;
			bool read_success = ReadFile(child_stdout_read, &buffer[0], sz, &actually_read, NULL) != 0;
			if (!read_success || actually_read == 0 ) {
				if (GetLastError() == ERROR_BROKEN_PIPE) {
					break;
				}
			}
			std_output.append(buffer, buffer + actually_read);
		}

		CloseHandle(child_stdout_read);
		CloseHandle(child_stdout_write);

	} else {
		const DWORD dw = WaitForSingleObject(pi.hProcess, timeout_in_seconds * 1000);
		if (dw == WAIT_FAILED) {
			while ((elapsed = std::time(NULL) - start_time) < timeout_in_seconds) {
				// just wait
			}
			std::cout << "Wait for process '" << name << "' failed"  // TODO: use logger
			             " (will attempt to shut it down)";
		}
	}


	result.output = std_output;

	if (SafeTerminateProcess(pi.hProcess, EXIT_FAILURE) || GetLastError() == ERROR_PROCESS_ABORTED) {
		std::cout << "Process '" << name << "' terminated." << std::endl; // TODO: use logger
	}
	else {
		std::cout << "Process '" << name << "' could not be terminated."; // TODO: use logger
	}


	if (elapsed < timeout_in_seconds) {
		result.result = LaunchResult::success;
		DWORD dw = 0;
		GetExitCodeProcess(pi.hProcess, &dw);
		result.exit_code = dw;
	} else {
		const int e = EXIT_FAILURE;
		result.exit_code = e;
		result.result = LaunchResult::timeout;
	}

	CloseHandle(pi.hThread);
	CloseHandle(pi.hProcess);
	
	return result;

}

