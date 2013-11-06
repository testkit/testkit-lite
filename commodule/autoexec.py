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
#              Liu,chengtao <chengtaox.liu@intel.com>
""" The shell command executor module"""

import os
import sys
import time
import subprocess

from .killall import killall
from .str2 import str2str


def shell_command(cmd, timeout=15):
    """shell communication for quick return in sync mode"""
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    time_cnt = 0
    exit_code = None
    while time_cnt < timeout:
        exit_code = proc.poll()
        if not exit_code is None:
            break
        time_cnt += 0.2
        time.sleep(0.2)

    if exit_code is None:
        killall(proc.pid)
        exit_code = -1
        result = []
    else:
        result = proc.stdout.readlines() or proc.stderr.readlines()
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
    if stdout_file is None:
        stdout_file = os.path.expanduser("~") + os.sep + "shell_stdout"

    if stderr_file is None:
        stderr_file = os.path.expanduser("~") + os.sep + "shell_stderr"

    exit_code = None
    wbuffile1 = file(stdout_file, "w")
    wbuffile2 = file(stderr_file, "w")
    rbuffile1 = file(stdout_file, "r")
    rbuffile2 = file(stderr_file, "r")
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
        if timeout is not None:
            timeout -= 0.1
            if timeout <= 0:
                try:
                    exit_code = "timeout"
                    cmd_open.terminate()
                    time.sleep(5)
                except OSError:
                    killall(cmd_open.pid)
                break
        time.sleep(0.1)

    if boutput:
        print_log()
    rbuffile1.seek(0)
    rbuffile2.seek(0)
    stdout_log = str2str(rbuffile1.read())
    stderr_log = str2str(rbuffile2.read())
    if 'returncode=' in stdout_log:
        index = stdout_log.find('returncode=') + 11
        exit_code = str(stdout_log[index:]).strip('\r\n')
    stdout_log = '<![CDATA[' + stdout_log + ']]>'
    stderr_log = '<![CDATA[' + stderr_log + ']]>'

    wbuffile1.close()
    wbuffile2.close()
    rbuffile1.close()
    rbuffile2.close()
    os.remove(stdout_file)
    os.remove(stderr_file)
    return [exit_code, stdout_log, stderr_log]
