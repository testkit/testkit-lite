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

""" The implementation of local host communication"""

import os
import time
import socket
import re
from shutil import copyfile

from testkitlite.util.log import LOGGER
from testkitlite.util.autoexec import shell_command, shell_command_ext


HOST_NS = "127.0.0.1"
os.environ['no_proxy'] = HOST_NS
os.environ['TEST_PLATFORM'] = 'localhost'
os.environ['CONNECT_TYPE'] = 'local'
APP_QUERY_STR = "ps aux | grep %s | grep -v grep"


class LocalHost:

    """ Implementation for transfer data
        between Host and Tizen PC
    """

    def __init__(self):
        self.deviceid = "localhost"
        self.support_remote = False

    def is_support_remote(self):
        return self.support_remote

    def shell_cmd(self, cmd="", timeout=15):
        return shell_command(cmd, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(APP_QUERY_STR % process_name)
        return len(ret)

    def launch_stub(self, stub_app, stub_port="8000", debug_opt=""):
        cmdline = "%s --port:%s %s" % (stub_app, stub_port, debug_opt)
        exit_code, ret = self.shell_cmd(cmdline)
        time.sleep(2)

    def check_widget_process(self, wgt_name):
        return True

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
            get tizen deivce inforamtion
        """
        device_info = {}
        device_info["device_id"] = self.deviceid
        device_info["resolution"] = "N/A"
        device_info["screen_size"] = "N/A"
        device_info["device_model"] = "N/A"
        device_info["device_name"] = "N/A"
        device_info["os_version"] = "N/A"
        device_info["build_id"] = "N/A"
        return device_info

    def get_server_url(self, remote_port="8000"):
        """get server url"""
        url_forward = "http://%s:%s" % (HOST_NS, remote_port)
        return url_forward

    def install_package(self, pkgpath):
        """
           install a package on tizen device
        """
        cmd = "rpm -ivh %s" % pkgpath
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self):
        """get list of installed package from device"""
        cmd = "rpm -qa | grep tct"
        exit_code, ret = shell_command(cmd)
        return ret

    def download_file(self, remote_path, local_path):
        """download file"""
        # copyfile(remote_path, local_path)
        # return True
        return False

    def upload_file(self, remote_path, local_path):
        """upload file"""
        # copyfile(local_path, remote_path)
        return False

    def get_launcher_opt(self, test_launcher, test_ext, test_widget, test_suite, test_set):
        """get test option dict """
        test_opt = {}
        test_opt["suite_name"] = test_suite
        test_opt["launcher"] = test_launcher
        test_opt["test_app_id"] = test_launcher
        return test_opt

    def launch_app(self, wgt_name):
        exit_code, ret = shell_command(wgt_name + '&')
        return True

    def kill_app(self, wgt_name):
        return True

    def start_debug(self, dlogfile):
        pass

    def stop_debug(self):
        pass

    def get_buildinfo(self):
        """ get builf info"""
        build_info = {}
        build_info['buildid'] = ''
        build_info['manufacturer'] = ''
        build_info['model'] = ''
        return build_info


def get_target_conn():
    """ Get connection for Test Target"""
    return LocalHost()
