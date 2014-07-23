
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
""" The implementation of default test engine"""
import os
import time
import sys
import json
import socket
import shutil
import uuid
import threading
import re
import ConfigParser
from datetime import datetime
from tempfile import mktemp
import xml.etree.ElementTree as etree
from testkitlite.engines import test_executer
from shutil import copyfile
from testkitlite.util import tr_utils
from testkitlite.util.log import LOGGER
from testkitlite.util.result import TestSetResut

EXECUTER_POLLING_INTERVAL = 2
CNT_RETRY = 10


def initExecuter(test_env=None):
    TE = test_executer.TestExecuter(test_env)
    TE.runTestsExecuter()


def _run_webdrvier_test(self, cases, result_obj):
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
        start = (idx - 1) * self.opts['block_size']
        if idx == blknum:
            end = case_count
        else:
            end = idx * self.opts['block_size']
        block_data = cases[start:end]
        test_set_queues.append({'cases': block_data})
        idx += 1

    self.testcases = []
    get_result = False
    abort_from_set = False

    for section_json in test_set_queues:
        if result_obj.get_status() == 1:
            break
        LOGGER.info("Loading a new section for testing ...")
        time.sleep(EXECUTER_POLLING_INTERVAL)
        get_result = False
        while True:
            if result_obj.get_status() == 1:
                break
            exe_command, exe_data = self.talkWithEXE(
                'GET_STATUS', '', 0)
            if exe_command == 'GET_STATUS':
                if exe_data == 'READY':
                    exe_command, exe_data = self.talkWithEXE(
                        'TESTS', {'data': section_json}, 0)
                    if exe_command != 'TESTS' or exe_data != 'OK':
                        LOGGER.debug('Send tests failed')
                        result_obj.set_status(1)
                        break
                    continue
                elif exe_data == 'RUNNING':
                    continue
                elif exe_data == 'DONE':
                    exe_command, exe_data = self.talkWithEXE(
                        'GET_RESULTS', '', 0)
                    if exe_data is not None and len(exe_data):
                        result_obj.extend_result(exe_data['cases'])
                    get_result = True
                    break
                elif exe_data == 'ERROR':
                    LOGGER.error('Executer got error')
                    get_result = True
                    result_obj.set_status(1)
                    break
            else:
                abort_from_set = True
                result_obj.set_status(1)
                break
        if abort_from_set:
            LOGGER.error('Exit from current set execution')
            break
    result_obj.set_status(1)
    exe_command, exe_data = self.talkWithEXE(
        'TERMINAL', '', 1)


