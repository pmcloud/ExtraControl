Summary:   Aruba serial client
Name:      aruba-serclient
Version:   0.01
Release:   1
License:   Proprietary
Packager:  info@aruba.it
BuildArch: noarch
Group:     admin
Provides:  aruba-serclient
Requires:  python >= 2.4

%description
Aruba serial client
automate common system administration tasks.

%build
:

%install
../../install.sh %{distribution}

%post
#!/bin/sh

set -e

/etc/init.d/serclient restart
chkconfig --add serclient

%preun
#!/bin/sh

set -e

/etc/init.d/serclient stop
chkconfig --del serclient

%files
/opt/serclient/
/etc/init.d/serclient
%if %{distribution} == endian
/usr/lib/python/site-packages/endian/restartscripts/serclient.py
%endif
