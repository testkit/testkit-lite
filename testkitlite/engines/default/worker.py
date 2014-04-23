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
""" The implementation test worker"""

import os
import time
import socket
import threading
import re
import uuid
import ConfigParser

from datetime import datetime
from commodule.log import LOGGER
from commodule.httprequest import get_url, http_request

CNT_RETRY = 10
DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"
UIFW_MAX_TIME = 600
UIFW_RESULT = "/opt/usr/media/Documents/tcresult"
UIFW_SET_NUM = 0
LAUNCH_ERROR = 1
BLOCK_ERROR = 3


class TestSetResut(object):

    """ test result """

    _progress = "execute case: %s # %s...(%s)"
    _mutex = threading.Lock()

    def __init__(self, testsuite_name="", testset_name=""):
        self._suite_name = testsuite_name
        self._set_name = testset_name
        self._result = {"cases": []}
        self._finished = 0

    def set_status(self, flag=0):
        """set finished tag"""
        self._mutex.acquire()
        self._finished = flag
        self._mutex.release()

    def get_status(self):
        """return finished tag"""
        self._mutex.acquire()
        flag = self._finished
        self._mutex.release()
        return flag

    def set_result(self, tresult):
        """set cases result to result buffer"""
        self._mutex.acquire()
        self._result = tresult
        self._mutex.release()

    def extend_result(self, cases_result=None, print_out=True):
        """update cases result to the result buffer"""
        self._mutex.acquire()
        if cases_result is not None:
            self._result["cases"].extend(cases_result)

        if print_out:
            for case_it in cases_result:
                LOGGER.info(self._progress %
                            (self._suite_name, case_it['case_id'], case_it['result']))
                if case_it['result'].lower() in ['fail', 'block'] and 'stdout' in case_it:
                    LOGGER.info(case_it['stdout'])
        self._mutex.release()

    def get_result(self):
        """get cases result from the result buffer"""
        self._mutex.acquire()
        result = self._result
        self._mutex.release()
        return result


def _print_dlog(dlog_file):
    if os.path.exists(dlog_file):
        LOGGER.info('[ start of dlog message ]')
        readbuff = file(dlog_file, "r")
        for line in readbuff.readlines():
            LOGGER.info(line.strip('\n'))
        LOGGER.info('[ end of dlog message ]')


def _core_test_exec(conn, test_set_name, exetype, cases_queue, result_obj):
    """function for running core tests"""
    exetype = exetype.lower()
    total_count = len(cases_queue)
    current_idx = 0
    manual_skip_all = False
    result_list = []
    for test_case in cases_queue:
        if result_obj.get_status() == 1:
            break

        current_idx += 1
        core_cmd = ""
        if "entry" in test_case:
            core_cmd = test_case["entry"]
        else:
            LOGGER.info(
                "[ Warnning: test script is empty,"
                " please check your test xml file ]")
            continue
        expected_result = test_case.get('expected_result', '0')
        time_out = int(test_case.get('timeout', '90'))
        measures = test_case.get('measures', [])
        retmeasures = []
        LOGGER.info("\n[core test] execute case:\nTestCase: %s\n"
                    "TestEntry: %s\nExpected: %s\nTotal: %s, Current: %s"
                    % (test_case['case_id'], test_case['entry'],
                       expected_result, total_count, current_idx))
        LOGGER.info("[ execute core test script, please wait ! ]")
        strtime = datetime.now().strftime(DATE_FORMAT_STR)
        LOGGER.info("start time: %s" % strtime)
        test_case["start_at"] = strtime
        if exetype == 'auto':
            return_code, stdout, stderr = conn.shell_cmd_ext(
                core_cmd, time_out, False)
            if return_code is not None and return_code != "timeout":
                test_case["result"] = "pass" if str(
                    return_code) == expected_result else "fail"
                test_case["stdout"] = stdout
                test_case["stderr"] = stderr
                for item in measures:
                    ind = item['name']
                    fname = item['file']
                    if fname is None:
                        continue
                    tmpname = os.path.expanduser("~") + os.sep + "mea_tmp"
                    if conn.download_file(fname, tmpname):
                        try:
                            config = ConfigParser.ConfigParser()
                            config.read(tmpname)
                            item['value'] = config.get(ind, 'value')
                            retmeasures.append(item)
                            os.remove(tmpname)
                        except IOError as error:
                            LOGGER.error(
                                "[ Error: fail to parse value,"
                                " error:%s ]\n" % error)
                test_case["measures"] = retmeasures
            else:
                test_case["result"] = "BLOCK"
                test_case["stdout"] = stdout
                test_case["stderr"] = stderr
        elif exetype == 'manual':
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
            except IOError as error:
                LOGGER.info(
                    "[ Error: fail to get core manual test step,"
                    " error: %s ]\n" % error)
        strtime = datetime.now().strftime(DATE_FORMAT_STR)
        LOGGER.info("end time: %s" % strtime)
        test_case["end_at"] = strtime
        LOGGER.info("Case Result: %s" % test_case["result"])
        result_list.append(test_case)

    result_obj.extend_result(result_list, False)
    result_obj.set_status(1)


