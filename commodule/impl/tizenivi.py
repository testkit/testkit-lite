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
# Authors:
#           Chengtao,Liu  <chengtaox.liu@intel.com>

""" The implementation of tizen IVI communication"""

import os
import time
import socket
import threading
import re
from shutil import copyfile

from commodule.log import LOGGER
from commodule.autoexec import shell_command, shell_command_ext
from commodule.killall import killall
from commodule.connector import InvalidDeviceException


HOST_NS = "127.0.0.1"
os.environ['no_proxy'] = HOST_NS
RPM_INSTALL = "ssh %s rpm -ivh %s"
RPM_UNINSTALL = "ssh %s rpm -e %s"
RPM_LIST = "ssh %s rpm -qa | grep tct"
APP_QUERY_STR = "ssh %s \"ps aux |grep '%s'|grep -v grep\"|awk '{print $2}'"
APP_KILL_STR = "ssh %s kill -9 %s"
WRT_QUERY_STR = "ssh %s \"wrt-launcher -l|grep '%s'|grep -v grep\"|awk '{print $2\":\"$NF}'"
WRT_START_STR = "ssh %s wrt-launcher -s %s"
WRT_STOP_STR = "ssh %s wrt-launcher -k %s"
WRT_INSTALL_STR = "ssh %s wrt-installer -i %s"
WRT_UNINSTL_STR = "ssh %s wrt-installer -un %s"
WGT_LOCATION = "/opt/usr/media/tct/opt/%s/%s.wgt"


