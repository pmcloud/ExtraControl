#!/bin/bash

set -e

VERSION=0.01
MAINTAINER=info@aruba.it

rm -rf clone ubuntu debian centos openfiler endian

if test -d ../../.git; then
    mkdir clone
    git --git-dir ../../.git archive HEAD | tar -x -C clone
elif test -d .svn; then
    svn export ../.. clone
else
    echo "Not under revision control"
fi

mkdir ubuntu debian centos openfiler endian

# create Ubuntu package
cp postinstall.ubuntu postinstall-pak
cp preremove.ubuntu preremove-pak
fakeroot checkinstall --fstrans -y --install=no --backup=no \
    --type debian \
    --pakdir ubuntu \
    --pkgname aruba-serclient \
    --pkgversion "$VERSION" \
    --arch all \
    --pkglicense Proprietary \
    --pkggroup admin \
    --maintainer "$MAINTAINER" \
    --requires 'python2.7 \| python2.6 \| python2.5 \| python2.4' \
    ./install.sh ubuntu

# create Debian package
cp postinstall.debian postinstall-pak
cp preremove.debian preremove-pak
fakeroot checkinstall --fstrans -y --install=no --backup=no \
    --type debian \
    --pakdir debian \
    --pkgname aruba-serclient \
    --pkgversion "$VERSION" \
    --arch all \
    --pkglicense Proprietary \
    --pkggroup admin \
    --maintainer "$MAINTAINER" \
    --requires 'python2.7 \| python2.6 \| python2.5 \| python2.4, lsb-base \(\>= 3.2-14\)' \
    ./install.sh debian

# create CentOS package
fakeroot rpmbuild --define="_topdir `pwd`/centos" --define="distribution centos" -ba serclient.spec
if test -d centos/RPMS/noarch; then
    mv centos/RPMS/noarch/*.rpm centos
else
    mv centos/RPMS/*.rpm centos
fi
# Create Endian package
fakeroot rpmbuild --define="_topdir `pwd`/endian" --define="distribution endian" -ba serclient.spec
if test -d endian/RPMS/noarch; then
    mv endian/RPMS/noarch/*.rpm endian
else
    mv endian/RPMS/*.rpm endian
fi

# Create .tar.gz for OpenFiler
RPM_BUILD_ROOT=/tmp/openfiler-build fakeroot sh -c 'rm -rf /tmp/openfiler-build && ./install.sh centos && tar -C /tmp/openfiler-build -c -z -f openfiler.tar.gz .'

mv openfiler.tar.gz openfiler/openfiler-$VERSION.tar.gz
