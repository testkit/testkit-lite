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

""" The implementation of TIZEN mobile communication"""

import os
import time
import socket
import threading
import re
import shutil
import xml.etree.ElementTree as etree

from testkitlite.util.log import LOGGER
from testkitlite.util.autoexec import shell_command, shell_command_ext
from testkitlite.util.killall import killall
from testkitlite.util.errors import InvalidDeviceException

os.environ['TEST_PLATFORM'] = 'tizen'
os.environ['CONNECT_TYPE'] = 'sdb'
LOCAL_HOST_NS = "127.0.0.1"
BUILD_INFO_FILE = '/opt/usr/media/Documents/tct/buildinfo.xml'
RPM_INSTALL = "sdb -s %s shell rpm -ivh %s"
RPM_UNINSTALL = "sdb -s %s shell rpm -e %s"
RPM_LIST = "sdb -s %s shell \"rpm -qa|grep tct\""
APP_QUERY_STR = "sdb -s %s shell \"ps aux|grep '%s'|grep -v grep\"|awk '{print $2}'"
STUB_KILL_STR = "sdb -s %s shell \"ps aux|grep '%s'|grep -v grep\"|awk '{print $2}'|xargs kill -9"
APP_KILL_STR = "sdb -s %s shell kill -9 %s"
APP_NONBLOCK_STR = "sdb -s %s shell '%s' &"
SDB_COMMAND = "sdb -s %s shell '%s'"
SDB_COMMAND_RTN = "sdb -s %s shell '%s; echo returncode=$?'"
SDB_COMMAND_APP = """sdb -s %s shell 'su - %s -c "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;export TIZEN_USER=%s;%s";echo returncode=$?'"""


# wrt-launcher constants

WRT_MAIN = "wrt-launcher"
WRT_QUERY_STR = "sdb -s %s shell wrt-launcher -l | grep '%s'|awk '{print $2\":\"$NF}'"
WRT_START_STR = "sdb -s %s shell 'wrt-launcher -s %s; echo returncode=$?'"
WRT_STOP_STR = "sdb -s %s shell wrt-launcher -k %s"
WRT_INSTALL_STR = "sdb -s %s shell wrt-installer -i %s"
WRT_UNINSTL_STR = "sdb -s %s shell wrt-installer -un %s"
WRT_LOCATION = "/home/app/content/tct/opt/%s/%s.wgt"

# crosswalk constants
#XWALK_MAIN = "xwalkctl"
#XWALK_MAIN = "open_app"
XWALK_MAIN = "app_launcher -s"
#XWALK_QUERY_STR = "sdb -s %s shell su - app -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/5000/dbus/user_bus_socket;ail_list' | grep -w %s | awk '{print $(NF-1)}'"
XWALK_QUERY_STR = "sdb -s %s shell su - %s -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;ail_list' | grep -w %s | awk '{print $1}'"
#XWALK_QUERY_STR = "sdb -s %s shell su - app -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/5000/dbus/user_bus_socket;xwalkctl' | grep -w %s | awk '{print $(NF-1)}'"
#XWALK_START_STR = "sdb -s %s shell su - app -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/5000/dbus/user_bus_socket;launch_app %s' &"
XWALK_START_STR = "sdb -s %s shell su - %s -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;%s %s' &"
#XWALK_START_STR = "sdb -s %s shell su - %s -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;xwalk-launcher %s' &"
XWALK_INSTALL_STR = "sdb -s %s shell su - %s -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;pkgcmd -i -t %s -p  %s -q'"
#XWALK_INSTALL_STR = "sdb -s %s shell su - app -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/5000/dbus/user_bus_socket;xwalkctl --install %s'"
XWALK_UNINSTL_STR = "sdb -s %s shell su - %s -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/dbus/user_bus_socket;pkgcmd -u -t wgt -q -n %s'"
#XWALK_UNINSTL_STR = "sdb -s %s shell su - app -c 'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/5000/dbus/user_bus_socket;xwalkctl --uninstall %s'"
XWALK_LOCATION = "/home/%s/content/tct/opt/%s/%s.wgt"

XWALK_QUERY_ID = "sdb -s %s shell  'id -u %s'"

