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

""" The implementation of Android communication driver"""

import os
import time
import socket
import threading
import re

from testkitlite.util.log import LOGGER
from testkitlite.util.autoexec import shell_command, shell_command_ext
from testkitlite.util.killall import killall
from testkitlite.util.errors import InvalidDeviceException


os.environ['TEST_PLATFORM'] = 'android'
os.environ['CONNECT_TYPE'] = 'adb'
LOCAL_HOST_NS = "127.0.0.1"
APP_QUERY_STR = "adb -s %s shell ps | grep %s | awk '{print $2}' "
APK_INSTALL = "adb -s %s shell pm install %s"
APK_UNINSTALL = "adb -s %s shell pm uninstall %s"
APK_LIST = "adb -s %s shell pm list packages |grep '%s'|cut -d ':' -f2"
APP_NONBLOCK_STR = "adb -s %s shell '%s' &"
APP_START = "adb -s %s shell am start -n %s"
APP_STOP = "adb -s %s shell am force-stop %s"
XWALK_APP_STR = "org.xwalk.%s/.%sActivity"


LOGCAT_CLEAR = "adb -s %s shell logcat -c"
LOGCAT_START = "adb -s %s shell logcat -v time"
DMESG_CLEAR = "adb -s %s shell dmesg -c"
DMESG_START = "adb -s %s shell cat /proc/kmsg"


def debug_trace(cmdline, logfile):
    global debug_flag, metux
    wbuffile = file(logfile, "a")
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


def _get_device_ids():
    """get android deivce list of ids"""
    result = []
    exit_code, ret = shell_command("adb devices")
    for line in ret:
        if str.find(line, "\tdevice") != -1:
            result.append(line.split("\t")[0])
    return result