class TestWorker(object):

    """Test executor for testkit-lite"""

    def __init__(self, conn):
        super(TestWorker, self).__init__()
        self.conn = conn
        self.server_url = None
        self.result_obj = None
        self.opts = dict({'block_size': 20,
                          'test_type': None,
                          'exe_socket_buff_size': 20480,
                          'runner_proc': os.getpid(),
                          })
        self.testcases = []
        self.runner_proc = self.opts['runner_proc']
        self.exe_socket_file = os.path.expanduser(
            "~") + os.sep + str(self.runner_proc) + '.socket'
        self.exe_proc = None
        self.exe_socket = None
        self.exe_socket_connect = None

    def init_test(self, params):
        """init the test envrionment"""
        """init the test envrionment"""
        self.opts['testset_name'] = params.get('testset-name', '')
        self.opts['suite_name'] = params.get('testsuite-name', '')
        self.opts['debug_log_base'] = params.get("debug-log-base", '')
        self.opts['wd_url'] = params.get("wd_url", '')
        self.opts['target_platform'] = params.get("target_platform", '')
        self.opts['set_type'] = params.get("set_type", '')
        self.opts['set_exetype'] = params.get("set_exetype", '')
        self.opts['session_dir'] = params.get("session_dir", '')
        self.opts['log_debug'] = params.get("log_debug", '')
        self.opts['exe_socket_file'] = self.exe_socket_file
        #get tizen xw IP and appid
        if self.opts['target_platform'].upper().find('TIZEN') >= 0:
            _opts = self.conn.get_launcher_opt('xwalk', None, None, self.opts['suite_name'], self.opts['testset_name'])
            self.opts['appid'] = _opts.get("test_app_id", '') if _opts else ''
            self.opts['debugip'] = params.get("debugip", '')

        if not self.__exitExecuter():
            LOGGER.debug('__exitExecuter failed')
            return None

        if self.__initExecuterSocket():
            time.sleep(EXECUTER_POLLING_INTERVAL)
            if (not self.exe_proc) or (not tr_utils.pidExists(self.exe_proc)):
                LOGGER.debug('Executer not existing')
                return None
            else:
                timecnt = 0
                blaunched = False
                while timecnt < CNT_RETRY:
                    exe_command, exe_data = self.talkWithEXE(
                        'GET_STATUS', '', 0)
                    if exe_command == 'GET_STATUS':
                        if exe_data == 'READY':
                            blaunched = True
                            break
                    else:
                        timecnt += 1
                if not blaunched:
                    LOGGER.info("[ launch webdriver failed! ]")
                    return None
                else:
                    return str(uuid.uuid1())

    def __initExecuter(self):
        try:
            new_proc = os.fork()

            if new_proc == 0:
                initExecuter(self.opts)
                sys.exit(0)
            else:
                self.exe_proc = new_proc
                LOGGER.debug('Runner Proc: %s, Executer Proc: %s' %
                          (self.runner_proc, self.exe_proc))
                return True
        except OSError, e:
            return False

    def __exitExecuter(self):
        if self.exe_socket:
            self.exe_socket_connect.close()
            self.exe_socket.close()
        self.exe_socket = None
        try:
            os.remove(self.exe_socket_file)
        except Exception, e:
            pass

        if self.exe_proc and tr_utils.pidExists(self.exe_proc):
            if not tr_utils.KillAllProcesses(self.exe_proc):
                return False
        self.exe_proc = None
        return True

    def __initExecuterSocket(self):
        if not self.exe_socket:
            try:
                os.remove(self.exe_socket_file)
            except OSError:
                pass
            try:
                self.exe_socket = socket.socket(
                    socket.AF_UNIX, socket.SOCK_STREAM)
                self.exe_socket.bind(self.exe_socket_file)
                self.exe_socket.listen(1)
            except Exception, e:
                LOGGER.error('Setup socket failed')
                return False
            if not self.__initExecuter():
                LOGGER.error('Init Executer failed')
                if self.exe_proc and tr_utils.pidExists(self.exe_proc):
                    killProcGroup(self.exe_proc)
                self.exe_proc = None
                self.exe_socket.close()
                self.exe_socket = None
                return False
            self.exe_socket_connect, addr = self.exe_socket.accept()
        return True

    def talkWithEXE(self, command=None, data=None, recv_timeout=None):
        # LOGGER.debug('Start send: %s, %s' % (command, data))
        try:
            if self.exe_socket is None:
                return (None, None)
            self.exe_socket.settimeout(recv_timeout)
            self.exe_socket_connect.send(
                json.dumps({'COMMAND': command, 'DATA': data}))
            exe_data = self.exe_socket_connect.recv(
                self.opts['exe_socket_buff_size'])
            exe_json = json.loads(exe_data)
            if exe_json['COMMAND']:
                command = exe_json['COMMAND']
            if exe_json['DATA']:
                data = exe_json['DATA']
        except Exception, e:
            LOGGER.error('Talk with executer failed: %s, kill executer' % e)
            self.__exitExecuter()
            return (None, None)

        return (command, data)

    def __saveSectionToSetJSON(self, testcases, exe_data):
        if exe_data:
            for i_case in exe_data['cases']:
                testcases.append(i_case)

        return testcases

    def run_test(self, sessionid, test_set):
        """
            process the execution for a test set
        """
        if sessionid is None:
            return False

        if not "cases" in test_set:
            return False

        if len(test_set["cases"]) == 0:
            return False

        self.result_obj = TestSetResut(
            self.opts['suite_name'], self.opts['testset_name'])
        cases, exetype, ctype = test_set[
            "cases"], test_set["exetype"], test_set["type"]

        self.opts['async_th'] = threading.Thread(
            target=_run_webdrvier_test,
            args=(self, cases, self.result_obj)
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

        # remove socketfile

        return True
