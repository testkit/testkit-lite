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
#              Liu ChengTao <liux.chengtao@intel.com>
""" The implementation for HD (host device) test mode"""

import os
import time
import socket
import threading
import re
import uuid
import ConfigParser

from datetime import datetime
from commodule.log import LOGGER
from .httprequest import get_url, http_request
from .autoexec import shell_command, shell_command_ext

HOST_NS = "127.0.0.1"
DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"


def _get_forward_connect(device_id, remote_port=None):
    """forward request a host tcp port to targe tcp port"""
    if remote_port is None:
        return None

    os.environ['no_proxy'] = HOST_NS
    host = HOST_NS
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
        except socket.error, error:
            if error.errno == 98 or error.errno == 13:
                bflag = True
        if bflag:
            inner_port += 1
        else:
            break
    host_port = str(inner_port)
    cmd = "sdb -s %s forward tcp:%s tcp:%s" % \
        (device_id, host_port, remote_port)
    exit_code, ret = shell_command(cmd)
    url_forward = "http://%s:%s" % (host, host_port)
    return url_forward


def _download_file(deviceid, remote_path, local_path):
    """download file from device"""
    cmd = "sdb -s %s pull %s %s" % (deviceid, remote_path, local_path)
    exit_code, ret = shell_command(cmd)
    if exit_code != 0:
        LOGGER.info("[ Download file \"%s\" from target failed, error: %s ]"
                    % (remote_path, ret[0].strip('\r\n')))
        return False
    else:
        return True


def _upload_file(deviceid, remote_path, local_path):
    """upload file to device"""
    cmd = "sdb -s %s push %s %s" % (deviceid, local_path, remote_path)
    exit_code, result = shell_command(cmd)
    if exit_code != 0:
        LOGGER.info("[ Upload file \"%s\" failed,"
                    " get error: %s ]" % (local_path, result))
        return False
    else:
        return True


class StubExecThread(threading.Thread):

    """stub instance serve_forever in async mode"""
    def __init__(self, cmd=None, sessionid=None):
        super(StubExecThread, self).__init__()
        self.cmdline = cmd
        self.sessionid = sessionid

    def run(self):
        stdout_file = os.path.expanduser(
            "~") + os.sep + self.sessionid + "_stdout"
        stderr_file = os.path.expanduser(
            "~") + os.sep + self.sessionid + "_stderr"
        shell_command_ext(cmd=self.cmdline,
                          timeout=None,
                          boutput=True,
                          stdout_file=stdout_file,
                          stderr_file=stderr_file)


LOCK_OBJ = threading.Lock()
TEST_SERVER_RESULT = []
TEST_SERVER_STATUS = {}


def _set_result(result_data):
    """set cases result to the global result buffer"""
    global TEST_SERVER_RESULT
    if not result_data is None:
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT["cases"].extend(result_data)
        LOCK_OBJ.release()


