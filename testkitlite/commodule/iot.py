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
#           Bruce Dai <feng.dai@intel.com>

""" The implementation of IoT communication"""

import os
import time
import socket
import threading
import re
import sys
from shutil import copyfile
from testkitlite.util.log import LOGGER
from testkitlite.util.autoexec import shell_command, shell_command_ext
from testkitlite.util.killall import killall
from testkitlite.util.errors import InvalidDeviceException

try:
    import paramiko
except ImportError, err:
    LOGGER.info("Failed to import 'paramiko' module, please check your installation:")
    LOGGER.info("  You can use 'sudo pip install paramiko' to install the module!")
    sys.exit(1)


HOST_NS = "127.0.0.1"
os.environ['no_proxy'] = HOST_NS
os.environ['TEST_PLATFORM'] = 'iot'
os.environ['CONNECT_TYPE'] = 'ssh'


APP_QUERY_STR = "ssh %s \"pgrep -a '%s'|grep -v grep\"|cut -d ' ' -f1"
APP_KILL_STR = "ssh %s kill -9 %s"

SSH_COMMAND_RTN = "ssh %s \"%s\"; echo returncode=$?"

XWALK_MAIN = "xwalk"


class SSH_Handler:
    """
    long connection with login
    """

    def __init__(self, host='127.0.0.1', username='root', port=22):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(host, port, username)

    def ssh_command(self, cmd='whoami'):
        stdin, stdout, stderr = self._ssh.exec_command(cmd)
        return stdout.readlines()

    def close(self):
        if self._ssh is not None:
            self._ssh.close()


class IoT:

    """ Implementation for transfer data
        between Host and IoT devices on SSH connection
    """

    def __init__(self, deviceid="root@127.0.0.1"):
        self.deviceid = deviceid
        remotes = deviceid.split('@')
        self._ssh = SSH_Handler(remotes[1], remotes[0])
        self.support_remote = True

    def is_support_remote(self):
        return self.support_remote

    def shell_cmd(self, cmd="", timeout=15):
        cmd = "ssh %s \"%s\"" % (self.deviceid, cmd)
        return shell_command(cmd, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(APP_QUERY_STR % (self.deviceid, process_name))
        return len(ret)

    def kill_stub(self):
        cmdline = APP_QUERY_STR % (self.deviceid, "testkit-stub")
        exit_code, ret_lines = shell_command(cmdline)
        if exit_code ==0 and len(ret_lines) > 0:
            cmdline = "kill -9 %s" % ret_lines[0]
            ret_lines = self._ssh.ssh_command(cmdline)

    def launch_stub(self, stub_app, stub_port="8000", debug_opt=""):
        cmdline = "/opt/testkit/%s --port:%s %s" % (stub_app, stub_port, debug_opt)
        ret_lines = self._ssh.ssh_command(cmdline)
        time.sleep(2)

    def get_device_ids(self):
        """
            get deivce list of ids
        """
        return [self.deviceid]

    def get_device_info(self):
        """
            get iot deivce inforamtion
        """
        device_info = {}
        resolution_str = ""
        screen_size_str = ""
        device_model_str = ""
        device_name_str = ""
        build_id_str = ""
        os_version_str = ""

        # get resolution and screen size
        exit_code, ret = self.shell_cmd('export DISPLAY=:0.0;xrandr')
        pattern = re.compile("current (\d+) x (\d+), maximum (\d+) x (\d+)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))

        # get architecture
        exit_code, ret = self.shell_cmd("uname -m")
        if len(ret) > 0:
            device_model_str = ret[0].strip('\n')

        # get hostname
        exit_code, ret = self.shell_cmd("uname -n")
        if len(ret) > 0:
            device_name_str = ret[0].strip('\n')

        # get os version
        exit_code, ret = self.shell_cmd("cat /etc/issue")
        for line in ret:
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)

        # get build id
        exit_code, ret = self.shell_cmd("cat /etc/os-release")
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
        """
        get test option dict
        """
        test_opt = {}
        test_opt["launcher"] = XWALK_MAIN
        test_opt["test_app_id"] = test_suite
        return test_opt

    def start_debug(self, dlogfile):
        global debug_flag, metux
        debug_flag = True

    def stop_debug(self):
        global debug_flag
        debug_flag = False

    def launch_app(self, wgt_name, extension=None):
        blauched = False
        cmdline = "export DISPLAY=:0.0;xwalk /opt/%s/manifest.json &" % wgt_name
        exit_code, ret = self.shell_cmd(cmdline)
        time.sleep(3)
        blauched = True
        return blauched

    def kill_app(self, wgt_name):
        cmd = "pgrep -a xwalk | grep '%s/manifest.json' | cut -d ' ' -f1" % wgt_name
        exit_code, ret = self.shell_cmd(cmd)
        for line in ret:
            cmd = "kill -9 %s" % line.strip('\n')
            exit_code, ret = self.shell_cmd(cmd)
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
        raise InvalidDeviceException('deviceid("username@ip") required by SSH connection!')
    return IoT(deviceid)
