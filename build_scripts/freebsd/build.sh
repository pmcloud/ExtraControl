#!/bin/sh

SOURCE=../..
BASE=$PWD
TARGET=$BASE/tmp/serclient

rm -rf $BASE/tmp freenas pfsense
mkdir freenas pfsense

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
find $TARGET -name .svn | xargs rm -rf

mkdir -p tmp/rcd.pfsense
cp rc.serclient tmp/rcd.pfsense/serclient
cp serclient.boot.pfsense tmp/rcd.pfsense/serclient.boot.sh
chmod +x tmp/rcd.pfsense/*

mkdir -p tmp/conf.freenas
cp rc.serclient tmp/conf.freenas/serclient
chmod +x tmp/conf.freenas/*

echo "@cwd /usr/local/serclient" > $BASE/packinglist
echo "@srcdir $BASE/tmp/serclient" >> $BASE/packinglist
(cd tmp/serclient && find -d * \! -type d >> $BASE/packinglist)

cp packinglist packinglist.pfsense

echo "@cwd /usr/local/etc/rc.d" >> $BASE/packinglist.pfsense
echo "@srcdir $BASE/tmp/rcd.pfsense" >> $BASE/packinglist.pfsense
(cd tmp/rcd.pfsense && find -d * \! -type d >> $BASE/packinglist.pfsense)

pkg_create -f packinglist.pfsense -c -'Aruba serial client' \
    -d -'automate common system administration tasks' \
    -v -I postinstall.freebsd -k preremove.freebsd \
    pfsense/aruba-serclient-0.01.tbz

cp packinglist packinglist.freenas

echo "@cwd /conf/base/etc/local/rc.d" >> $BASE/packinglist.freenas
echo "@srcdir $BASE/tmp/conf.freenas" >> $BASE/packinglist.freenas
(cd tmp/conf.freenas && find -d * \! -type d >> $BASE/packinglist.freenas)

pkg_create -f packinglist.freenas -c -'Aruba serial client' \
    -d -'automate common system administration tasks' \
    -v -I postinstall.freebsd -k preremove.freebsd \
    freenas/aruba-serclient-0.01.tbz