class CoreTestExecThread(threading.Thread):

    """ stub instance serve_forever in async mode"""
    def __init__(self, device_id, test_set_name, exetype, test_cases):
        super(CoreTestExecThread, self).__init__()
        self.test_set_name = test_set_name
        self.cases_queue = test_cases
        self.device_id = device_id
        self.exetype = exetype

    def run(self):
        """run core tests"""
        if self.cases_queue is None:
            return
        total_count = len(self.cases_queue)
        current_idx = 0
        manual_skip_all = False
        global TEST_SERVER_STATUS, TEST_SERVER_RESULT
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT = {"cases": []}
        TEST_SERVER_STATUS = {"finished": 0}
        result_list = []

        LOCK_OBJ.release()
        for test_case in self.cases_queue:
            current_idx += 1
            expected_result = "0"
            core_cmd = ""
            time_out = None
            measures = []
            retmeasures = []
            if "entry" in test_case:
                core_cmd = "sdb -s %s shell '%s ;  echo returncode=$?'" % (
                    self.device_id, test_case["entry"])
            else:
                LOGGER.info(
                    "[ Warnning: test script is empty,"
                    " please check your test xml file ]")
                continue
            if "expected_result" in test_case:
                expected_result = test_case["expected_result"]
            if "timeout" in test_case:
                time_out = int(test_case["timeout"])
            if "measures" in test_case:
                measures = test_case["measures"]
            LOGGER.info("\n[case] execute case:\nTestCase: %s\nTestEntry: %s\n"
                        "Expected Result: %s\nTotal: %s, Current: %s" % (
                        test_case['case_id'], test_case['entry'],
                        expected_result, total_count, current_idx))
            LOGGER.info("[ execute test script,"
                        "this might take some time, please wait ]")

            strtime = datetime.now().strftime(DATE_FORMAT_STR)
            LOGGER.info("start time: %s" % strtime)
            test_case["start_at"] = strtime
            if self.exetype == 'auto':
                return_code, stdout, stderr = shell_command_ext(
                    core_cmd, time_out, False)
                if return_code is not None:
                    actual_result = str(return_code)
                    if actual_result == "timeout":
                        test_case["result"] = "BLOCK"
                        test_case["stdout"] = "none"
                        test_case["stderr"] = "none"
                    else:
                        if actual_result == expected_result:
                            test_case["result"] = "pass"
                        else:
                            test_case["result"] = "fail"
                        test_case["stdout"] = stdout
                        test_case["stderr"] = stderr

                        for item in measures:
                            ind = item['name']
                            fname = item['file']
                            if fname is None:
                                continue
                            tmpname = os.path.expanduser(
                                "~") + os.sep + "measure_tmp"
                            if _download_file(self.device_id, fname, tmpname):
                                try:
                                    config = ConfigParser.ConfigParser()
                                    config.read(tmpname)
                                    item['value'] = config.get(ind, 'value')
                                    retmeasures.append(item)
                                    os.remove(tmpname)
                                except IOError, error:
                                    LOGGER.error(
                                        "[ Error: fail to parse value,"
                                        " error:%s ]\n" % error)
                        test_case["measures"] = retmeasures
                else:
                    test_case["result"] = "BLOCK"
                    test_case["stdout"] = "none"
                    test_case["stderr"] = "none"
            elif self.exetype == 'manual':
                # handle manual core cases
                try:
                    # LOGGER.infopre-condition info
                    if "pre_condition" in test_case:
                        LOGGER.info("\n****\nPre-condition: %s\n ****\n"
                                    % test_case['pre_condition'])
                    # LOGGER.infostep info
                    if "steps" in test_case:
                        for step in test_case['steps']:
                            LOGGER.info(
                                "********************\n"
                                "Step Order: %s" % step['order'])
                            LOGGER.info("Step Desc: %s" % step['step_desc'])
                            LOGGER.info(
                                "Expected: %s\n********************\n"
                                % step['expected'])
                    if manual_skip_all:
                        test_case["result"] = "N/A"
                    else:
                        while True:
                            test_result = raw_input(
                                '[ please input case result ]'
                                ' (p^PASS, f^FAIL, b^BLOCK, n^Next, d^Done):')
                            if test_result.lower() == 'p':
                                test_case["result"] = "PASS"
                                break
                            elif test_result.lower() == 'f':
                                test_case["result"] = "FAIL"
                                break
                            elif test_result.lower() == 'b':
                                test_case["result"] = "BLOCK"
                                break
                            elif test_result.lower() == 'n':
                                test_case["result"] = "N/A"
                                break
                            elif test_result.lower() == 'd':
                                manual_skip_all = True
                                test_case["result"] = "N/A"
                                break
                            else:
                                LOGGER.info(
                                    "[ Warnning: you input: '%s' is invalid,"
                                    " please try again ]" % test_result)
                except IOError, error:
                    LOGGER.info(
                        "[ Error: fail to get core manual test step,"
                        " error: %s ]\n" % error)
            strtime = datetime.now().strftime(DATE_FORMAT_STR)
            LOGGER.info("end time: %s" % strtime)
            test_case["end_at"] = strtime
            LOGGER.info("Case Result: %s" % test_case["result"])
            result_list.append(test_case)

        _set_result(result_list)
        LOCK_OBJ.acquire()
        TEST_SERVER_STATUS = {"finished": 1}
        LOCK_OBJ.release()