TIZEN_USER = os.environ.get('TIZEN_USER','app').strip()
#print os.environ['TIZEN_USER']
# dlog constants
DLOG_CLEAR = "sdb -s %s shell dlogutil -c"
DLOG_WRT = "sdb -s %s shell dlogutil -v time"

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
    """get tizen deivce list of ids"""
    result = []
    exit_code, ret = shell_command("sdb start-server")
    exit_code, ret = shell_command("sdb devices")
    for line in ret:
        if str.find(line, "\tdevice") != -1:
            result.append(line.split("\t")[0])
    return result

class TizenMobile:

    """
    Implementation for transfer data
    between Host and Tizen Mobile Device
    """

    def __init__(self, device_id=None):
        self.deviceid = device_id
        self._wrt = False
        self._xwalk = False
        self.support_remote = True
        self.get_user_id()

    def get_user_id(self):
        if TIZEN_USER == 'app':
            self.port = '5000'
        else:
            cmdline = XWALK_QUERY_ID % (self.deviceid, TIZEN_USER)
            exit_code, ret = shell_command(cmdline)
            if exit_code == -1:
                LOGGER.info("[ can not get user id ]")
            if len(ret) >0 :
                self.port = ret[0].strip('\r\n')

    def is_support_remote(self):
        return self.support_remote

    def shell_cmd(self, cmd="", timeout=15):
        cmdline = SDB_COMMAND % (self.deviceid, cmd)
        #print "cmdline : " , cmdline
        return shell_command(cmdline, timeout)

    def check_process(self, process_name):
        exit_code, ret = shell_command(
            APP_QUERY_STR % (self.deviceid, process_name))
        return len(ret)

    def kill_stub(self):
        #add this function to avoid webdriver issue if stub exists running on device,yangx.zhou@intel.com
        cmdline = APP_QUERY_STR % (self.deviceid, 'testkit-stub')
        exit_code, ret = shell_command(cmdline)
        if exit_code == 0 and len(ret) >0:
            cmdline = "kill -9 %s" %ret[0]
            exit_code, ret = self.shell_cmd(cmdline)

    def launch_stub(self, stub_app, stub_port="8000", debug_opt=""):
        #block OTCIS-3781
        cmdline = "/opt/home/developer/%s --port:%s %s; sleep 2s" % (stub_app, stub_port, debug_opt)
        exit_code, ret = self.shell_cmd(cmdline)
        time.sleep(2)

    def shell_cmd_ext(self,
                      cmd="",
                      timeout=None,
                      boutput=False,
                      stdout_file=None,
                      stderr_file=None):
        #if cmd.startswith('app_user@'):
        usr = TIZEN_USER + '_user@'
        if  cmd.find("_user@") > 0:
            cmd = cmd[cmd.index('@') - 5 :]
            cmd = TIZEN_USER + cmd

        if cmd.startswith(usr):
            cmdline = SDB_COMMAND_APP % (self.deviceid, TIZEN_USER, self.port, TIZEN_USER, cmd[cmd.index('@') + 1 :])
        else:
            cmdline = SDB_COMMAND_RTN % (self.deviceid, cmd)
        return shell_command_ext(cmdline, timeout, boutput, stdout_file, stderr_file)

    def get_device_info(self):
        """get tizen deivce inforamtion"""
        device_info = {}
        resolution_str = ""
        screen_size_str = ""
        device_model_str = ""
        device_name_str = ""
        build_id_str = ""
        os_version_str = ""

        # get resolution and screen size
        exit_code, ret = shell_command(
            "sdb -s %s shell xrandr" % self.deviceid)
        pattern = re.compile("connected (\d+)x(\d+).* (\d+mm) x (\d+mm)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))

        # get architecture
        exit_code, ret = shell_command(
            "sdb -s %s shell uname -m" % self.deviceid)
        if len(ret) > 0:
            device_model_str = ret[0]

        # get hostname
        exit_code, ret = shell_command(
            "sdb -s %s shell uname -n" % self.deviceid)
        if len(ret) > 0:
            device_name_str = ret[0]

        # get os version
        exit_code, ret = shell_command(
            "sdb -s %s shell cat /etc/issue" % self.deviceid)
        for line in ret:
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)

        # get build id
        exit_code, ret = shell_command(
            "sdb -s %s shell cat /etc/os-release" % self.deviceid)
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
        cmd = "sdb -s %s forward tcp:%s tcp:%s" % \
            (self.deviceid, host_port, remote_port)
        exit_code, ret = shell_command(cmd)
        url_forward = "http://%s:%s" % (host, host_port)
        return url_forward

    def download_file(self, remote_path, local_path):
        """download file from device"""
        local_path_dir = os.path.dirname(local_path)
        if not os.path.exists(local_path_dir):
            os.makedirs(local_path_dir)
        filename = os.path.basename(remote_path)
        cmd = "sdb -s %s pull %s %s" % (
            self.deviceid, remote_path, local_path_dir)
        exit_code, ret = shell_command(cmd)
        if exit_code != 0:
            error = ret[0].strip('\r\n') if len(ret) else "sdb shell timeout"
            LOGGER.info("[ Download file \"%s\" failed, error: %s ]"
                        % (remote_path, error))
            return False
        else:
            src_path = os.path.join(local_path_dir, filename)
            if src_path != local_path:
                shutil.move(src_path, local_path)
            return True

    def upload_file(self, remote_path, local_path):
        """upload file to device"""
        cmd = "sdb -s %s push %s %s" % (self.deviceid, local_path, remote_path)
        exit_code, ret = shell_command(cmd)
        if exit_code != 0:
            error = ret[0].strip('\r\n') if len(ret) else "sdb shell timeout"
            LOGGER.info("[ Upload file \"%s\" failed,"
                        " get error: %s ]" % (local_path, error))
            return False
        else:
            return True

    def _get_wrt_app(self, test_suite, test_set, fuzzy_match, auto_iu):
        test_app_id = None
        if auto_iu:
            test_wgt = test_set
            test_wgt_path = WRT_LOCATION % (test_suite, test_wgt)
            if not self.install_app(test_wgt_path):
                LOGGER.info("[ failed to install widget \"%s\" in target ]"
                            % test_wgt)
                return None
        else:
            test_wgt = test_suite

        # check if widget installed already
        cmd = WRT_QUERY_STR % (self.deviceid, test_wgt)
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

        return test_app_id

    def _get_xwalk_app(self, test_suite, test_set, fuzzy_match, auto_iu):
        test_app_id = None
        if auto_iu:
            test_wgt = test_set
            test_wgt_path = XWALK_LOCATION % (TIZEN_USER, test_suite, test_wgt)

            if not self.install_app(test_wgt_path):
                LOGGER.info("[ failed to install widget \"%s\" in target ]"
                            % test_wgt)
                return None
        else:
            test_wgt = test_suite

        # check if widget installed already
        cmd = XWALK_QUERY_STR % (self.deviceid, TIZEN_USER, self.port, test_wgt)
        exit_code, ret = shell_command(cmd)
        if exit_code == -1:
            return None
        for line in ret:
            test_app_id = line.strip('\r\n')
        if test_app_id is None:
            LOGGER.info("[ test widget \"%s\" not found in target ]"
                        % test_wgt)
            return None

        return test_app_id

    def get_launcher_opt(self, test_launcher, test_ext, test_widget, test_suite, test_set):
        """
        get test option dict
        """
        test_opt = {}
        self._wrt = False
        self._xwalk = False
        app_id = None
        test_opt["suite_name"] = test_suite
        test_opt["launcher"] = test_launcher
        if test_widget is not None and test_widget != "":
            test_suite = test_widget
        if test_launcher.find('WRTLauncher') >= 0:
            self._wrt = True
            test_opt["launcher"] = WRT_MAIN
            client_cmds = test_launcher.strip().split()
            wrt_tag = client_cmds[1] if len(client_cmds) > 1 else ""
            test_opt['fuzzy_match'] = fuzzy_match = wrt_tag.find('z') != -1
            test_opt['auto_iu'] = auto_iu = wrt_tag.find('iu') != -1
            test_opt['self_exec'] = wrt_tag.find('a') != -1
            test_opt['self_repeat'] = wrt_tag.find('r') != -1
            app_id = self._get_wrt_app(test_suite, test_set, fuzzy_match, auto_iu)
        elif test_launcher.find('XWalkLauncher') >= 0:
            self._xwalk = True
            test_opt["launcher"] = XWALK_MAIN
            client_cmds = test_launcher.strip().split()
            xpk_tag = client_cmds[1] if len(client_cmds) > 1 else ""
            test_opt['fuzzy_match'] = fuzzy_match = xpk_tag.find('z') != -1
            test_opt['auto_iu'] = auto_iu = xpk_tag.find('iu') != -1
            test_opt['self_exec'] = xpk_tag.find('a') != -1
            test_opt['self_repeat'] = xpk_tag.find('r') != -1
            app_id = self._get_xwalk_app(test_suite, test_set, fuzzy_match, auto_iu)
        else:
            app_id = test_launcher

        if app_id is None:
            return None
        length = len(app_id) - 1
        #test_opt["test_app_id"] = '''%s''' % app_id[1:length]
        test_opt["test_app_id"] = app_id
        return test_opt

    def install_package(self, pkgpath):
        """install a package on tizen device:
        push package and install with shell command
        """
        cmd = RPM_INSTALL % (self.deviceid, pkgpath)
        exit_code, ret = shell_command(cmd)
        return ret

    def uninstall_package(self, pkgname):
        """install a package on tizen device:
        push package and install with shell command
        """
        cmd = RPM_UNINSTALL % (self.deviceid, pkgname)
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self):
        """get list of installed package from device"""
        cmd = RPM_LIST % self.deviceid
        exit_code, ret = shell_command(cmd)
        return ret

    def start_debug(self, dlogfile):
        global debug_flag, metux
        debug_flag = True
        metux = threading.Lock()
        cmdline = DLOG_CLEAR % self.deviceid
        exit_code, ret = shell_command(cmdline)
        cmdline = DLOG_WRT % self.deviceid
        threading.Thread(target=debug_trace, args=(cmdline, dlogfile+'.dlog')).start()

    def stop_debug(self):
        global debug_flag, metux
        metux.acquire()
        debug_flag = False
        metux.release()

    def launch_app(self, wgt_name, extension=None):
        blauched = False
        if self._wrt:
            timecnt = 0
            cmdline = WRT_STOP_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmdline)
            cmdline = WRT_START_STR % (self.deviceid, wgt_name)
            while timecnt < 3:
                exit_code, ret_out, ret_err = shell_command_ext(cmdline, 30)
                if exit_code == "0":
                    blauched = True
                    break
                timecnt += 1
                time.sleep(3)
        elif self._xwalk:
            cmd = APP_QUERY_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmd)
            for line in ret:
                cmd = APP_KILL_STR % (self.deviceid, line.strip('\r\n'))
                exit_code, ret = shell_command(cmd)
            cmdline = XWALK_START_STR % (self.deviceid, TIZEN_USER, self.port, XWALK_MAIN, wgt_name)
            exit_code, ret = shell_command(cmdline)
            time.sleep(3)
            blauched = True
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
        if self._wrt:
            cmdline = WRT_STOP_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmdline)
        elif self._xwalk:
            cmd = APP_QUERY_STR % (self.deviceid, wgt_name)
            exit_code, ret = shell_command(cmd)
            for line in ret:
                cmd = APP_KILL_STR % (self.deviceid, line.strip('\r\n'))
                exit_code, ret = shell_command(cmd)
        return True

    def install_app(self, wgt_path="", timeout=90):
        if self._wrt:
            cmd = WRT_INSTALL_STR % (self.deviceid, wgt_path)
        elif self._xwalk:
            if len(wgt_path):
                 ext = wgt_path.split(".")[1]
            cmd = XWALK_INSTALL_STR % (self.deviceid, TIZEN_USER, self.port, ext, wgt_path)
        else:
            return True
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
        if self._wrt:
            cmd = WRT_UNINSTL_STR % (self.deviceid, TIZEN_USER, self.port,  wgt_name)
        elif self._xwalk:
            cmd = XWALK_UNINSTL_STR % (self.deviceid, TIZEN_USER,self.port,  wgt_name)
        else:
            return True
        exit_code, ret = shell_command(cmd)
        return True

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
            raise InvalidDeviceException('No TIZEN device found!')
    return TizenMobile(device_id)