def _web_test_exec(conn, server_url, test_web_app, exetype, cases_queue, result_obj):
    """function for running web tests"""
    exetype = exetype.lower()
    test_set_finished = False
    err_cnt = 0
    relaunch_cnt = 0
    for test_group in cases_queue:
        if test_set_finished:
            break

        ret = http_request(
            get_url(server_url, "/set_testcase"), "POST", test_group, 30)
        if ret is None:
            LOGGER.error(
                "[ set testcases timeout, please check device! ]")
            result_obj.set_status(1)
            break

        if not conn.launch_app(test_web_app):
            result_obj.set_status(1)
            break

        while True:
            if result_obj.get_status() == 1:
                test_set_finished = True
                break
            ret = http_request(
                get_url(server_url, "/check_server_status"), "GET", {})
            if ret is None:
                err_cnt += 1
                if err_cnt >= CNT_RETRY:
                    LOGGER.error(
                        "[ check server status time out, please check deivce! ]")
                    test_set_finished = True
                    result_obj.set_status(1)
                    break
            else:
                result_cases = ret.get("cases")
                error_code = ret.get("error_code")
                if error_code is not None:
                    if not conn.launch_app(test_web_app):
                        test_set_finished = True
                        result_obj.set_status(1)
                        break
                    if error_code == LAUNCH_ERROR:
                        relaunch_cnt += 1
                        if relaunch_cnt >= 3:
                            test_set_finished = True
                            result_obj.set_status(1)
                            break
                    elif error_code == BLOCK_ERROR:
                        relaunch_cnt = 0
                else:
                    err_cnt = 0
                    relaunch_cnt = 0

                if result_cases is not None and len(result_cases):
                    result_obj.extend_result(result_cases)
                elif exetype == 'manual':
                    LOGGER.info(
                        "[ please execute manual cases ]\r\n")

                if ret["finished"] == 1:
                    test_set_finished = True
                    result_obj.set_status(1)
                    break
                elif ret["block_finished"] == 1:
                    break
            time.sleep(2)


def _webuifw_test_exec(conn, test_web_app, test_session, test_set_name, exetype, cases_queue, result_obj):
    """function for running webuifw tests"""
    global UIFW_SET_NUM
    UIFW_SET_NUM = UIFW_SET_NUM + 1
    set_UIFW_RESULT = UIFW_RESULT + "_" + str(UIFW_SET_NUM) +".xml"
    result_obj.set_status(0)
    result_obj.set_result({"resultfile": ""})
    ls_cmd = "ls -l %s" % set_UIFW_RESULT
    time_out = UIFW_MAX_TIME
    rm_cmd = "rm /opt/usr/media/Documents/tcresult*.xml"

    if exetype == "auto":
        conn.shell_cmd(rm_cmd)
        UIFW_SET_NUM = 1
        LOGGER.info('[webuifw] start test executing')
        if not conn.launch_app(test_web_app):
            LOGGER.info("[ launch test app \"%s\" failed! ]" %
                        self.opts['test_app_id'])
            result_obj.set_result({"resultfile": ""})
            result_obj.set_status(1)

    result_file = os.path.expanduser("~") + os.sep + test_session + "_uifw.xml"

    while time_out > 0:
        LOGGER.info('[webuifw] waiting for test completed...')
        exit_code, ret = conn.shell_cmd(ls_cmd)
        if 'No such file or directory' in ret[0]:
            continue
        else:
            break
        time.sleep(2)
        time_out -= 2

    LOGGER.info('[webuifw] end test executing')
    if conn.download_file(set_UIFW_RESULT, result_file):
        result_obj.set_result({"resultfile": result_file})
    for test_case in cases_queue:
        LOGGER.info("[webuifw] execute case: %s # %s" %
                    (test_set_name, test_case['case_id']))
    result_obj.set_status(1)


