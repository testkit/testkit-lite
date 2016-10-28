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
#           Bruce Dai  <feng.dai@intel.com>
""" The implementation of mocha test engine"""

import commands
import os
import time
import sys
import threading
import uuid
from testkitlite.util.log import LOGGER
from testkitlite.util.result import TestSetResut
from testkitlite.util import tr_utils
import subprocess

STR_PASS = 'PASS'
STR_FAIL = 'FAIL'
STR_BLOCK = 'BLOCK'
DEFAULT_TIMEOUT = 90

def _mocha_test_exec(test_session, cases, result_obj, session_dir):
    """function for running mocha tests"""
    result_obj.set_status(0)
    result_list = []
    for i_case in cases['cases']:
        i_case_timeout = i_case.get('timeout', DEFAULT_TIMEOUT)

        try:
            case_entry = i_case['entry']
            status, output =  commands.getstatusoutput("ssh %s 'ls %s'" %  (os.environ["DEVICE_ID"], case_entry))
            if status != 0:
                i_case['result'] = STR_BLOCK
                i_case['stdout'] = "[Message]No such file or dirctory: %s" % case_entry
                result_list.append(i_case)
                continue

            case_id = i_case['case_id']
            tmp_result_dir = "%s/json_results" % session_dir
            os.makedirs(tmp_result_dir)
            popen_args = "ssh %s 'mocha %s --reporter json' > %s/%s.json" % (os.environ["DEVICE_ID"], case_entry, tmp_result_dir, case_id)
            i_case_proc = subprocess.Popen(args=popen_args, shell=True)
            i_case_pre_time = time.time()
            while True:
                i_case_exit_code = i_case_proc.poll()
                i_case_elapsed_time = time.time() - i_case_pre_time
                if i_case_exit_code == None:
                    if i_case_elapsed_time >= i_case_timeout:
                        tr_utils.KillAllProcesses(ppid=i_case_proc.pid)
                        i_case['result'] = STR_BLOCK
                        i_case['stdout'] = "[Message]Timeout"
                        LOGGER.debug("Run %s timeout" % case_id)
                        break
                else:
                    i_case['result'] = STR_FAIL
                    i_case['stdout'] = tmp_result_dir
                    break
                time.sleep(1)
        except Exception, e:
           i_case['result'] = STR_BLOCK
           i_case['stdout'] = "[Message]%s" % e
           LOGGER.error(
               "Run %s: failed: %s, exit from executer" % (case_id, e))
        result_list.append(i_case)
    result_obj.extend_result(result_list)
    result_obj.set_status(1)


class TestWorker(object):

    """Test executor for testkit-lite"""

    def __init__(self, conn):
        super(TestWorker, self).__init__()
        self.conn = conn
        self.server_url = None
        self.result_obj = None
        self.session_dir = None
        self.opts = dict({'block_size': 300,
                          'test_type': None,
                          'auto_iu': False,
                          'fuzzy_match': False,
                          'self_exec': False,
                          'self_repeat': False,
                          'debug_mode': False
                          })

    def init_test(self, params):
        """init the test envrionment"""
        self.session_dir =params.get('session_dir', '')
        self.opts['testset_name'] = params.get('testset-name', '')
        self.opts['testsuite_name'] = params.get('testsuite-name', '')
        self.opts['debug_log_base'] = params.get("debug-log-base", '')
        return str(uuid.uuid1())

    def run_test(self, sessionid, test_set):
        """
            process the execution for a test set
        """
        if sessionid is None:
            return False
        disabledlog = os.environ.get("disabledlog","")
        # start debug trace thread
        if len(disabledlog) > 0 :
            pass
        else:
            self.conn.start_debug(self.opts['debug_log_base'])
        time.sleep(1)
        self.result_obj = TestSetResut(
            self.opts['testsuite_name'], self.opts['testset_name'])
        self.opts['async_th'] = threading.Thread(
            target=_mocha_test_exec,
            args=(sessionid, test_set, self.result_obj, self.session_dir)
        )

        self.opts['async_th'].start()
        return True

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

        if self.result_obj is not None:
            self.result_obj.set_status(1)

        # stop debug thread
        self.conn.stop_debug()

        return True
