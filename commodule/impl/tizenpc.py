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
#           Chengtao,Liu  <chengtaox.liu@intel.com>

""" The implementation of tizenpc PC communication"""

import os
import time
import socket
import threading
import re
from shutil import copyfile

from commodule.log import LOGGER
from commodule.autoexec import shell_command, shell_command_ext
from commodule.killall import killall


HOST_NS = "127.0.0.1"
os.environ['no_proxy'] = HOST_NS
RPM_INSTALL = "rpm -ivh %s"
RPM_UNINSTALL = "rpm -e %s"
RPM_LIST = "sdb -s %s shell rpm -qa | grep tct"
APP_QUERY_STR = "ps aux |grep '%s'|grep -v grep|awk '{print $2}'"
APP_KILL_STR = "kill -9 %s"
WRT_QUERY_STR = "wrt-launcher -l|grep '%s'|grep -v grep|awk '{print $2\":\"$NF}'"
WRT_START_STR = "wrt-launcher -s %s"
WRT_STOP_STR = "wrt-launcher -k %s"
WRT_INSTALL_STR = "wrt-installer -i %s"
WRT_UNINSTL_STR = "wrt-installer -un %s"
DLOG_CLEAR = "dlogutil -c"
DLOG_WRT = "dlogutil WRT:D -v time"


def debug_trace(cmdline, logfile):
    global debug_flag, metux
    wbuffile = file(logfile, "w")
    import subprocess
    exit_code = None
    proc = subprocess.Popen(args=cmdline,
                            shell=True,
                            stdout=wbuffile,
                            stderr=None)
    while True:
        exit_code = proc.poll()
        if exit_code is not None:
            break
        time.sleep(0.5)
        metux.acquire()
        proc_flag = debug_flag
        metux.release()
        if not proc_flag:
            break
    wbuffile.close()
    if exit_code is None:
        killall(proc.pid)


