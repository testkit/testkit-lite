#!/usr/bin/python
# -*- coding: utf-8 -*-
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
reload(sys)
sys.setdefaultencoding('utf-8')
import threading
import uuid
import StringIO
import unittest
from unittest import TestResult
from datetime import datetime
from testkitlite.util.log import LOGGER
from testkitlite.util.result import TestSetResut


ANDROID_UNIT_STATUS = "INSTRUMENTATION_STATUS:"
ANDROID_UNIT_STATUS_CODE = "INSTRUMENTATION_STATUS_CODE:"
ANDROID_UNIT_STATUS_LEN = len(ANDROID_UNIT_STATUS)
ANDROID_UNIT_STATUS_CODE_LEN = len(ANDROID_UNIT_STATUS_CODE)
ANDROID_UNIT_START = "am instrument -r -w -e class %s %s/android.test.InstrumentationTestRunner"
DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"
result_buffer = None

gcase_class = None
gcase_id = None
gpurpose = None
gmessage = ''


def _case_create(case_class, case_id, purpose, status, message):
    _case = dict()
    _case['case_class'] = case_class
    _case['case_id'] = case_id
    _case['purpose'] = case_id
    _case['start_at'] = datetime.now().strftime(DATE_FORMAT_STR)
    if status == '-2':
        _case['result'] = 'FAIL'
    elif status == '0':
        _case['result'] = 'PASS'
    _case['stdout'] = '[message]' + message
    _case['end_at'] = datetime.now().strftime(DATE_FORMAT_STR)
    return _case


def _adunit_lines_handler(outstr):
    """android unittest result wrapper"""
    lines = outstr.split('\r\n')
    results = []
    b_stack = False

    global gcase_class
    global gcase_id
    global gpurpose
    global gmessage

    for line in lines:
        if line.startswith(ANDROID_UNIT_STATUS):
            content = line[ANDROID_UNIT_STATUS_LEN:].strip()
            if content.startswith('class='):
                gcase_class = content[content.find('class=')+6:]
            elif content.startswith('test='):
                b_stack = False
                gcase_id = content[content.find('test=')+5:]
                gpurpose = gcase_id
            elif content.startswith('stack='):
                gmessage = content[content.find('stack=')+6:]
                b_stack = True
        elif line.startswith(ANDROID_UNIT_STATUS_CODE):
            status = line[ANDROID_UNIT_STATUS_CODE_LEN:].strip()
            if status != '1': # FAIL / PASS
                results.append(_case_create(gcase_class, gcase_id, gpurpose, status, gmessage))
                gmessage = ''
        else:
            if b_stack:
                gmessage += '\n' + line
    result_buffer.extend_result(results)


def _adunit_test_exec(conn, test_session, test_set_path, result_obj):
    """function for running core tests"""
    global result_buffer
    result_buffer = result_obj
    result_obj.set_status(0)
    checked = False
    i = 0
    for tc in test_set_path['cases']:
        LOGGER.info('[ android unit test, entry: %s ]' % tc['entry'])
        inst_pack = conn.get_installed_package(tc['entry'][:tc['entry'].rindex('.')])
        if not checked and i == 0:
            if  len(inst_pack) > 0:
                checked = True
                test_cmd = ANDROID_UNIT_START % (tc['entry'], '.'.join(tc['entry'].split('.')[:-1]))
                _code, _out, _error = conn.shell_cmd_ext(cmd=test_cmd, timeout=None, boutput=True, callbk=_adunit_lines_handler)
            else:
                i += 1
        elif checked:
            test_cmd = ANDROID_UNIT_START % (tc['entry'], '.'.join(tc['entry'].split('.')[:-1]))
            _code, _out, _error = conn.shell_cmd_ext(cmd=test_cmd, timeout=None, boutput=True, callbk=_adunit_lines_handler)
            i += 1
        else:
            pass
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
        if len(disabledlog) > 1:
            pass
        else:
            self.conn.start_debug(self.opts['debug_log_base'])
        time.sleep(1)
        self.result_obj = TestSetResut(
            self.opts['testsuite_name'], self.opts['testset_name'])
        self.opts['async_th'] = threading.Thread(
            target=_adunit_test_exec,
            args=(self.conn, sessionid, test_set, self.result_obj)
        )
       # self.opts['async_th'] = threading.Thread(
       #     target=_adunit_test_exec,
       #     args=(self.conn, sessionid, test_set['test_set_src'], self.result_obj)
       # )
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
