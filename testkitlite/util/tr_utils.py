import os
import signal
import sys
import logging

LOG = logging.getLogger("TestRunner")


def pidExists(pid):
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as e:
        return False
    else:
        return True


def IsWindows():
    return sys.platform == 'cygwin' or sys.platform.startswith('win')


def KillAllProcesses(ppid=None):
    if IsWindows():
        subprocess.check_call("TASKKILL /F /PID %s /T" % ppid)
    else:
        ppid = str(ppid)
        pidgrp = []

        def GetChildPids(ppid):
            command = "ps -ef | awk '{if ($3 ==%s) print $2;}'" % str(ppid)
            pids = os.popen(command).read()
            pids = pids.split()

            return pids

        pidgrp.extend(GetChildPids(ppid))
        for pid in pidgrp:
            pidgrp.extend(GetChildPids(pid))

        pidgrp.insert(0, ppid)
        while len(pidgrp) > 0:
            pid = pidgrp.pop()
            try:
                os.kill(int(pid), signal.SIGKILL)
                return True
            except OSError:
                try:
                    os.popen("kill -9 %d" % int(pid))
                    return True
                except:
                    return False