class TestWorker(object):

    """Test executor for testkit-lite"""

    def __init__(self, client=None):
        super(TestWorker, self).__init__()
        self.conn = client
        self.server_url = None
        self.result_obj = None
        self.opts = dict({'block_size': 300,
                          'test_type': None,
                          'auto_iu': False,
                          'fuzzy_match': False,
                          'self_exec': False,
                          'self_repeat': False,
                          'debug_mode': False
                          })

    def __init_test_stub(self, stub_app, stub_port, debug_opt):
        # init testkit-stub deamon process
        timecnt = 0
        blaunched = False
        while timecnt < CNT_RETRY:
            if not self.conn.check_process(stub_app):
                LOGGER.info("[ no stub process activated, now try to launch %s ]" % stub_app)
                self.conn.launch_stub(stub_app, stub_port, debug_opt)
                timecnt += 1
            else:
                blaunched = True
                break

        if not blaunched:
            LOGGER.info("[ launch stub process failed! ]")
            return False

        if self.server_url is None:
            self.server_url = self.conn.get_server_url(stub_port)

        timecnt = 0
        blaunched = False
        while timecnt < CNT_RETRY:
            ret = http_request(get_url(
                self.server_url, "/check_server_status"), "GET", {})
            if ret is None:
                LOGGER.info("[ check server status, not ready yet! ]")
                timecnt += 1
                time.sleep(1)
            else:
                blaunched = True
                break
        return blaunched

    def __init_webtest_opt(self, params):
        """init the test runtime, mainly process the star up of test stub"""
        if params is None:
            return None

        session_id = str(uuid.uuid1())
        cmdline = ""
        debug_opt = ""
        stub_app = params.get('stub-name', 'testkit-stub')
        stub_port = params.get('stub-port', '8000')
        test_launcher = params.get('external-test', '')
        testsuite_name = params.get('testsuite-name', '')
        testset_name = params.get('testset-name', '')
        capability_opt = params.get("capability", None)
        client_cmds = params.get('test-launcher', '').strip().split()
        wrt_tag = client_cmds[1] if len(client_cmds) > 1 else ""
        self.opts['fuzzy_match'] = fuzzy_match = wrt_tag.find('z') != -1
        self.opts['auto_iu'] = auto_iu = wrt_tag.find('iu') != -1
        self.opts['self_exec'] = wrt_tag.find('a') != -1
        self.opts['self_repeat'] = wrt_tag.find('r') != -1
        self.opts['debug_mode'] = params.get("debug", False)

        test_opt = self.conn.get_launcher_opt(
            test_launcher, testsuite_name, testset_name, fuzzy_match, auto_iu)
        if test_opt is None:
            LOGGER.info("[ init the test options, get failed ]")
            return None

        # to be removed in later version
        test_opt["suite_id"] = test_opt["test_app_id"]
        self.opts.update(test_opt)

        # uifw, this suite don't need stub
        if self.opts['self_exec'] or self.opts['self_repeat']:
            self.opts['test_type'] = "jqunit"
            return session_id

        # enable debug information
        if self.opts['debug_mode']:
            debug_opt = '--debug'

        if self.__init_test_stub(stub_app, stub_port, debug_opt):
            ret = http_request(get_url(
                self.server_url, "/init_test"), "POST", test_opt)
            if ret is None:
                LOGGER.info("[ init test suite failed! ]")
                return None
            elif "error_code" in ret:
                LOGGER.info("[ init test suite, "
                            "get error code %d ! ]" % ret["error_code"])
                return None

            if capability_opt is not None:
                ret = http_request(get_url(self.server_url,
                                           "/set_capability"),
                                   "POST", capability_opt)
            return session_id
        else:
            LOGGER.info("[ Init test failed ! ]")
            return None

    def init_test(self, params):
        """init the test envrionment"""
        self.opts['testset_name'] = params.get('testset-name', '')
        self.opts['testsuite_name'] = params.get('testsuite-name', '')
        if params.get('test-launcher') is not None:
            self.opts['test_type'] = "webapi"
            return self.__init_webtest_opt(params)
        else:
            self.opts['test_type'] = "coreapi"
            return str(uuid.uuid1())

    def __run_core_test(self, sessionid, test_set_name, exetype, cases):
        """
            process the execution for core api test
        """
        self.opts['async_th'] = threading.Thread(
            target=_core_test_exec,
            args=(
                self.conn, test_set_name, exetype, cases, self.result_obj)
        )
        self.opts['async_th'].start()
        return True

    def __run_jqt_test(self, sessionid, test_set_name, cases):
        """
            process the execution for Qunit testing
        """
        exetype = "auto" if self.opts['self_exec'] else ""
        self.opts['async_th'] = threading.Thread(
            target=_webuifw_test_exec,
            args=(
                self.conn, self.opts['test_app_id'], sessionid, test_set_name, exetype, cases, self.result_obj)
        )
        self.opts['async_th'].start()
        return True

    def __run_web_test(self, sessionid, test_set_name, exetype, ctype, cases):
        """
            process the execution for web api test
            may be splitted to serveral blocks,
            with the unit size defined by block_size
        """
        case_count = len(cases)
        blknum = 0
        if case_count % self.opts['block_size'] == 0:
            blknum = case_count / self.opts['block_size']
        else:
            blknum = case_count / self.opts['block_size'] + 1

        idx = 1
        test_set_queues = []
        while idx <= blknum:
            block_data = {}
            block_data["exetype"] = exetype
            block_data["type"] = ctype
            block_data["totalBlk"] = str(blknum)
            block_data["currentBlk"] = str(idx)
            block_data["casecount"] = str(case_count)
            start = (idx - 1) * self.opts['block_size']
            if idx == blknum:
                end = case_count
            else:
                end = idx * self.opts['block_size']
            block_data["cases"] = cases[start:end]
            test_set_queues.append(block_data)
            idx += 1
        self.opts['async_th'] = threading.Thread(
            target=_web_test_exec,
            args=(
                self.conn, self.server_url, self.opts['test_app_id'], exetype, test_set_queues, self.result_obj)
        )
        self.opts['async_th'].start()
        return True

    def run_test(self, sessionid, test_set):
        """
            process the execution for a test set
        """
        if sessionid is None:
            return False

        if not "cases" in test_set:
            return False

        # start debug trace thread
        dlogfile = test_set['current_set_name'].replace('.xml', '.dlog')
        self.opts['dlog_file'] = dlogfile
        self.conn.start_debug(dlogfile)
        time.sleep(1)

        self.result_obj = TestSetResut(
            self.opts['testsuite_name'], self.opts['testset_name'])
        cases, exetype, ctype = test_set[
            "cases"], test_set["exetype"], test_set["type"]
        if self.opts['test_type'] == "webapi":
            return self.__run_web_test(sessionid, self.opts['testset_name'], exetype, ctype, cases)
        elif self.opts['test_type'] == "coreapi":
            return self.__run_core_test(sessionid, self.opts['testset_name'], exetype, cases)
        elif self.opts['test_type'] == "jqunit":
            return self.__run_jqt_test(sessionid, self.opts['testset_name'], cases)
        else:
            LOGGER.info("[ unsupported test suite type ! ]")
            return False

    def get_test_status(self, sessionid):
        """poll the test task status"""
        if sessionid is None:
            return None
        result = {}
        result["msg"] = []
        result["finished"] = str(self.result_obj.get_status())
        return result

    def get_test_result(self, sessionid):
        """get the test result for a test set """
        result = {}
        if sessionid is None:
            return result

        result = self.result_obj.get_result()
        return result

    def finalize_test(self, sessionid):
        """clear the test stub and related resources"""
        if sessionid is None:
            return False

        self.result_obj.set_status(1)

        # stop test app
        if self.opts['test_type'] == "webapi":
            self.conn.kill_app(self.opts['test_app_id'])
            # uninstall test app
            if self.opts['auto_iu']:
                self.conn.uninstall_app(self.opts['test_app_id'])

        # stop debug thread
        self.conn.stop_debug()

        # add dlog output for debug
        if self.opts['debug_mode']:
            _print_dlog(self.opts['dlog_file'])

        return True