class WebTestExecThread(threading.Thread):

    """sdb communication for serve_forever app in async mode"""
    def __init__(self, server_url, test_set_name, test_data_queue):
        super(WebTestExecThread, self).__init__()
        self.server_url = server_url
        self.test_set_name = test_set_name
        self.data_queue = test_data_queue

    def run(self):
        """run web tests"""
        if self.data_queue is None:
            return

        set_finished = False
        err_cnt = 0
        global TEST_SERVER_RESULT, TEST_SERVER_STATUS
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT = {"cases": []}
        LOCK_OBJ.release()
        for test_block in self.data_queue:
            ret = http_request(get_url(
                self.server_url, "/set_testcase"), "POST", test_block)
            if ret is None or "error_code" in ret:
                break
            while True:
                ret = http_request(
                    get_url(self.server_url, "/check_server_status"),
                    "GET", {})

                if ret is None or "error_code" in ret:
                    err_cnt += 1
                    if err_cnt >= 3:
                        LOCK_OBJ.acquire()
                        TEST_SERVER_STATUS = {"finished": 1}
                        LOCK_OBJ.release()
                        break
                elif "finished" in ret:
                    LOCK_OBJ.acquire()
                    TEST_SERVER_STATUS = ret
                    LOCK_OBJ.release()
                    err_cnt = 0
                    # check if current test set is finished
                    if ret["finished"] == 1:
                        set_finished = True
                        ret = http_request(
                            get_url(self.server_url, "/get_test_result"),
                            "GET", {})
                        _set_result(ret["cases"])
                        break
                    # check if current block is finished
                    elif ret["block_finished"] == 1:
                        ret = http_request(
                            get_url(self.server_url, "/get_test_result"),
                            "GET", {})
                        _set_result(ret["cases"])
                        break
                time.sleep(2)

            if set_finished:
                break

UIFW_RESULT = "/opt/media/Documents/tcresult.xml"


class QUTestExecThread(threading.Thread):

    """sdb communication for Jquery Unit test suite """
    def __init__(self, deviceid="", sessionid=""):
        super(QUTestExecThread, self).__init__()
        self.device_id = deviceid
        self.test_session = sessionid

    def run(self):
        """run Qunit tests"""
        global TEST_SERVER_RESULT, TEST_SERVER_STATUS
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT = {"resultfile": ""}
        TEST_SERVER_STATUS = {"finished": 0}
        LOCK_OBJ.release()
        ls_cmd = "sdb -s %s shell ls -l %s" % (self.device_id, UIFW_RESULT)
        exit_code, ret = shell_command(ls_cmd)
        if len(ret) > 0:
            prev_stamp = ret[0]
        else:
            prev_stamp = ""
        time_stamp = ""
        prev_stamp = ""
        LOGGER.info('[ web uifw test suite start ...]')
        time_out = 600
        status_cnt = 0
        while time_out > 0:
            time.sleep(2)
            time_out -= 2
            exit_code, ret = shell_command(ls_cmd)
            if len(ret) > 0:
                time_stamp = ret[0]
            else:
                time_stamp = ""

            if time_stamp == prev_stamp:
                continue
            else:
                prev_stamp = time_stamp
                status_cnt += 1

            if status_cnt == 1:
                LOGGER.info('[ web uifw begin generating result xml ... ]')
            elif status_cnt >= 2:
                LOGGER.info('[ web uifw end generating result xml ... ]')
                result_file = os.path.expanduser(
                    "~") + os.sep + self.test_session + "_uifw.xml"
                b_ok = _download_file(self.device_id,
                                      UIFW_RESULT,
                                      result_file)
                if b_ok:
                    LOCK_OBJ.acquire()
                    TEST_SERVER_RESULT = {"resultfile": result_file}
                    LOCK_OBJ.release()
                break
        LOGGER.info('[ web uifw test suite completed ... ]')
        LOCK_OBJ.acquire()
        TEST_SERVER_STATUS = {"finished": 1}
        LOCK_OBJ.release()

WRT_INSTALL_STR = "sdb -s %s shell wrt-installer -i /opt/%s/%s.wgt"
WRT_QUERY_STR = "sdb -s %s shell wrt-launcher -l | grep %s | awk '{print $NF}'"
WRT_START_STR = "sdb -s %s shell wrt-launcher -s %s"
WRT_KILL_STR = "sdb -s %s shell wrt-launcher -k %s"


