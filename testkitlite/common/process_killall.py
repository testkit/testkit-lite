#!/usr/bin/python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>
""" kill testkit-lite """
import os
import platform
import signal
import re
import ctypes
from commodule.log import LOGGER
from commodule.killall import killall


def kill_testkit_lite(pid_file):
    """ kill testkit lite"""
    try:
        with open(pid_file, "r") as pidfile:
            pid = pidfile.readline().rstrip("\n")
            if pid:
                killall(pid)
    except IOError, error:
        pattern = re.compile('No such file or directory|No such process')
        match = pattern.search(str(error))
        if not match:
            LOGGER.info("[ Error: fail to kill existing testkit-lite, "\
                "error: %s ]\n" % error)
    return None

def clean_testxml(testxmls,remote_test):
    """clean all test xmls"""
    if remote_test:
        EXISTS = os.path.exists
        for testxml in testxmls:
            if EXISTS(testxml):
                fd_name = os.path.dirname(testxml)
                os.remove(testxml)
                os.rmdir(fd_name)
    return None