class tizenIVI:

    """ Implementation for transfer data
        between Host and tizenivi PC
    """

    def __init__(self, deviceid="root@127.0.0.1"):
        self.deviceid = deviceid

    def shell_cmd(self, cmd="", timeout=15):
        cmd = "ssh %s %s" % (self.deviceid, cmd)
        return shell_command(cmd, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(APP_QUERY_STR % (self.deviceid, process_name))
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
        cmd = "ssh %s '%s; echo returncode=$?'" % (self.deviceid, cmd)
        return shell_command_ext(cmd, timeout, boutput, stdout_file, stderr_file)

    def shell_cmd_host(self,
                       cmd="",
                       timeout=None,
                       boutput=False,
                       stdout_file=None,
                       stderr_file=None):
        cmd = cmd.replace("$deviceid", self.deviceid)
        return shell_command_ext(cmd, timeout, boutput, stdout_file, stderr_file)

    def get_device_ids(self):
        """
            get deivce list of ids
        """
        return ['localhost']

    def get_device_info(self):
        """
            get tizenivi deivce inforamtion
        """
        device_info = {}
        resolution_str = ""
        screen_size_str = ""
        device_model_str = ""
        device_name_str = ""
        build_id_str = ""
        os_version_str = ""

        # get resolution and screen size
        exit_code, ret = shell_command("ssh %s xrandr" % self.deviceid)
        pattern = re.compile("connected (\d+)x(\d+).* (\d+mm) x (\d+mm)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))

        # get architecture
        exit_code, ret = shell_command("ssh %s uname -m" % self.deviceid)
        if len(ret) > 0:
            device_model_str = ret[0]

        # get hostname
        exit_code, ret = shell_command("ssh %s uname -n" % self.deviceid)
        if len(ret) > 0:
            device_name_str = ret[0]

        # get os version
        exit_code, ret = shell_command("ssh %s cat /etc/issue" % self.deviceid)
        for line in ret:
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)

        # get build id
        exit_code, ret = shell_command("ssh %s cat /etc/os-release" % self.deviceid)
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
        remote_ip = self.deviceid
        remote_ip = remote_ip.split('@')[1]
        os.environ['no_proxy'] = remote_ip
        url_forward = "http://%s:%s" % (remote_ip, remote_port)
        return url_forward

    def install_package(self, pkgpath):
        """
           install a package on tizenivi device
        """
        cmd = RPM_INSTALL % (self.deviceid, pkgpath)
        exit_code, ret = shell_command(cmd)
        return ret

    def install_package(self, pkgname):
        """
           install a package on tizenivi device
        """
        cmd = RPM_UNINSTALL % (self.deviceid, pkgname)
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self):
        """get list of installed package from device"""
        cmd = RPM_LIST % (self.deviceid)
        exit_code, ret = shell_command(cmd)
        return ret

    def download_file(self, remote_path, local_path):
        """download file"""
        local_path_dir = os.path.dirname(local_path)
        if not os.path.exists(local_path_dir):
            os.makedirs(local_path_dir)
        cmd = "scp %s:%s %s" % (self.deviceid, remote_path, local_path)
        exit_code, ret = shell_command(cmd)
        if not os.path.exists(local_path):
            return False
        return True

    def upload_file(self, remote_path, local_path):
        """upload file"""
        cmd = "scp %s %s:%s" % (local_path, self.deviceid, remote_path)
        exit_code, ret = shell_command(cmd)
        return True

    def get_launcher_opt(self, test_launcher, test_ext, test_widget, test_suite, test_set):
        """get test option dict """
        test_opt = {}
        test_opt["suite_name"] = test_suite
        test_opt["launcher"] = test_launcher
        test_opt["test_app_id"] = test_suite
        cmd = ""
        if test_launcher.find('WRTLauncher') != -1:
            test_app_id = None
            client_cmds = test_launcher.strip().split()
            wrt_tag = client_cmds[1] if len(client_cmds) > 1 else ""
            test_opt['fuzzy_match'] = fuzzy_match = wrt_tag.find('z') != -1
            test_opt['auto_iu'] = auto_iu = wrt_tag.find('iu') != -1
            test_opt['self_exec'] = wrt_tag.find('a') != -1
            test_opt['self_repeat'] = wrt_tag.find('r') != -1
            test_opt["launcher"] = "wrt-launcher"
            # test suite need to be installed
            if auto_iu:
                test_wgt = test_set
                test_wgt_path = WGT_LOCATION % (test_suite, test_set)
                if not self.install_app(test_wgt_path):
                    LOGGER.info("[ failed to install widget \"%s\" in target ]"
                                % test_wgt)
                    return None
            else:
                test_wgt = test_suite

            # query the whether test widget is installed ok
            cmd = WRT_QUERY_STR % (self.deviceid, test_wgt)
            exit_code, ret = shell_command(cmd)
            if exit_code == -1:
                return None
            print 'id', ret
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

    def stop_debug(self):
        global debug_flag
        debug_flag = False

    def launch_app(self, wgt_name):
        timecnt = 0
        blauched = False
        print 'widget', wgt_name
        cmdline = WRT_STOP_STR % (self.deviceid, wgt_name)
        exit_code, ret = shell_command(cmdline)
        cmdline = WRT_START_STR % (self.deviceid, wgt_name)
        while timecnt < 3:
            exit_code, ret = shell_command(cmdline)
            if len(ret) > 0 and ret[0].find('launched') != -1:
                blauched = True
                break
            timecnt += 1
            time.sleep(3)
        return blauched

    def kill_app(self, wgt_name):
        cmdline = WRT_STOP_STR % (self.deviceid, wgt_name)
        exit_code, ret = shell_command(cmdline)
        return True

    def install_app(self, wgt_path="", timeout=90):
        cmd = WRT_INSTALL_STR % (self.deviceid, wgt_path)
        exit_code, ret = shell_command(cmd, timeout)
        if exit_code == -1:
            cmd = APP_QUERY_STR % (self.deviceid, wgt_path)
            exit_code, ret = shell_command(cmd)
            for line in ret:
                cmd = APP_KILL_STR % (self.deviceid, line.strip('\r\n'))
                exit_code, ret = shell_command(cmd)
            return False
        else:
            return True

    def uninstall_app(self, wgt_name):
        cmd = WRT_UNINSTL_STR % (self.deviceid, wgt_name)
        exit_code, ret = shell_command(cmd)
        return True

    def get_buildinfo(self):
        """ get builf info"""
        build_info = {}
        build_info['buildid'] = ''
        build_info['manufacturer'] = ''
        build_info['model'] = ''
        return build_info


def get_target_conn(deviceid=None):
    """ Get connection for Test Target"""
    if deviceid is None or '@' not in deviceid:
        raise InvalidDeviceException('deviceid("username@ip") required by TIZEN-IVI device!')
    return tizenIVI(deviceid)
