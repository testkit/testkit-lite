#!/bin/bash
#
# Copyright (C) 2012 Intel Corporation
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>


# parse spec required name
NAME=`grep "Name:" testkit-lite.spec | awk '{print $2}'`
if [ -z "$NAME" ];then
	echo "Name not specified in spec file"
	exit 1
fi

# parse spec required version
VERSION=`grep "Version:" testkit-lite.spec | awk '{print $2}'`
if [ -z "$VERSION" ];then
	echo "Version not specified in spec file"
	exit 1
fi

SRC_ROOT=${PWD}
RPM_ROOT=/tmp/${NAME}_pack
ARCHIVE_TYPE=tar.gz	#tar.gz2
ARCHIVE_OPTION=czvf	#czvf

# check precondition
check_precondition()
{
	which $1 > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "Error: no tool: $1"
		exit 1
	fi
}
check_precondition rpmbuild
#check_precondition gcc
check_precondition make

# clean
echo "cleaning rpm workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
rm -rf $RPM_ROOT

# create workspace
echo "create rpm workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
mkdir -p $RPM_ROOT/RPMS $RPM_ROOT/SRPMS $RPM_ROOT/SPECS $RPM_ROOT/SOURCES $RPM_ROOT/BUILD $RPM_ROOT/src_tmp/$NAME-$VERSION

# prepare
echo "prepare workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
rm -rf *.rpm *.tar.bz2 *.tar.gz
cp -a $SRC_ROOT/* $RPM_ROOT/src_tmp/$NAME-$VERSION
# create Makefile in top src folder
#cp $SRC_ROOT/top_Makefile $RPM_ROOT/src_tmp/$NAME-$VERSION/Makefile
cp $PWD/testkit-lite.spec $RPM_ROOT/SPECS
cd $RPM_ROOT/src_tmp
tar $ARCHIVE_OPTION $RPM_ROOT/SOURCES/$NAME-$VERSION.$ARCHIVE_TYPE $NAME-$VERSION
cd -

# build
echo "build from workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
cd  $RPM_ROOT/SPECS
rpmbuild -ba testkit-lite.spec --clean --define "_topdir $RPM_ROOT" --target=noarch
cd -

# copy rpm
echo "copy from workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "get rpm packages......"
find $RPM_ROOT -name "$NAME*.rpm" | grep -v debuginfo | xargs -n1 -I {} mv {} $PWD -f
echo "get $NAME-$VERSION.$ARCHIVE_TYPE......"
mv $RPM_ROOT/SOURCES/$NAME-$VERSION.$ARCHIVE_TYPE $PWD -f

# clean
echo "cleaning rpm workspace... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
#rm -rf $RPM_ROOT

# validate
echo "checking result... >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
if [ -z "`ls | grep "\.rpm"`" ] || [ -z "`ls | grep "\.$ARCHIVE_TYPE"`" ];then
	echo "------------------------------ FAILED to build $NAME RPM packages --------------------------"
	exit 1
else
	echo "------------------------------ Done to build $NAME RPM packages --------------------------"
	ls *.rpm *.$ARCHIVE_TYPE 2>/dev/null
fi
