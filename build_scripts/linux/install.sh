#!/bin/bash

set -e

if test -n "$RPM_BUILD_ROOT"; then
    BUILD_ROOT=$RPM_BUILD_ROOT
else
    BUILD_ROOT=''
fi

FULLPATH=`readlink -f $0`
BASE=`dirname $FULLPATH`
TARGET=$BUILD_ROOT/opt/serclient
SOURCE=$BASE/clone

case "$1" in
    ubuntu|centos|endian|debian)
    ;;
    *)
        echo "Usage: $0 [ubuntu | centos | endian | debian]"
        exit 1
    ;;
esac

# common installation
mkdir -p $TARGET $TARGET/custom $TARGET/internals $TARGET/plugins
cp $SOURCE/serclient.version $TARGET
cp $SOURCE/argparse.py $TARGET
cp $SOURCE/service.py $TARGET
chmod +x $TARGET/service.py
cp $SOURCE/tools.py $TARGET
cp -r $SOURCE/elementtree $TARGET
cp -r $SOURCE/serial $TARGET
cp -r $SOURCE/internals $TARGET
cp -r $SOURCE/plugins $TARGET

# Ubuntu-specific
case "$1" in
    ubuntu)
        mkdir -p $BUILD_ROOT/etc/init
        cp $SOURCE/../ubuntu-serclient.upstart $BUILD_ROOT/etc/init/serclient.conf
        ;;
    centos)
        mkdir -p $BUILD_ROOT/etc/init.d
        cp $SOURCE/../centos-serclient.init $BUILD_ROOT/etc/init.d/serclient
        chmod +x $BUILD_ROOT/etc/init.d/serclient
        ;;
    endian)
        mkdir -p $BUILD_ROOT/etc/init.d
        cp $SOURCE/../centos-serclient.init $BUILD_ROOT/etc/init.d/serclient
        chmod +x $BUILD_ROOT/etc/init.d/serclient
        mkdir -p $BUILD_ROOT/usr/lib/python/site-packages/endian/restartscripts
        cp $SOURCE/../endian-serclient.startup $BUILD_ROOT/usr/lib/python/site-packages/endian/restartscripts/serclient.py
        ;;
    debian)
        mkdir -p $BUILD_ROOT/etc/init.d
        cp $SOURCE/../debian-serclient.init $BUILD_ROOT/etc/init.d/serclient
        chmod +x $BUILD_ROOT/etc/init.d/serclient
        ;;
esac
