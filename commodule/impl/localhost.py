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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Liu ChengTao <liux.chengtao@intel.com>

import os
import sys
import time
import socket
import threading
import subprocess
import requests
import json
import re
import uuid

def get_url(baseurl, api):
    """get full url string"""
    return "%s%s" % (baseurl, api)

def http_request(url, rtype="POST", data=None):
    """http request to the device http server"""
    result = None
    if rtype == "POST":
        headers = {'content-type': 'application/json'}
        try:
            ret = requests.post(url, data=json.dumps(data), headers=headers)
            if ret:
                result = ret.json()
        except Exception, e:
            pass
    elif rtype == "GET":
        try:        
            ret = requests.get(url, params=data)
            if ret:
                result = ret.json()
        except Exception, e:
            pass

    return result

def shell_command(cmdline):
    """sdb communication for quick return in sync mode"""
    proc = subprocess.Popen(cmdline,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    ret1 = proc.stdout.readlines()
    ret2 = proc.stderr.readlines()
    result = ret1 or ret2
    return result

lockobj = threading.Lock()
test_server_result = []
test_server_status = {}
class StubExecThread(threading.Thread):
    """sdb communication for serve_forever app in async mode"""
    def __init__(self, cmd=None, sessionid=None):
        super(StubExecThread, self).__init__()
        self.stdout = []
        self.stderr = []
        self.cmdline = cmd
        self.sessionid = sessionid

    def run(self):        
        BUFFILE1 = os.path.expanduser("~") + os.sep + self.sessionid + "_stdout"
        BUFFILE2 = os.path.expanduser("~") + os.sep + self.sessionid + "_stderr"

        LOOP_DELTA = 0.2
        wbuffile1 = file(BUFFILE1, "w")
        wbuffile2 = file(BUFFILE2, "w")
        rbuffile1 = file(BUFFILE1, "r")
        rbuffile2 = file(BUFFILE2, "r")
        proc = subprocess.Popen(self.cmdline,
                                shell=True,
                                stdout=wbuffile1,
                                stderr=wbuffile2)
        def print_log():
            """
            print the stdout/stderr log
            """
            sys.stdout.write(rbuffile1.read())
            sys.stdout.write(rbuffile2.read())
            sys.stdout.flush()

        rbuffile1.seek(0)
        rbuffile2.seek(0)
        while True:
            if not proc.poll() is None:
                break
            print_log()
            time.sleep(LOOP_DELTA)
        # print left output
        print_log()
        wbuffile1.close()
        wbuffile2.close()
        rbuffile1.close()
        rbuffile2.close()
        os.remove(BUFFILE1)
        os.remove(BUFFILE2)

class CoreTestExecThread(threading.Thread):
    """sdb communication for serve_forever app in async mode"""
    def __init__(self, device_id, test_set_name, exetype, test_cases):
        super(CoreTestExecThread, self).__init__()
        self.test_set_name = test_set_name
        self.cases_queue = test_cases
        self.device_id = device_id
        self.exetype = exetype
        global test_server_result
        lockobj.acquire()
        test_server_result = {"cases":[]}
        lockobj.release()

    def set_result(self, result_data):
        """set case result to the result buffer"""
        if not result_data is None:
            global test_server_result
            lockobj.acquire()
            test_server_result["cases"].append(result_data)
            lockobj.release()

    def run(self):
        """run core tests"""
        from autoexec import shell_exec
        global test_server_status
        if self.cases_queue is None:
            return
        total_count = len(self.cases_queue)
        current_idx = 0
        for tc in self.cases_queue:
            current_idx += 1
            lockobj.acquire()
            test_server_status = {"finished": 0}
            lockobj.release()
            expected_result = "0"
            core_cmd = ""
            time_out = None
            measures = []
            retmeasures = []
            if "entry" in tc:
                core_cmd = tc["entry"]
            else:
                print "[ Warnning: test script is empty, please check your test xml file ]"
                continue
            if "expected_result" in tc:
                expected_result = tc["expected_result"]
            if "timeout" in tc:
                time_out = int(tc["timeout"])
            if "measures" in tc:
                measures = tc["measures"]

            print "\n[case] execute case:\nTestCase: %s\nTestEntry: %s\nExpected Result: %s\nTotal: %s, Current: %s" % (tc['case_id'], tc['entry'], expected_result, total_count, current_idx)
            print "[ execute test script, this might take some time, please wait ]"
            if self.exetype == 'auto':
                return_code, stdout, stderr = shell_exec(
                    core_cmd, time_out, False)
                if return_code is not None:
                    actual_result = str(return_code)
                    if actual_result == "timeout":
                        tc["result"] = "BLOCK"
                        tc["stdout"] = "none"
                        tc["stderr"] = "none"
                    else:
                        if actual_result == expected_result:
                            tc["result"] = "pass"
                        else:
                            tc["result"] = "fail"
                        tc["stdout"] = stdout
                        tc["stderr"] = stderr

                        for m in measures:
                            ind = m['name']
                            fname = m['file']
                            if fname and os.path.exists(fname):
                                try:
                                    config = ConfigParser.ConfigParser()
                                    config.read(fname)
                                    m['value'] = config.get(ind, 'value')
                                    retmeasures.append(m)
                                except Exception, e:
                                    print "[ Error: fail to parse performance value, error: %s ]\n" % e                        
                        tc["measures"] = retmeasures
                else:
                    tc["result"] = "BLOCK"
                    tc["stdout"] = "none"
                    tc["stderr"] = "none"
            elif self.exetype == 'manual':
                # handle manual core cases
                try:
                    # print pre-condition info
                    if "pre_condition" in tc:
                        print "\n****\nPre-condition: %s\n ****\n" % tc['pre_condition']
                    # print step info
                    if "steps" in tc:
                        for step in tc['steps']:
                            print "********************\nStep Order: %s" % step['order']
                            print "Step Desc: %s" % step['step_desc']
                            print "Expected: %s\n********************\n" % step['expected']
                    while True:
                        test_result = raw_input(
                            '[ please input case result ] (p^PASS, f^FAIL, b^BLOCK, n^Next, d^Done):')
                        if test_result.lower() == 'p':
                            tc["result"] = "PASS"
                            break
                        elif test_result.lower() == 'f':
                            tc["result"] = "FAIL"
                            break
                        elif test_result.lower() == 'b':
                            tc["result"] = "BLOCK"
                            break
                        elif test_result.lower() == 'n':
                            tc["result"] = "N/A"
                            break
                        elif test_result.lower() == 'd':
                            tc["result"] = "N/A"
                            break
                        else:
                            print "[ Warnning: you input: '%s' is invalid, \
                            please try again ]" % test_result
                except Exception, error:
                    print "[ Error: fail to get core manual test step, \
                    error: %s ]\n" % error
            print "Case Result: %s" % tc["result"]
            self.set_result(tc)

        lockobj.acquire()
        test_server_status = {"finished": 1}
        lockobj.release()

class WebTestExecThread(threading.Thread):
    """sdb communication for serve_forever app in async mode"""
    def __init__(self, server_url, test_set_name, test_data_queue):
        super(WebTestExecThread, self).__init__()
        self.server_url = server_url
        self.test_set_name = test_set_name
        self.data_queue = test_data_queue
        global test_server_result
        lockobj.acquire()
        test_server_result = {"cases":[]}
        lockobj.release()

    def set_result(self, result_data):
        """set http result response to the result buffer"""
        if not result_data is None:
            global test_server_result
            lockobj.acquire()
            test_server_result["cases"].extend(result_data["cases"])
            lockobj.release()

    def run(self):
        """run web tests"""
        if self.data_queue is None:
            return
        global test_server_status
        set_finished = False
        cur_block = 0
        err_cnt = 0
        total_block = len(self.data_queue)
        for test_block in self.data_queue:
            cur_block += 1
            ret = http_request(get_url(self.server_url, "/init_test"), "POST", test_block)
            if ret is None or "error_code" in ret:
                break

            while True:
                ret = http_request(get_url(self.server_url, "/check_server_status"), \
                                   "GET", {})

                if ret is None or "error_code" in ret:
                    err_cnt += 1
                    if err_cnt >= 10:
                        lockobj.acquire()
                        test_server_status = {"finished": 1}
                        lockobj.release()
                        break
                elif "finished" in ret:
                    lockobj.acquire()
                    test_server_status = ret
                    lockobj.release()
                    err_cnt = 0
                    print "[ test suite: %s, block: %d/%d , finished: %s ]" % \
                          (self.test_set_name, cur_block, total_block, ret["finished"])
                    ### check if current test set is finished
                    if ret["finished"] == 1:
                        set_finished = True
                        ret = http_request(get_url(self.server_url, "/get_test_result"), \
                                           "GET", {})
                        self.set_result(ret)
                        break
                    ### check if current block is finished
                    elif ret["block_finished"] == 1:
                        ret =  http_request(get_url(self.server_url, "/get_test_result"), \
                                            "GET", {})
                        self.set_result(ret)
                        break
                time.sleep(2)

            if set_finished:
                break

class HostCon:
    """ Implementation for transfer data between Host and Tizen Mobile Device"""

    def __init__(self):
        self.__server_url = "http://127.0.0.1:8000"
        self.__test_async_shell = None
        self.__test_async_http = None
        self.__test_async_core = None
        self.__test_set_block = 100
        self.__device_id = None
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
        ret = shell_command("xrandr")
        pattern = re.compile("connected (\d+)x(\d+).* (\d+mm) x (\d+mm)")
        for line in ret:
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))
        # get architecture
        ret = shell_command("uname -m")
        if len(ret) > 0:
            device_model_str = ret[0]
        # get hostname
        ret = shell_command("uname -n")
        if len(ret) > 0:
            device_name_str = ret[0]
        # get os version
        ret = shell_command("cat /etc/issue")
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

    def __init_test_stub(self, deviceid,  params):
        """init the test runtime, mainly process the star up of test stub"""
        result = None
        if params is None:
            return result
        stub_name = ""
        stub_server_port = "8000"
        testsuite_name = ""
        testsuite_id = ""
        external_command = ""       
        stub_name = params["stub-name"]
        capability_opt = None
        debug_opt = ""

        if "capability" in params:
            capability_opt = params["capability"]

        if "stub-port" in params:
            stub_server_port = params["stub-port"]

        if "debug" in params:
            bvalue = params["debug"]
            if bvalue:
                debug_opt = "--debug"
           
        if not "testsuite-name" in params:
            print "\"testsuite-name\" is required for web tests!"
            return result
        else:
            testsuite_name = params["testsuite-name"]
 
        if not "external-test" in params:
            print "\"external-test\" is required for web tests!"
            return result
        else:
            external_command = params["external-test"]
            if external_command.find("WRTLauncher") != -1:
                external_command = "wrt-launcher"

        cmd = "wrt-launcher -l | grep %s | awk '{print $NF}'" %  testsuite_name
        ret = shell_command(cmd)
        if len(ret) == 0:
            print "[ test suite \"%s\" not found in device! ]" % testsuite_name
            return result
        else:
            testsuite_id = ret[0].strip('\r\n')

        ###kill the stub process###
        cmd = " killall %s " % stub_name
        ret =  shell_command(cmd)
        print "[ waiting for kill http server ]"
        time.sleep(3)

        ###launch an new stub process###
        session_id = str(uuid.uuid1())
        print "[ launch the stub app ]"
        cmdline = "%s --testsuite:%s --external-test:\"%s\" %s" % \
                  (stub_name, testsuite_id, external_command, debug_opt)
        self.__test_async_shell = StubExecThread(cmd=cmdline, sessionid=session_id)
        self.__test_async_shell.start()
        time.sleep(2)

        ###check if http server is ready for data transfer### 
        timecnt = 0
        while timecnt < 10:
            ret = http_request(get_url(self.__server_url, "/check_server_status"), "GET", {})
            if ret is None:
                print "[ check server status, not ready yet! ]"
                time.sleep(1)
                timecnt += 1
            else:
                if "error_code" in ret:
                    print "[ check server status, get error code %d ! ]" % ret["error_code"]
                    result = None
                else:
                    result = session_id
                    print "[ check server status, get ready! ]"
                    if capability_opt is not None:
                        ret = http_request(get_url(self.__server_url, "/set_capability"), "POST", capability_opt)
                break
        return result

    def init_test(self, deviceid,  params):
        """init the test envrionment"""
        self.__device_id = deviceid
        if "client-command" in params and params['client-command'] is not None:
            self.__test_type = "webapi"
            return self.__init_test_stub(deviceid, params)
        else:
            self.__test_type = "coreapi"
            return str(uuid.uuid1())

    def __run_core_test(self, test_set_name, exetype, ctype, cases):
        """
            process the execution for core api test
        """
        self.__test_async_core = CoreTestExecThread(self.__device_id, test_set_name, exetype, cases)
        self.__test_async_core.start()
        return True

    def __run_web_test(self, test_set_name, exetype, ctype, cases):
        """
            process the execution for web api test
            may be splitted to serveral blocks, with the unit size defined by block_size
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
        self.__test_async_http = WebTestExecThread(self.__server_url, test_set_name, test_set_blocks)
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
            return self.__run_core_test(test_set_name, exetype, ctype, cases)

    def get_test_status(self, sessionid):
        """poll the test task status"""
        if sessionid is None: 
            return None
        result = {}
        result["msg"] = []
        global test_server_status
        lockobj.acquire()
        if "finished" in test_server_status:
            result["finished"] = str(test_server_status["finished"])
        else:
            result["finished"] = "0"
        test_server_status = {"finished": 0}
        lockobj.release()

        return result

    def get_test_result(self, sessionid):
        """get the test result for a test set """
        result = {}
        if sessionid is None:
            return result
        try:
            global test_server_result
            lockobj.acquire()
            result = test_server_result
            lockobj.release()
        except Exception, e:
            print e

        return result

    def finalize_test(self, sessionid):
        """clear the test stub and related resources"""
        if sessionid is None: 
            return False

        if self.__test_type == "webapi":
            ret = http_request(get_url(self.__server_url, "/shut_down_server"), "GET", {})
        return True

testremote = HostCon()
