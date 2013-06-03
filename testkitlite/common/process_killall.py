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


def killall(ppid):
    """Kill all children process by parent process ID"""
    sys_platform = platform.system()
    try:
        if sys_platform == "Linux":
            ppid = str(ppid)
            pidgrp = []

            def getchildpids(ppid):
                """Return a list of children process"""
                command = "ps -ef | awk '{if ($3 == %s) print $2;}'" % str(ppid)
                pids = os.popen(command).read()
                pids = pids.split()
                return pids

            pidgrp.extend(getchildpids(ppid))
            for pid in pidgrp:
                pidgrp.extend(getchildpids(pid))
            # Insert self process ID to PID group list
            pidgrp.insert(0, ppid)
            while len(pidgrp) > 0:
                pid = pidgrp.pop()
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except OSError, error:
                    pattern = re.compile('No such process')
                    match = pattern.search(str(error))
                    if not match:
                        LOGGER.info(
                            "[ Error: fail to kill pid: %s, error: %s ]\n" % (
                            int(pid), error))
        # kill for windows platform
        else:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, 0, int(ppid))
            # kill_result
            kernel32.TerminateProcess(handle, 0)
    except OSError, error:
        pattern = re.compile('No such process')
        match = pattern.search(str(error))
        if not match:
            LOGGER.info("[ Error: fail to kill pid: %s, error: %s ]\n" % (
                int(ppid), error))
    return None


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
