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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>

import os
import sys
import time
import threading
import subprocess
from multiprocessing import Process
from multiprocessing import Value
from testkitlite.common.killall import killall
from testkitlite.common.str2 import *

def shell_exec(cmd, pid_log, timeout=None, boutput=False):
    """shell executor, return [exitcode, stdout/stderr]
       timeout: None means unlimited timeout
       boutput: specify whether print output during the command running
    """
    BUFFILE1 = os.path.expanduser("~") + os.sep + ".shellexec_buffile_stdout"
    BUFFILE2 = os.path.expanduser("~") + os.sep + ".shellexec_buffile_stderr"
    
    LOOP_DELTA = 0.01
    
    exit_code = None
    stdout_log = ""
    stderr_log = ""
    
    wbuffile1 = file(BUFFILE1, "w")
    wbuffile2 = file(BUFFILE2, "w")
    rbuffile1 = file(BUFFILE1, "r")
    rbuffile2 = file(BUFFILE2, "r")
    
    # start execution process
    cmdPopen = subprocess.Popen(args=cmd, shell=True,
                                stdout=wbuffile1, stderr=wbuffile2)
    # write pid only for external execution
    if pid_log is not "no_log":
        try:
            with open(pid_log, "a") as fd:
                pid = str(cmdPopen.pid)
                fd.writelines(pid + '\n')
        except:
            pass
            
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
                    exit_code = "time_out"
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
    # only leave readable characters
    stdout_log = str2str(stdout_log)
    stderr_log = str2str(stderr_log)
    stdout_log = '<![CDATA[' + stdout_log + ']]>'
    stderr_log = '<![CDATA[' + stderr_log + ']]>'
    # close file
    wbuffile1.close()
    wbuffile2.close()
    rbuffile1.close()
    rbuffile2.close()
    os.remove(BUFFILE1)
    os.remove(BUFFILE2)
    
    return [exit_code, stdout_log.strip('\n'), stderr_log.strip('\n')]
