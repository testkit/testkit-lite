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
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110 - 1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>
""" The process kill for os"""

import os
import platform
import signal
import re
import ctypes


def killall(ppid):
    """Kill all children process by parent process ID"""
    os_ver = platform.system()
    try:
        if os_ver == "Linux":
            ppid = str(ppid)
            pidgrp = []

            def getchildpids(ppid):
                """Return a list of children process"""
                command = "ps -ef | awk '{if ($3 == %s) print $2;}'" % str(
                    ppid)
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
                        print "[ Error: fail to kill pid: %s," \
                            " error: %s ]\n" % (int(pid), error)
        # kill for windows platform
        else:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, 0, int(ppid))
            kernel32.TerminateProcess(handle, 0)
    except OSError, error:
        pattern = re.compile('No such process')
        match = pattern.search(str(error))
        if not match:
            print "[ Error: fail to kill pid: %s, error: %s ]\n" \
                % (int(ppid), error)
    return None
