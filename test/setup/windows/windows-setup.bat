@echo off

set SOURCE_BASE=\\tsclient\sct
set INSTALL_BASE=c:\serclient-test\cygwin

echo Installing Cygwin
%SOURCE_BASE%\windows\cygwin-setup.exe --local-install ^
    --local-package-dir %SOURCE_BASE%\windows\packages --no-startmenu ^
    --no-shortcuts --no-desktop --root %INSTALL_BASE% --quiet-mode ^
    --no-verify --packages openssh,editrights,coreutils > install.log

rem Without '-l' PATH is just Windows path
echo Setup OpenSSH
%INSTALL_BASE%\bin\bash -l -c "ssh-host-config -y"
echo Start OpenSSH
%INSTALL_BASE%\bin\bash -l -c "cygrunsrv --start sshd"

echo Open firewall port 22
ver | findstr /i "6\.1\." > nul
if %ERRORLEVEL% equ 0 (
    netsh advfirewall firewall show rule name=OpenSSH || netsh ^
        advfirewall firewall add rule name=OpenSSH ^
            protocol=TCP dir=in localport=22 action=allow
) else (
    netsh firewall add portopening name=OpenSSH ^
            protocol=TCP port=22 mode=enable
)