class AndroidMobile:

    """ Implementation for transfer data
        between Host and Android Mobile Device
    """

    def __init__(self, device_id=None):
        self.deviceid = device_id
        self.support_remote = True

    def is_support_remote(self):
        return self.support_remote

    def shell_cmd(self, cmd="", timeout=15):
        cmdline = "adb -s %s shell %s" % (self.deviceid, cmd)
        return shell_command(cmdline, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(
            APP_QUERY_STR % (self.deviceid, process_name))
        return len(ret)

    def kill_stub(self):
        #add this function to avoid webdriver issue, yangx.zhou@intel.com,2015.01.15
        wgt_name = "testkit.stub/.TestkitStub"
        pkg_name = wgt_name.split('/')[0]
        cmdline = APP_STOP % (self.deviceid, pkg_name)
        exit_code, ret = shell_command(cmdline)


    def launch_stub(self, stub_app, stub_port="8000", debug_opt=""):
       # self.kill_stub()
        wgt_name = "testkit.stub/.TestkitStub"
       # pkg_name = wgt_name.split('/')[0]
       # cmdline = APP_STOP % (self.deviceid, pkg_name)
       # exit_code, ret = shell_command(cmdline)
        cmdline = APP_START % (self.deviceid, wgt_name)
        debug_ext = " -e debug on" if debug_opt != "" else " -e debug off"
        port_ext = " -e port " + stub_port
        exit_code, ret = shell_command(cmdline + port_ext + debug_ext)
        time.sleep(2)
        return True

    def shell_cmd_ext(self,
                      cmd="",
                      timeout=None,
                      boutput=False,
                      stdout_file=None,
                      stderr_file=None,
                      callbk=None):
        cmdline = "adb -s %s shell '%s; echo returncode=$?'" % (
            self.deviceid, cmd)
        return shell_command_ext(cmdline, timeout, boutput, stdout_file, stderr_file, callbk)

    def get_device_info(self):
        """get android deivce inforamtion"""
        device_info = {}
        device_info["device_id"] = self.deviceid
        device_info["resolution"] = "N/A"
        device_info["screen_size"] = "N/A"
        device_info["device_model"] = "N/A"
        device_info["device_name"] = "N/A"
        device_info["os_version"] = "N/A"
        device_info["build_id"] = "N/A"
        return device_info

    def download_file(self, remote_path, local_path):
        """download file from device"""
        cmd = "adb -s %s pull %s %s" % (self.deviceid, remote_path, local_path)
        exit_code, ret = shell_command(cmd)
        if exit_code != 0:
            error = ret[0].strip('\r\n') if len(ret) else "sdb shell timeout"
            LOGGER.info("[ Download file \"%s\" failed, error: %s ]"
                        % (remote_path, error))
            return False
        else:
            return True

    def upload_file(self, remote_path, local_path):
        """upload file to device"""
        cmd = "adb -s %s push %s %s" % (self.deviceid, local_path, remote_path)
        exit_code, ret = shell_command(cmd)
        if exit_code != 0:
            error = ret[0].strip('\r\n') if len(ret) else "sdb shell timeout"
            LOGGER.info("[ Upload file \"%s\" failed,"
                        " get error: %s ]" % (local_path, error))
            return False
        else:
            return True

    def get_launcher_opt(self, test_launcher, test_ext, test_widget, test_suite, test_set):
        """get test option dict """
        test_opt = {}
        test_opt["suite_name"] = test_suite
        test_opt["launcher"] = test_launcher
        if test_launcher.find('xwalk') >= 0:
            if test_widget is not None and test_widget != "":
                test_suite = test_widget
            test_suite = test_suite.replace('-', '_')
            test_opt["test_app_id"] = XWALK_APP_STR % (test_suite, test_suite)
        else:
            test_opt["test_app_id"] = test_launcher
        return test_opt

    def get_server_url(self, remote_port="8000"):
        """forward request a host tcp port to targe tcp port"""
        if remote_port is None:
            return None

        os.environ['no_proxy'] = LOCAL_HOST_NS
        host = LOCAL_HOST_NS
        inner_port = 9000
        time_out = 2
        bflag = False
        while True:
            sock_inner = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_inner.settimeout(time_out)
            try:
                sock_inner.bind((host, inner_port))
                sock_inner.close()
                bflag = False
            except socket.error as error:
                if error.errno == 98 or error.errno == 13:
                    bflag = True
            if bflag:
                inner_port += 1
            else:
                break
        host_port = str(inner_port)
        cmd = "adb -s %s forward tcp:%s tcp:%s" % \
            (self.deviceid, host_port, remote_port)
        exit_code, ret = shell_command(cmd)
        url_forward = "http://%s:%s" % (host, host_port)
        return url_forward

    def install_package(self, pkgpath):
        """install a package on android device:
        push package and install with shell command
        """
        cmd = APK_INSTALL % (self.deviceid, pkgpath)
        exit_code, ret = shell_command(cmd)
        return ret

    def uninstall_package(self, pkgname):
        """install a package on android device:
        push package and install with shell command
        """
        cmd = APK_UNINSTALL % (self.deviceid, pkgname)
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self):
        """get list of installed package from device"""
        cmd = APK_LIST % self.deviceid
        exit_code, ret = shell_command(cmd)
        return ret

    def start_debug(self, dlogfile):
        global debug_flag, metux
        debug_flag = True
        metux = threading.Lock()
        logcat_cmd = LOGCAT_CLEAR % self.deviceid
        exit_code, ret = shell_command(logcat_cmd)
        dmesg_cmd = DMESG_CLEAR % self.deviceid
        exit_code, ret = shell_command(logcat_cmd)
        logcat_cmd = LOGCAT_START % self.deviceid
        dmesg_cmd = DMESG_START % self.deviceid
        threading.Thread(target=debug_trace, args=(logcat_cmd, dlogfile+'.logcat')).start()
        threading.Thread(target=debug_trace, args=(dmesg_cmd, dlogfile+'.dmesg')).start()

    def stop_debug(self):
        global debug_flag, metux
        metux.acquire()
        debug_flag = False
        metux.release()

    def launch_app(self, wgt_name):
        blauched = False
        if wgt_name.find('xwalk') != -1:
            timecnt = 0
            blauched = False
            pkg_name, actv_name = wgt_name.split('/')
            actv_name = actv_name.strip('.')
            cmdline = APP_STOP % (self.deviceid, pkg_name)
            exit_code, ret = shell_command(cmdline)
            cmdline = APP_START % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmdline)
            if len(ret) > 1:
                # remove Activity to retry
                actv_name = actv_name.replace('Activity', '')
                LOGGER.info("[ Retry to launch app: %s ]" % (pkg_name + '/.' + actv_name))
                cmdline = APP_START % (self.deviceid, pkg_name + '/.' + actv_name)
                exit_code, ret = shell_command(cmdline)
            if len(ret) > 1:
                # use capitalize to retry
                tmps = actv_name.split('_')
                actv_name = ''.join([it.capitalize() for it in tmps if it])
                LOGGER.info("[ Retry to launch app: %s ]" % (pkg_name + '/.' + actv_name + 'Activity'))
                cmdline = APP_START % (self.deviceid, pkg_name + '/.' + actv_name + 'Activity')
                exit_code, ret = shell_command(cmdline)
                if len(ret) > 1:
                    # remove Activity
                    LOGGER.info("[ Retry to launch app: %s ]" % (pkg_name + '/.' + actv_name))
                    cmdline = APP_START % (self.deviceid, pkg_name + '/.' + actv_name)
                    exit_code, ret = shell_command(cmdline)

            blauched = True
            time.sleep(3)
        else:
            cmdline = APP_NONBLOCK_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmdline)
            time.sleep(3)
            cmd = APP_QUERY_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmd)
            if ret and len(ret):
                blauched = True
        return blauched

    def kill_app(self, wgt_name):
        pkg_name = wgt_name.split('/')[0]
        cmdline = APP_STOP % (self.deviceid, pkg_name)
        exit_code, ret = shell_command(cmdline)        
        return True

    install_app = install_package
    uninstall_app = uninstall_package

    def get_buildinfo(self):
        """ get builf info"""
        build_info = {}
        build_info['buildid'] = ''
        build_info['manufacturer'] = ''
        build_info['model'] = ''
        return build_info


def get_target_conn(device_id=None):
    """ Get connection for Test Target"""
    if device_id is None:
        dev_list = _get_device_ids()
        if len(dev_list):
            device_id = dev_list[0]
        else:
            raise InvalidDeviceException('No android device found!')
    return AndroidMobile(device_id)