class tizenpcPC:

    """ Implementation for transfer data
        between Host and tizenpc PC
    """

    def __init__(self):
        self.deviceid = "localhost"

    def shell_cmd(self, cmd="", timeout=15):
        return shell_command(cmd, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(APP_QUERY_STR % process_name)
        return len(ret)

    def launch_stub(self, stub_app, stub_port="8000", debug_opt=""):
        cmdline = "%s --port:%s %s" % (stub_app, stub_port, debug_opt)
        exit_code, ret = self.shell_cmd(cmdline)
        time.sleep(2)

    def shell_cmd_ext(self,
                      cmd="",
                      timeout=None,
                      boutput=False,
                      stdout_file=None,
                      stderr_file=None):
        return shell_command_ext(cmd, timeout, boutput, stdout_file, stderr_file)

    def get_device_ids(self):
        """
            get deivce list of ids
        """
        return ['localhost']

    def get_device_info(self):
        """
            get tizenpc deivce inforamtion
        """
        device_info = {}
        resolution_str = ""
        screen_size_str = ""
        device_model_str = ""
        device_name_str = ""
        build_id_str = ""
        os_version_str = ""

        # get resolution and screen size
        exit_code, ret = shell_command("xrandr")
        pattern = re.compile("connected (\d+)x(\d+).* (\d+mm) x (\d+mm)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))

        # get architecture
        exit_code, ret = shell_command("uname -m")
        if len(ret) > 0:
            device_model_str = ret[0]

        # get hostname
        exit_code, ret = shell_command("uname -n")
        if len(ret) > 0:
            device_name_str = ret[0]

        # get os version
        exit_code, ret = shell_command("cat /etc/issue")
        for line in ret:
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)

        # get build id
        exit_code, ret = shell_command("cat /etc/os-release")
        for line in ret:
            if line.find("BUILD_ID=") != -1:
                build_id_str = line.split('=')[1].strip('\"\r\n')

        os_version_str = os_version_str[0:-1]
        device_info["device_id"] = self.deviceid
        device_info["resolution"] = resolution_str
        device_info["screen_size"] = screen_size_str
        device_info["device_model"] = device_model_str
        device_info["device_name"] = device_name_str
        device_info["os_version"] = os_version_str
        device_info["build_id"] = build_id_str
        return device_info

    def get_server_url(self, remote_port="8000"):
        """get server url"""
        url_forward = "http://%s:%s" % (HOST_NS, remote_port)
        return url_forward

    def install_package(self, pkgpath):
        """
           install a package on tizenpc device
        """
        cmd = RPM_INSTALL % pkgpath
        exit_code, ret = shell_command(cmd)
        return ret

    def install_package(self, pkgname):
        """
           install a package on tizenpc device
        """
        cmd = RPM_UNINSTALL % pkgname
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self):
        """get list of installed package from device"""
        cmd = RPM_LIST
        exit_code, ret = shell_command(cmd)
        return ret

    def download_file(self, remote_path, local_path):
        """download file"""
        copyfile(remote_path, local_path)
        return True

    def upload_file(self, remote_path, local_path):
        """upload file"""
        copyfile(local_path, remote_path)
        return True

    def get_launcher_opt(self, test_launcher, test_suite, test_set, fuzzy_match, auto_iu):
        """get test option dict """
        test_opt = {}
        test_opt["suite_name"] = test_suite
        test_opt["launcher"] = test_launcher
        test_opt["test_app_id"] = test_suite
        if test_launcher.find('WRTLauncher') != -1:
            cmd = ""
            test_app_id = None
            test_opt["launcher"] = "wrt-launcher"
            # test suite need to be installed
            if auto_iu:
                test_wgt = test_set
                test_wgt_path = "/opt/%s/%s.wgt" % (test_suite, test_set)
                if not self.install_app(test_wgt_path):
                    LOGGER.info("[ failed to install widget \"%s\" in target ]"
                                % test_wgt)
                    return None
            else:
                test_wgt = test_suite

            # query the whether test widget is installed ok
            cmd = WRT_QUERY_STR % test_wgt
            exit_code, ret = shell_command(cmd)
            if exit_code == -1:
                return None
            for line in ret:
                items = line.split(':')
                if len(items) < 1:
                    continue
                if (fuzzy_match and items[0].find(test_wgt) != -1) or items[0] == test_wgt:
                    test_app_id = items[1].strip('\r\n')
                    break

            if test_app_id is None:
                LOGGER.info("[ test widget \"%s\" not found in target ]"
                            % test_wgt)
                return None
            else:
                test_opt["test_app_id"] = test_app_id

        return test_opt

    def start_debug(self, dlogfile):
        global debug_flag, metux
        debug_flag = True
        metux = threading.Lock()
        cmdline = DLOG_CLEAR
        exit_code, ret = shell_command(cmdline)
        cmdline = DLOG_WRT
        threading.Thread(target=debug_trace, args=(cmdline, dlogfile)).start()

    def stop_debug(self):
        global debug_flag, metux
        metux.acquire()
        debug_flag = False
        metux.release()

    def launch_app(self, wgt_name):
        timecnt = 0
        blauched = False
        cmdline = WRT_STOP_STR % wgt_name
        exit_code, ret = shell_command(cmdline)
        cmdline = WRT_START_STR % wgt_name
        while timecnt < 3:
            exit_code, ret = shell_command(cmdline)
            if len(ret) > 0 and ret[0].find('launched') != -1:
                blauched = True
                break
            timecnt += 1
            time.sleep(3)
        return blauched

    def kill_app(self, wgt_name):
        cmdline = WRT_STOP_STR % wgt_name
        exit_code, ret = shell_command(cmdline)
        return True

    def install_app(self, wgt_path="", timeout=90):
        cmd = WRT_INSTALL_STR % wgt_path
        exit_code, ret = shell_command(cmd, timeout)
        if exit_code == -1:
            cmd = APP_QUERY_STR % wgt_path
            exit_code, ret = shell_command(cmd)
            for line in ret:
                cmd = APP_KILL_STR % line.strip('\r\n')
                exit_code, ret = shell_command(cmd)
            return False
        else:
            return True

    def uninstall_app(self, wgt_name):
        cmd = WRT_UNINSTL_STR % wgt_name
        exit_code, ret = shell_command(cmd)
        return True


def get_target_conn():
    """ Get connection for Test Target"""
    return tizenpcPC()
