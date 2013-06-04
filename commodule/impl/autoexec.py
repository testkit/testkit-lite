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
# Boston, MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>
""" The shell command executor module"""

import os
import sys
import time
import subprocess

from .killall import killall
from .str2 import str2str


def shell_command(cmd):
    """shell communication for quick return in sync mode"""
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    ret1 = proc.stdout.readlines()
    ret2 = proc.stderr.readlines()
    exit_code = proc.poll()
    if exit_code is None:
        exit_code = 0
    result = ret1 or ret2
    return [exit_code, result]


def shell_command_ext(cmd="",
                      timeout=None,
                      boutput=False,
                      stdout_file=None,
                      stderr_file=None):
    """shell executor, return [exitcode, stdout/stderr]
       timeout: None means unlimited timeout
       boutput: specify whether print output during the command running
    """
    buffer_1 = ""
    buffer_2 = ""
    if stdout_file is None:
        buffer_1 = os.path.expanduser(
            "~") + os.sep + "shellexec_stdout"
    else:
        buffer_1 = stdout_file

    if stderr_file is None:
        buffer_2 = os.path.expanduser(
            "~") + os.sep + "shellexec_stderr"
    else:
        buffer_2 = stderr_file

    loop_delta = 0.1
    exit_code = None
    stdout_log = ""
    stderr_log = ""
    time_val = timeout

    wbuffile1 = file(buffer_1, "w")
    wbuffile2 = file(buffer_2, "w")
    rbuffile1 = file(buffer_1, "r")
    rbuffile2 = file(buffer_2, "r")
    cmd_open = subprocess.Popen(args=cmd,
                                shell=True,
                                stdout=wbuffile1,
                                stderr=wbuffile2)
    rbuffile1.seek(0)
    rbuffile2.seek(0)

    def print_log():
        """print the stdout to terminate"""
        sys.stdout.write(rbuffile1.read())
        sys.stdout.write(rbuffile2.read())
        sys.stdout.flush()

    while True:
        exit_code = cmd_open.poll()
        if exit_code is not None:
            break

        if boutput:
            print_log()

        if time_val is not None:
            if time_val <= 0:
                try:
                    exit_code = "timeout"
                    cmd_open.terminate()
                    time.sleep(5)
                except OSError:
                    killall(cmd_open.pid)
                break
            else:
                time_val -= loop_delta
        time.sleep(loop_delta)

    if boutput:
        print_log()

    if not boutput:
        rbuffile1.seek(0)
        rbuffile2.seek(0)
        stdout_log = rbuffile1.read()
        stderr_log = rbuffile2.read()
        stdout_log = str2str(stdout_log)
        stderr_log = str2str(stderr_log)
        if 'returncode=' in stdout_log:
            index = stdout_log.find('returncode=') + 11
            retruncode = str(stdout_log[index:])
            exit_code = retruncode.strip('\r\n')
        stdout_log = '<![CDATA[' + stdout_log + ']]>'
        stderr_log = '<![CDATA[' + stderr_log + ']]>'

    wbuffile1.close()
    wbuffile2.close()
    rbuffile1.close()
    rbuffile2.close()
    os.remove(buffer_1)
    os.remove(buffer_2)
    if not boutput:
        return [exit_code, stdout_log.strip('\n'), stderr_log.strip('\n')]
    else:
        return True
