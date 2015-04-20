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
""" The implementation of pyunit test engine"""

import os
import time
import sys
import threading
import uuid
import StringIO
import unittest
from unittest import TestResult
from datetime import datetime
from testkitlite.util.log import LOGGER
from testkitlite.util.result import TestSetResut


DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"
result_buffer = None
class LiteTestResult(TestResult):

    """Python unittest result wrapper"""

    def startTest(self, test):
        super(LiteTestResult, self).startTest(test)
        self._case = {}
        case_full_id = test.id()
        self._case['case_id'] = case_full_id
        self._case['start_at'] = datetime.now().strftime(DATE_FORMAT_STR)

    def stopTest(self, test):
        self._case['end_at'] = datetime.now().strftime(DATE_FORMAT_STR)
        super(LiteTestResult, self).stopTest(test)
        if result_buffer is not None:
            result_buffer.extend_result([self._case])

    def addSuccess(self, test):
        super(LiteTestResult, self).addSuccess(test)
        self._case['result'] = 'PASS'

    def addError(self, test, err):
        super(LiteTestResult, self).addError(test, err)
        _, _exc_str = self.errors[-1]
        self._case['result'] = 'BLOCK'
        self._case['stdout'] = '[message]' + _exc_str

    def addFailure(self, test, err):
        super(LiteTestResult, self).addFailure(test, err)
        _, _exc_str = self.failures[-1]
        self._case['result'] = 'FAIL'
        self._case['stdout'] = '[message]' + _exc_str


def _pyunit_test_exec(test_session, cases, result_obj):
    """function for running core tests"""
    global result_buffer
    result_buffer = result_obj
    result_obj.set_status(0)
    total = unittest.TestSuite()
    for tc in cases['cases']:
        if tc['entry'].find(os.sep) != -1:
            arr = tc['entry'].split(os.sep)
            path = tc['entry'][:tc['entry'].rindex(os.sep)]
            case = arr[-1]
        else:
            path = os.getcwd()
            case = tc['entry']
        try:
            tests = unittest.TestLoader().discover(path, pattern='''%s''' %case)
            total.addTest(tests)
           # unittest.TextTestRunner(resultclass=LiteTestResult, buffer=True).run(tests)
        except ImportError as error:
            pass
    try:
        unittest.TextTestRunner(resultclass=LiteTestResult, buffer=True).run(total)
    except ImportError as error:
        pass

    #result_obj.extend_result(resultclass)
    result_obj.set_status(1)


class TestWorker(object):

    """Test executor for testkit-lite"""

    def __init__(self, conn):
        super(TestWorker, self).__init__()
        self.conn = conn
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

    def init_test(self, params):
        """init the test envrionment"""
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
       # self.opts['async_th'] = threading.Thread(
       #     target=_pyunit_test_exec,
       #     args=(sessionid, test_set['test_set_src'], test_set,  self.result_obj)
       # )
        self.opts['async_th'] = threading.Thread(
            target=_pyunit_test_exec,
            args=(sessionid, test_set, self.result_obj)
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