class TizenMobile:

    """ Implementation for transfer data
        between Host and Tizen Mobile Device
    """

    def __init__(self):
        self.__stub_server_url = None
        self.__test_async_shell = None
        self.__test_async_http = None
        self.__test_async_core = None
        self.__test_set_block = 100
        self.__device_id = None
        self.__test_type = None
        self.__test_auto_iu = False
        self.__test_self_exec = False
        self.__test_self_repeat = False
        self.__test_wgt = None

    def get_device_ids(self):
        """get tizen deivce list of ids"""
        result = []
        exit_code, ret = shell_command("sdb devices")
        for line in ret:
            if str.find(line, "\tdevice\t") != -1:
                result.append(line.split("\t")[0])
        return result

    def get_device_info(self, deviceid=None):
        """get tizen deivce inforamtion"""
        device_info = {}
        resolution_str = "Empty resolution"
        screen_size_str = "Empty screen_size"
        device_model_str = "Empty device_model"
        device_name_str = "Empty device_name"
        os_version_str = ""

        # get resolution and screen size
        exit_code, ret = shell_command("sdb -s %s shell xrandr" % deviceid)
        pattern = re.compile("connected (\d+)x(\d+).* (\d+mm) x (\d+mm)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))
        # get architecture
        exit_code, ret = shell_command("sdb -s %s shell uname -m" % deviceid)
        if len(ret) > 0:
            device_model_str = ret[0]
        # get hostname
        exit_code, ret = shell_command("sdb -s %s shell uname -n" % deviceid)
        if len(ret) > 0:
            device_name_str = ret[0]
        # get os version
        exit_code, ret = shell_command(
            "sdb -s %s shell cat /etc/issue" % deviceid)
        for line in ret:
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)
        os_version_str = os_version_str[0:-1]
        device_info["resolution"] = resolution_str
        device_info["screen_size"] = screen_size_str
        device_info["device_model"] = device_model_str
        device_info["device_name"] = device_name_str
        device_info["os_version"] = os_version_str
        return device_info

    def install_package(self, deviceid, pkgpath):
        """install a package on tizen device:
        push package and install with shell command
        """
        filename = os.path.split(pkgpath)[1]
        devpath = "/tmp/%s" % filename
        cmd = "sdb -s %s push %s %s" % (deviceid, pkgpath, devpath)
        exit_code, ret = shell_command(cmd)
        cmd = "sdb shell rpm -ivh %s" % devpath
        exit_code, ret = shell_command(cmd)
        return ret

    def get_installed_package(self, deviceid):
        """get list of installed package from device"""
        cmd = "sdb -s %s shell rpm -qa | grep tct" % (deviceid)
        exit_code, ret = shell_command(cmd)
        return ret

    def download_file(self, deviceid, remote_path, local_path):
        """download file from device"""
        return _download_file(deviceid, remote_path, local_path)

    def upload_file(self, deviceid, remote_path, local_path):
        """upload file to device"""
        return _upload_file(deviceid, remote_path, local_path)

    def __get_test_options(self, deviceid, test_launcher, test_suite):
        """get test option dict """
        test_opt = {}
        test_opt["suite_name"] = test_suite
        cmd = ""
        if test_launcher.find('WRTLauncher') != -1:
            test_opt["launcher"] = "wrt-launcher"
            # test suite need to be installed by commodule
            if self.__test_auto_iu:
                test_wgt = self.__test_wgt
                cmd = WRT_INSTALL_STR % (deviceid, test_suite, test_wgt)
                exit_code, ret = shell_command(cmd)
            else:
                test_wgt = test_suite

            # query the whether test widget is installed ok
            cmd = WRT_QUERY_STR % (deviceid, test_wgt)
            exit_code, ret = shell_command(cmd)
            if len(ret) == 0:
                LOGGER.info("[ test widget \"%s\" not installed in target ]"
                            % test_wgt)
                return None
            else:
                test_opt["suite_id"] = ret[0].strip('\r\n')
                self.__test_wgt = test_opt["suite_id"]
        else:
            test_opt["launcher"] = test_launcher

        return test_opt

    def __init_webtest_opt(self, deviceid, params):
        """init the test runtime, mainly process the star up of test stub"""
        if params is None:
            return None

        session_id = str(uuid.uuid1())
        cmdline = ""
        debug_opt = ""
        test_opt = None
        capability_opt = None
        stub_app = params["stub-name"]
        stub_port = "8000"
        test_launcher = params["external-test"]
        testsuite_name = params["testsuite-name"]
        client_cmds = params['client-command'].strip(' ').split(' ')
        wrt_tag = ""
        if len(client_cmds) >= 2:
            wrt_tag = client_cmds[1]

        if "debug" in params and params["debug"]:
            debug_opt = "--debug"

        if "capability" in params:
            capability_opt = params["capability"]

        if wrt_tag.find('-iu') != -1:
            self.__test_auto_iu = True
            self.__test_wgt = params["testset-name"]
        else:
            self.__test_auto_iu = False

        # this suite is automated by itself
        if wrt_tag.find('-a') != -1:
            self.__test_self_exec = True
            testsuite_name = 'tct-webuifw-tests'
        else:
            self.__test_self_exec = False

        # this suite is repeat just skip it
        if wrt_tag.find('-r') != -1:
            self.__test_self_repeat = True
            return session_id
        else:
            self.__test_self_repeat = False

        test_opt = self.__get_test_options(
            deviceid, test_launcher, testsuite_name)

        if test_opt is None:
            return None

        timecnt = 0
        blauched = False
        # test suite is executed by framework of itself, no stub process needed
        if self.__test_self_exec:
            cmdline = WRT_START_STR % (deviceid, test_opt["suite_id"])
            while timecnt < 3:
                exit_code, ret = shell_command(cmdline)
                if len(ret) > 0 and ret[0].find('launched') != -1:
                    blauched = True
                    break
                time.sleep(3)

            if not blauched:
                LOGGER.info("[ launch test widget \"%s\" but get failed! ]" %
                            test_opt["suite_name"])
                return None
            else:
                return session_id

        LOGGER.info("[ launch the stub httpserver ]")
        cmdline = "sdb shell killall %s " % stub_app
        exit_code, ret = shell_command(cmdline)
        time.sleep(2)
        cmdline = "sdb -s %s shell %s --port:%s %s" \
            % (deviceid, stub_app, stub_port, debug_opt)
        self.__test_async_shell = StubExecThread(
            cmd=cmdline, sessionid=session_id)
        self.__test_async_shell.start()
        time.sleep(2)
        self.__stub_server_url = _get_forward_connect(deviceid, stub_port)
        LOGGER.info("[ Access baseURL: %s ]" % self.__stub_server_url)

        while timecnt < 10:
            ret = http_request(get_url(
                self.__stub_server_url, "/check_server_status"), "GET", {})
            if ret is None:
                LOGGER.info("[ check server status, not ready yet! ]")
                timecnt += 1
                time.sleep(1)
                continue

            if "error_code" in ret:
                LOGGER.info("[ check server status, "
                            "get error code %d ! ]" % ret["error_code"])
                return None
            else:
                blauched = True
            break

        if blauched:
            ret = http_request(get_url(
                self.__stub_server_url, "/init_test"), "POST", test_opt)
            if "error_code" in ret:
                LOGGER.info("[ init test suite, "
                            "get error code %d ! ]" % ret["error_code"])
                return None

            if capability_opt is not None:
                ret = http_request(get_url(self.__stub_server_url,
                                           "/set_capability"),
                                   "POST", capability_opt)
            return session_id
        else:
            LOGGER.info("[ connect to server timeout! ]")
            return None

    def init_test(self, deviceid, params):
        """init the test envrionment"""
        self.__device_id = deviceid
        if "client-command" in params and params['client-command'] is not None:
            self.__test_type = "webapi"
            return self.__init_webtest_opt(deviceid, params)
        else:
            self.__test_type = "coreapi"
            return str(uuid.uuid1())

    def __run_core_test(self, sessionid, test_set_name, exetype, cases):
        """
            process the execution for core api test
        """
        self.__test_async_core = CoreTestExecThread(
            self.__device_id, test_set_name, exetype, cases)
        self.__test_async_core.start()
        return True

    def __run_web_test(self, sessionid, test_set_name, exetype, ctype, cases):
        """
            process the execution for web api test
            may be splitted to serveral blocks,
            with the unit size defined by block_size
        """
        if self.__test_self_exec:
            self.__test_async_shell = QUTestExecThread(
                deviceid=self.__device_id,
                sessionid=sessionid)
            self.__test_async_shell.start()
            return True

        if self.__test_self_repeat:
            global TEST_SERVER_RESULT, TEST_SERVER_STATUS
            result_file = os.path.expanduser(
                "~") + os.sep + sessionid + "_uifw.xml"
            b_ok = _download_file(self.__device_id,
                                  UIFW_RESULT,
                                  result_file)
            LOGGER.info('[ web uifw test suite result splitting ...]')
            if b_ok:
                TEST_SERVER_RESULT = {"resultfile": result_file}
                TEST_SERVER_STATUS = {"finished": 1}
            else:
                TEST_SERVER_RESULT = {"resultfile": ""}
                TEST_SERVER_STATUS = {"finished": 1}
            return True

        case_count = len(cases)
        blknum = 0
        if case_count % self.__test_set_block == 0:
            blknum = case_count / self.__test_set_block
        else:
            blknum = case_count / self.__test_set_block + 1

        idx = 1
        test_set_blocks = []
        while idx <= blknum:
            block_data = {}
            block_data["exetype"] = exetype
            block_data["type"] = ctype
            block_data["totalBlk"] = str(blknum)
            block_data["currentBlk"] = str(idx)
            block_data["casecount"] = str(case_count)
            start = (idx - 1) * self.__test_set_block
            if idx == blknum:
                end = case_count
            else:
                end = idx * self.__test_set_block
            block_data["cases"] = cases[start:end]
            test_set_blocks.append(block_data)
            idx += 1
        self.__test_async_http = WebTestExecThread(
            self.__stub_server_url, test_set_name, test_set_blocks)
        self.__test_async_http.start()
        return True

    def run_test(self, sessionid, test_set):
        """
            process the execution for a test set
        """
        if sessionid is None:
            return False
        if not "cases" in test_set:
            return False
        test_set_name = os.path.split(test_set["current_set_name"])[1]
        cases = test_set["cases"]
        exetype = test_set["exetype"]
        ctype = test_set["type"]
        if self.__test_type == "webapi":
            return self.__run_web_test(sessionid, test_set_name,
                                       exetype, ctype, cases)
        else:
            return self.__run_core_test(sessionid, test_set_name,
                                        exetype, cases)

    def get_test_status(self, sessionid):
        """poll the test task status"""
        if sessionid is None:
            return None
        result = {}
        result["msg"] = []
        global TEST_SERVER_STATUS
        LOCK_OBJ.acquire()
        if "finished" in TEST_SERVER_STATUS:
            result["finished"] = str(TEST_SERVER_STATUS["finished"])
        else:
            result["finished"] = "0"
        TEST_SERVER_STATUS = {"finished": 0}
        LOCK_OBJ.release()

        return result

    def get_test_result(self, sessionid):
        """get the test result for a test set """
        result = {}
        if sessionid is None:
            return result
        try:
            global TEST_SERVER_RESULT
            LOCK_OBJ.acquire()
            result = TEST_SERVER_RESULT
            LOCK_OBJ.release()
        except OSError, error:
            LOGGER.error(
                "[ Error: failed to get test result, error:%s ]\n" % error)
        return result

    def finalize_test(self, sessionid):
        """clear the test stub and related resources"""
        if sessionid is None:
            return False

        if self.__test_type == "webapi":
            if self.__test_auto_iu:
                cmd = "sdb -s %s shell wrt-installer -un %s" \
                    % (self.__device_id, self.__test_wgt)
                exit_code, ret = shell_command(cmd)

            ret = http_request(get_url(
                self.__stub_server_url, "/shut_down_server"), "GET", {})
        return True


def get_target_conn():
    """ Get connection for Test Target"""
    return TizenMobile()
