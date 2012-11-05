** Windows set-up

* Install CygWin and OpenSSH

$ rdesktop -g 1024x768 -u Administrator -p - \
      -r disk:sct=/path/to/serclient/test/setup <ip> \
      -s '\\tsclient\sct\windows\windows-setup.bat'

If there is an user already logged in, just start manually

C:\> \\tsclient\sct\windows\windows-setup.bat

from a command prompt; the setup procedure will create a privileged
user for the OpenSSH daemon (requires to enter a password) and will
open port 22 on Windows firewall.

* Copy a SSH public key in $HOME/.ssh/authorized_keys
