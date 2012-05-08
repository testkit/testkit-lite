#!/usr/bin/python
#
# Copyright (C) 2010, Intel Corporation.
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
#              Tian, Xu <xux.tian@intel.com>
#              Wang, Jing <jing.j.wang@intel.com>
#              Wei, Zhang <wei.z.zhang@intel.com>
#

import os
import sys
import time
import threading
import subprocess
from multiprocessing import Process
from multiprocessing import Value
from testkitlite.common.killall import killall


###############################################################################
def shell_exec(cmd, timeout=None, boutput=False):

    """shell executor, return [exitcode, stdout/stderr]
       timeout: None means unlimited timeout
       boutput: specify whether print output during the command running
    """
    BUFFILE1 = os.path.expanduser("~") + os.sep + ".shellexec_buffile_stdout"
    BUFFILE2 = os.path.expanduser("~") + os.sep + ".shellexec_buffile_stderr"

    LOOP_DELTA = 0.01

    exit_code = None
    stdout_log  = ""
    stderr_log  = ""

    wbuffile1 = file(BUFFILE1, "w")
    wbuffile2 = file(BUFFILE2, "w")
    rbuffile1 = file(BUFFILE1, "r")
    rbuffile2 = file(BUFFILE2, "r")

    # start execution process
    cmdPopen = subprocess.Popen(args=cmd, shell=True, close_fds=True,
                                stdout=wbuffile1, stderr=wbuffile2)

    def print_log():
        sys.stdout.write(rbuffile1.read())
        sys.stdout.write(rbuffile2.read())
        sys.stdout.flush()

    # loop for timeout and print
    rbuffile1.seek(0)
    rbuffile2.seek(0)
    t = timeout
    while True:

        exit_code = cmdPopen.poll()
        if exit_code is not None:
            break

        if boutput:
            print_log()

        if t is not None:
            if t <= 0:
                # timeout, kill command
                try:
                    cmdPopen.terminate()
                    time.sleep(5)
                except:
                    killall(cmdPopen.pid) 
                break
            else:
                t -= LOOP_DELTA

        time.sleep(LOOP_DELTA)


    # print left output
    if boutput:
        # flush left output in log
        print_log()

    # store the log from buffile
    rbuffile1.seek(0)
    rbuffile2.seek(0)
    stdout_log = rbuffile1.read()
    stderr_log = rbuffile2.read()

    # close file
    wbuffile1.close()
    wbuffile2.close()
    rbuffile1.close()
    rbuffile2.close()
    os.remove(BUFFILE1)
    os.remove(BUFFILE2)

    return [exit_code, stdout_log.strip('\n'), stderr_log.strip('\n')]
