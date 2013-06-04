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
#              Liu ChengTao <liux.chengtao@intel.com>
""" The implementation for local mode"""

import os
import time
import threading
import re
import uuid
import ConfigParser
from datetime import datetime
from commodule.log import LOGGER
from .httprequest import get_url, http_request
from .autoexec import shell_command, shell_command_ext


DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"
HOST_NS = "127.0.0.1"
os.environ["no_proxy"] = HOST_NS


class StubExecThread(threading.Thread):

    """ stub instance serve_forever in async mode"""
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


def _get_test_options(test_launcher, test_suite):
    """get test option dict """
    test_opt = {}
    if test_launcher.find('WRTLauncher') != -1:
        test_opt["launcher"] = "wrt-launcher"
        cmd = "wrt-launcher -l | grep %s | awk '{print $NF}'" % test_suite
        exit_code, ret = shell_command(cmd)
        if len(ret) == 0:
            LOGGER.info("[ test suite \"%s\" not found in target ]"
                        % test_suite)
            return None
        else:
            test_opt["suite_id"] = ret[0].strip('\r\n')
    else:
        test_opt["launcher"] = test_launcher

    test_opt["suite_name"] = test_suite
    return test_opt


def _set_result(result_data):
    """set cases result to the global result buffer"""
    global TEST_SERVER_RESULT
    if not result_data is None:
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT["cases"].extend(result_data)
        LOCK_OBJ.release()


class CoreTestExecThread(threading.Thread):

    """sdb communication for serve_forever app in async mode"""
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
        result_list = []

        global TEST_SERVER_STATUS, TEST_SERVER_RESULT
        LOCK_OBJ.acquire()
        TEST_SERVER_RESULT = {"cases": []}
        TEST_SERVER_STATUS = {"finished": 0}
        LOCK_OBJ.release()
        for test_case in self.cases_queue:
            current_idx += 1
            expected_result = "0"
            core_cmd = ""
            time_out = None
            measures = []
            retmeasures = []
            if "entry" in test_case:
                core_cmd = test_case["entry"]
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
                    cmd=core_cmd, timeout=time_out, boutput=False)
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
                            if fname and os.path.exists(fname):
                                try:
                                    config = ConfigParser.ConfigParser()
                                    config.read(fname)
                                    item['value'] = config.get(ind, 'value')
                                    retmeasures.append(item)
                                except IOError, error:
                                    LOGGER.error(
                                        "[ Error: failed to parse value,"
                                        " error: %s ]\n" % error)
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
                                    % test_case[
                                    'pre_condition'])
                    # LOGGER.infostep info
                    if "steps" in test_case:
                        for step in test_case['steps']:
                            LOGGER.info(
                                "********************\nStep Order: %s"
                                % step['order'])
                            LOGGER.info("Step Desc: %s" % step['step_desc'])
                            LOGGER.info(
                                "Expected: %s\n********************\n"
                                % step['expected'])
                    if manual_skip_all:
                        test_case["result"] = "N/A"
                    else:
                        while True:
                            test_result = raw_input(
                                '[ please input case result ] '
                                '(p^PASS, f^FAIL, b^BLOCK, n^Next, d^Done):')
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
                                    "[ Warning: you input: '%s' is invalid,"
                                    " please try again ]" % test_result)
                except IOError, error:
                    LOGGER.error(
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
        global TEST_SERVER_STATUS, TEST_SERVER_RESULT
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


class HostCon:

    """ Implementation for transfer data to Test Target in Local Host"""

    def __init__(self):
        self.__test_set_block = 100
        self.__device_id = None
        self.__server_url = None
        self.__test_async_shell = None
        self.__test_async_http = None
        self.__test_async_core = None
        self.__test_type = None

    def get_device_ids(self):
        """get tizen deivce list of ids"""
        return ['localhost']

    def get_device_info(self, deviceid=None):
        """get tizen deivce inforamtion"""
        device_info = {}
        resolution_str = "Empty resolution"
        screen_size_str = "Empty screen_size"
        device_model_str = "Empty device_model"
        device_name_str = "Empty device_name"
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
        os_version_str = os_version_str[0:-1]
        device_info["resolution"] = resolution_str
        device_info["screen_size"] = screen_size_str
        device_info["device_model"] = device_model_str
        device_info["device_name"] = device_name_str
        device_info["os_version"] = os_version_str
        return device_info

    def __init_webtest_opt(self, params):
        """init the test runtime, mainly process the star up of test stub"""
        if params is None:
            return None

        session_id = str(uuid.uuid1())
        debug_opt = ""
        test_opt = None
        capability_opt = None
        stub_app = params["stub-name"]
        stub_port = "8000"
        test_launcher = params["external-test"]
        testsuite_name = params["testsuite-name"]

        if "debug" in params and params["debug"]:
            debug_opt = "--debug"

        if "capability" in params:
            capability_opt = params["capability"]

        test_opt = _get_test_options(test_launcher, testsuite_name)
        if test_opt is None:
            return None

        LOGGER.info("[ launch the stub httpserver ]")
        cmdline = " killall %s " % stub_app
        exit_code, ret = shell_command(cmdline)
        time.sleep(2)
        cmdline = "%s --port:%s %s" % (stub_app, stub_port, debug_opt)
        self.__test_async_shell = StubExecThread(
            cmd=cmdline, sessionid=session_id)
        self.__test_async_shell.start()
        time.sleep(2)
        self.__server_url = "http://%s:%s" % (HOST_NS, stub_port)

        timecnt = 0
        blaunched = False
        while timecnt < 10:
            time.sleep(1)
            ret = http_request(get_url(self.__server_url,
                                       "/check_server_status"), "GET", {})
            if ret is None:
                LOGGER.info("[ check server status, not ready yet! ]")
                timecnt += 1
                continue

            if "error_code" in ret:
                LOGGER.info("[ check server status, "
                            "get error code %d ! ]" % ret["error_code"])
                return None
            else:
                LOGGER.info("[ check server status, get ready! ]")
                blaunched = True
            break

        if blaunched:
            ret = http_request(get_url(self.__server_url,
                                       "/init_test"),
                               "POST", test_opt)
            if "error_code" in ret:
                LOGGER.info("[ init test suite, "
                            "get error code %d ! ]" % ret["error_code"])
                return None

            if capability_opt is not None:
                ret = http_request(get_url(self.__server_url,
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
            return self.__init_webtest_opt(params)
        else:
            self.__test_type = "coreapi"
            return str(uuid.uuid1())

    def __run_core_test(self, test_set_name, exetype, cases):
        """
            process the execution for core api test
        """
        self.__test_async_core = CoreTestExecThread(
            self.__device_id, test_set_name, exetype, cases)
        self.__test_async_core.start()
        return True

    def __run_web_test(self, test_set_name, exetype, ctype, cases):
        """
            process the execution for web api test
            with the unit size defined by block_size
        """
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
            self.__server_url, test_set_name, test_set_blocks)
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
            return self.__run_web_test(test_set_name, exetype, ctype, cases)
        else:
            return self.__run_core_test(test_set_name, exetype, cases)

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
                "[ Error: failed to get test result, error: %s ]\n" % error)

        return result

    def finalize_test(self, sessionid):
        """clear the test stub and related resources"""
        if sessionid is None:
            return False

        if self.__test_type == "webapi":
            ret = http_request(get_url(
                self.__server_url, "/shut_down_server"), "GET", {})
            if ret:
                return True
        return False


def get_target_conn():
    """ Get connection for Test Target"""
    return HostCon()
