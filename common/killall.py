#!/bin/env python
#
# Copyright (C) 2012, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307 USA.
#
# Authors:
#                       Xu,Tian <xux.tian@intel.com>

import os
import platform
import signal

def killall(ppid):
    """Kill all children process by parent process ID"""

    OS = (platform.system()).upper()
    if OS == "LINUX":
        ppid = str(ppid)
        pidgrp = []

        def getchildpids(ppid):
            """Return a list of children process"""

            command = "ps -ef|awk '{if ($3 ==%s) print $2;}'"%str(ppid)
            pids = os.popen(command).read()
            pids = pids.split()
            return pids

        pidgrp.extend(getchildpids(ppid))
        for pid in pidgrp:
            pidgrp.extend(getchildpids(pid))

        #Insert self process ID to PID group list
        pidgrp.insert(0,ppid)
        while len(pidgrp) > 0:
            pid = pidgrp.pop()
            try:
               os.kill(int(pid),signal.SIGKILL)
            except OSError:
               try:
                   os.popen("sudo kill -9 %d"%int(pid))
               except:
                   pass
    else:
        os.kill(int(pid),signal.SIGKILL)
    return None
