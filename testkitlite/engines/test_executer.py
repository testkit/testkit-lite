import os
import re
import time
import sys
import thread
import threading
import socket
import json
import hashlib
import signal
import logging
import subprocess
import ConfigParser
from testkitlite.util import tr_utils
from testkitlite.util.log import LOGGER as g_logger
from urlparse import urlparse

try:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError, err:
    g_logger.info("Failed to import 'selenium' module, please check your installation:")
    g_logger.info("  You can use 'sudo pip install selenium' to install the module!")
    raise ImportError

TE = None
EXE_LOCK = threading.Lock()
DEFAULT_TIMEOUT = 90
REF_SET_TYPE = 'ref'
JS_SET_TYPE = 'js'
QUNIT_SET_TYPE = 'qunit'
STR_PASS = 'PASS'
STR_FAIL = 'FAIL'
STR_BLOCK = 'BLOCK'
STR_NOTRUN = 'n/a'
DEFAULT_WD_URL = 'http://127.0.0.1:9515'
MH_FILE = "/opt/testkit/lite/mh.html"


class TestExecuter:

    def __init__(self, test_env=None):
        self.runner_proc = test_env['runner_proc']
        self.exe_thread = None
        self.exe_status = 'READY'
        self.tests_json = ''
        self.target_platform = test_env['target_platform']
        self.web_driver = None
        self.wd_url = test_env.get("wd_url", '') or DEFAULT_WD_URL
        self.suite_name = test_env['suite_name']
        self.set_type = test_env['set_type']
        self.set_exetype = test_env['set_exetype']
        self.test_prefix = ''
        self.exe_socket_file = test_env['exe_socket_file']
        self.exe_socket_buff_size = test_env['exe_socket_buff_size']
        self.exe_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.exe_socket.connect(self.exe_socket_file)
        self.TE_LOG = g_logger
        self.debugip = test_env.get("debugip", '')
        self.appid = test_env.get("appid", '')
        self.launcher = test_env.get('launcher','')
        self.pre_url = ''
        signal.signal(signal.SIGINT, self.__exitHandler)
        signal.signal(signal.SIGTERM, self.__exitHandler)

    def __exitHandler(self, a, b):
        if self.web_driver:
            self.web_driver.quit()
            self.web_driver = None
        with EXE_LOCK:
            self.exe_status = 'DONE'

    def __updateTestPrefix(self):
        if self.target_platform.upper().find('ANDROID') >= 0:
            url_components = urlparse(self.web_driver.current_url)
            if url_components.scheme == 'http':
                self.test_prefix = '%s://%s/' % (url_components.scheme,
                                                 url_components.netloc)
        elif self.target_platform.upper().find('TIZEN') >=0:
            url_components = urlparse(self.web_driver.current_url)
            self.test_prefix = '%s://%s/' % (url_components.scheme,
                               url_components.netloc)

    def __initWebDriver(self):
        from selenium import webdriver
        self.TE_LOG.info('init web driver')
        if self.web_driver:
            self.web_driver.quit()
            self.web_driver = None

        test_app = test_ext = ''
        driver_env = {}
        try:
            exec 'from testkitlite.capability.%s import initCapability' % self.target_platform
            if self.target_platform.upper().find('TIZEN') >= 0:
                test_app = self.appid
                test_ext = self.debugip
                capa = {'xwalkOptions': {'tizenAppId': test_app[1:-1], 'tizenDebuggerAddress': test_ext}}
                driver_env = initCapability(test_app, test_ext)
                self.test_prefix = driver_env['test_prefix']
                self.web_driver = WebDriver(self.wd_url, capa)
                url_compon = urlparse(self.web_driver.current_url)
                self.__updateTestPrefix()

            elif self.target_platform.upper().find('ANDROID') >= 0 and self.launcher != "CordovaLauncher":
                test_app, test_ext = self.appid.split('/')
                test_ext = test_ext.strip('.').replace('Activity', '')
                tmps = test_ext.split('_')
                actv_name = ''.join([it.capitalize() for it in tmps if it])
                test_ext = '.%sActivity' % actv_name
                #driver_env = initCapability(test_app, test_ext)
                #capa = driver_env['desired_capabilities']
                driver_env = initCapability(test_app, test_ext)
                capa = driver_env['desired_capabilities']
                self.test_prefix = driver_env['test_prefix']
                self.web_driver = WebDriver(self.wd_url, capa)
                url_compon = urlparse(self.web_driver.current_url)
                self.__updateTestPrefix()

            elif self.target_platform.upper().find('ANDROID') >= 0 and self.launcher == "CordovaLauncher":
                test_app, test_ext = self.appid.split('/')
                test_ext = test_ext.replace('Activity', '')

                self.TE_LOG.info('activity : %s' %test_ext)
                driver_env = initCapability(test_app, test_ext)
                self.test_prefix = driver_env['test_prefix']
                self.web_driver = WebDriver(self.wd_url, driver_env['desired_capabilities'])
                time.sleep(1)
                self.__updateTestPrefix()
        except Exception, e:
            self.TE_LOG.error('Init Web Driver failed: %s' % e)
            return False
        else:
            return True

    def __talkWithRunnerRecv(self):
        try:
            exe_data = self.exe_socket.recv(self.exe_socket_buff_size)
            if exe_data is None:
                return (None, None)
            exe_json = json.loads(exe_data)
            command = exe_json['COMMAND']
            data = exe_json['DATA']
        except Exception, e:
            #self.TE_LOG.debug('Receive data failed, %s' % e)
            time.sleep(2)
            return (None, None)
        return (command, data)

    def __talkWithRunnerSend(self, data=None):
        try:
            self.exe_socket.send(json.dumps(data))
        except Exception, e:
            self.TE_LOG.debug('Send data failed, %s' % e)
            time.sleep(2)
            return False
        return True

    def __initWebManualHarness(self):
        if self.target_platform.upper().find('CHROME') >= 0:
            self.web_driver.get('%s%s' % (self.test_prefix, MH_FILE))
        else:
            self.web_driver.get('%s/index.html' % self.test_prefix)

        try:
            harness_page_file = open(MH_FILE)
            harness_page_raw = harness_page_file.read()
            harness_page_file.close()
        except Exception, e:
            self.TE_LOG.debug('Read manual harness file failed: %s' % e)
            return False
        harness_page_raw = harness_page_raw.replace(
            '\n', '').replace('"', '\\"').replace("'", "\\'")
        self.web_driver.execute_script(
            "document.write(\"%s\")" % harness_page_raw)
        self.web_driver.execute_script("document.close()")
        self.web_driver.execute_script("init_mh()")

        return True

    def __runWebManualTests(self):
        if not self.__initWebManualHarness():
            self.TE_LOG.error(
                'Init web manual harness failed, exit from executer')
            return False

        case_num = len(self.tests_json['cases'])
        i_case = 0
        while True:
            try:
                if i_case >= (case_num - 1):
                    i_case = case_num - 1
                    self.web_driver.execute_script(
                        "document.getElementById(\"forward-bt\").disabled=\"true\"")
                else:
                    self.web_driver.execute_script(
                        "document.getElementById(\"forward-bt\").disabled=\"\"")

                if i_case <= 0:
                    i_case = 0
                    self.web_driver.execute_script(
                        "document.getElementById(\"back-bt\").disabled=\"true\"")
                else:
                    self.web_driver.execute_script(
                        "document.getElementById(\"back-bt\").disabled=\"\"")

                if self.set_type == REF_SET_TYPE:
                    self.web_driver.execute_script(
                        "document.getElementById(\"test-entry\").textContent=\"%s%s\"" % (self.test_prefix, self.tests_json['cases'][i_case]['entry']))
                    self.web_driver.execute_script(
                        "document.getElementById(\"refer-test-entry\").textContent=\"%s%s\"" % (self.test_prefix, self.tests_json['cases'][i_case]['refer_entry']))
                    self.web_driver.execute_script(
                        "document.getElementById(\"run-refer-test-bt\").style.display=\"\"")
                    self.web_driver.execute_script(
                        "document.getElementById(\"refer-test-entry-area\").style.display=\"\"")
                elif self.set_type == JS_SET_TYPE:
                    self.web_driver.execute_script(
                        "document.getElementById(\"test-entry\").textContent=\"%s%s\"" % (self.test_prefix, self.tests_json['cases'][i_case]['entry']))
                    self.web_driver.execute_script(
                        "document.getElementById(\"run-refer-test-bt\").style.display=\"none\"")
                    self.web_driver.execute_script(
                        "document.getElementById(\"refer-test-entry-area\").style.display=\"none\"")

                WebDriverWait(self.web_driver, 3600).until(lambda strdiff: self.web_driver.execute_script(
                    "return document.getElementById(\"case-info-area\").className") != "READY")
                i_case_status = self.web_driver.find_element_by_id(
                    "case-info-area").get_attribute("class")
                self.web_driver.execute_script(
                    "document.getElementById(\"case-info-area\").className = \"READY\"")
                if i_case_status in [STR_PASS, STR_FAIL, STR_BLOCK]:
                    self.tests_json['cases'][i_case]['result'] = i_case_status
                    i_case = i_case + 1
                elif i_case_status == "FORWARD":
                    i_case = i_case + 1
                elif i_case_status == "BACK":
                    i_case = i_case - 1
                else:
                    break
            except Exception, e:
                self.tests_json['cases'][i_case]['result'] = STR_BLOCK
                self.TE_LOG.error("Run %s: failed: %s, exit from executer" %
                                  (self.tests_json['cases'][i_case]['case_id'], e))
                break

    def __checkPageNotFound(self, page_url=None):
        try:
            if self.web_driver:
                if self.web_driver.current_url.find('data:text/html,chromewebdata') >= 0:
                    self.TE_LOG.debug("Page not found: %s" %
                        self.web_driver.current_url)
                    return False
                else:
                    return True
            else:
                self.TE_LOG.debug("Page not found: %s" %
                    self.web_driver.current_url)
                return False
        except Exception, e:
            self.TE_LOG.error("Failed to get current url: %s" % e)
            return False

    def __runRefTests(self, haha=None, kkkk=None):
        for i_case in self.tests_json['cases']:
            with EXE_LOCK:
                if self.exe_status == 'DONE':
                    return False

            i_case['start_at'] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime())
            try:
                i_case_timeout = i_case['timeout']
            except Exception, e:
                i_case_timeout = DEFAULT_TIMEOUT

            i_page_url = '%s%s' % (self.test_prefix, i_case['entry'])
            try:
                self.web_driver.set_page_load_timeout(i_case_timeout)
                self.web_driver.get(i_page_url)
                time.sleep(int(i_case['onload_delay']))
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            if not self.__checkPageNotFound(i_page_url):
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked, page not found" % i_case['case_id'])
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                i_case['stdout'] = "page not found"
                continue

            try:
                test01_md5 = hashlib.md5(
                    self.web_driver.get_screenshot_as_base64()).hexdigest().upper()
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            try:
                i_refer_case_timeout = i_case['refer_timeout']
            except Exception, e:
                i_refer_case_timeout = DEFAULT_TIMEOUT

            i_ref_page_url = '%s%s' % (self.test_prefix, i_case['refer_entry'])
            try:
                self.web_driver.set_page_load_timeout(i_refer_case_timeout)
                self.web_driver.get(i_ref_page_url)
                time.sleep(int(i_case['onload_delay']))
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            if not self.__checkPageNotFound(i_ref_page_url):
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked, ref page not found" % i_case['case_id'])
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            try:
                test02_md5 = hashlib.md5(
                    self.web_driver.get_screenshot_as_base64()).hexdigest().upper()
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            if test01_md5 == test02_md5:
                i_case['result'] = STR_PASS
            else:
                i_case['result'] = STR_FAIL

    def __getCaseIndex(self, url):
        try:
            value_pos = url.rindex('value=')
            if value_pos == -1:
                return 0
            eq_value = url[value_pos:]
            eq_index = eq_value.index('=')
            sub_value = eq_value[eq_index + 1:]
            if sub_value is not None:
                return sub_value
        except Exception, e:
            return 0

    def __checkUrlSame(self, pre_url, url):
        try:
            if pre_url == '' or url == '':
                return False
            index_url = url.index('?')
            if index_url == -1:
                return False
            ab_url = url[0:index_url]
            if pre_url == ab_url:
                return True
            else:
                return False
        except Exception:
            return False

    def __runJSTests(self, haha=None, kkkk=None):
        for i_case in self.tests_json['cases']:
            with EXE_LOCK:
                if self.exe_status == 'DONE':
                    return False
            i_case['start_at'] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime())
            try:
                sub_index = 0
                url_equal = False
                tmp_pos = i_case['entry'].find('?')
                if tmp_pos == -1:
                    entry_url = i_case['entry']
                else:
                    entry_url = i_case['entry'][:tmp_pos]

                if not self.pre_url:
                    self.pre_url = entry_url
                else:
                    url_equal = self.__checkUrlSame(self.pre_url, i_case['entry'])
                    self.pre_url = entry_url
                i_case_timeout = i_case['timeout']
            except Exception, e:
                i_case_timeout = DEFAULT_TIMEOUT

            i_page_url = '%s%s' % (self.test_prefix, entry_url)
            try:
                self.web_driver.set_page_load_timeout(i_case_timeout)
                sub_index = self.__getCaseIndex(i_case['entry'])
                if not url_equal:
                    self.web_driver.implicitly_wait(i_case['onload_delay'])
                    self.web_driver.get(i_page_url)
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.debug(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                continue

            if not self.__checkPageNotFound(i_page_url):
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked, page not found" % i_case['case_id'])
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                i_case['stdout'] = "page not found"
                continue

            try:
                if sub_index:
                    sub_index = int(sub_index) - 1
                    table = self.web_driver.find_element_by_xpath(
                        "//table[@id='results']")
                    tr = table.find_elements_by_xpath(".//tbody/tr")[sub_index]
                    sub_result = tr.find_elements_by_xpath(".//td")[0].text
                    error_message = tr.find_elements_by_xpath(".//td")[2].text
                    if sub_result.upper() == 'PASS':
                        i_case['result'] = STR_PASS
                    elif sub_result.upper() == 'FAIL':
                        i_case['result'] = STR_FAIL
                        i_case['stdout'] = error_message
                    else:
                        i_case['result'] = STR_BLOCK
                else:
                    pass_result = self.web_driver.find_elements_by_class_name('pass')
                    fail_result = self.web_driver.find_elements_by_class_name('fail')
                    if len(fail_result) > 0:
                        i_case['result'] = STR_FAIL
                    elif len(pass_result) > 0 and len(fail_result) == 0:
                        i_case['result'] = STR_PASS
                    else:
                        i_case['result'] = STR_BLOCK
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
            except Exception, e:
                try:
                    pass_result = self.web_driver.find_elements_by_class_name('pass')
                    fail_result = self.web_driver.find_elements_by_class_name('fail')
                    if len(fail_result) > 0:
                        i_case['result'] = STR_FAIL
                    elif len(pass_result) > 0 and len(fail_result) == 0:
                        i_case['result'] = STR_PASS
                    else:
                        i_case['result'] = STR_BLOCK
                except Exception, e:
                    i_case['result'] = STR_BLOCK
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())

    def __runQUNITTests(self):
        for i_case in self.tests_json['cases']:
            with EXE_LOCK:
                if self.exe_status == 'DONE':
                    return False
            i_case['start_at'] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime())
            try:
                url_equal = False
                tmp_pos = i_case['entry'].find('?')
                if tmp_pos == -1:
                    entry_url = i_case['entry']
                else:
                    entry_url = i_case['entry'][:tmp_pos]

                if not self.pre_url:
                    self.pre_url = entry_url
                else:
                    url_equal = self.__checkUrlSame(self.pre_url, i_case['entry'])
                    self.pre_url = entry_url
                i_case_timeout = i_case['timeout']
            except Exception, e:
                i_case_timeout = DEFAULT_TIMEOUT

            i_page_url = '%s%s' % (self.test_prefix, entry_url)
            try:
                self.web_driver.set_page_load_timeout(i_case_timeout)
                sub_index = int(i_case['entry'].split("testNumber=")[1]) - 1
                if not url_equal:
                    self.web_driver.get(i_page_url)
                    self.web_driver.implicitly_wait(i_case['onload_delay'])
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.debug(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                self.web_driver.quit()
                continue

            if not self.__checkPageNotFound(i_page_url):
                i_case['result'] = STR_BLOCK
                self.TE_LOG.info(
                    "Cases %s: blocked, page not found" % i_case['case_id'])
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
                i_case['stdout'] = "page not found"
                continue
            try:
                result_counts = self.web_driver.find_elements_by_class_name('counts')
                result_str = '[Message]'
                count_tuple = eval(str(result_counts[sub_index].text))
                if int(count_tuple[0]) == 0:
                    i_case['result'] = STR_PASS
                    for sub_case_index in range(int(count_tuple[2])):
                        result_str += "[assert]pass[message]*okay\n"
                    i_case['stdout'] = result_str.strip("\n")
                else:
                    assert_list = self.web_driver.find_elements_by_class_name("qunit-assert-list")
                    tag_li_list = assert_list[sub_index].find_elements_by_tag_name('li')
                    result_list = []
                    result_str = '[Message]'
                    for item in tag_li_list:
                        case_result = item.get_attribute('class')
                        result_list.append(case_result)
                        tmp_msg = "[message]*okay"
                        if case_result == "fail":
                            tmp_msg = "[message]*failed"
                        result_str += "[assert]" + case_result + tmp_msg + "\n"
                    if "fail" in result_list:
                        i_case['result'] = STR_FAIL
                    else:
                        i_case['result'] = STR_PASS
                    i_case['stdout'] = result_str.strip("\n")
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())
            except Exception, e:
                i_case['result'] = STR_BLOCK
                self.TE_LOG.debug(
                    "Cases %s: blocked by %s" % (i_case['case_id'], e))
                i_case['end_at'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime())

    def __runTests(self, haha=None, kkkk=None):
        for i_case in self.tests_json['cases']:
            i_case['result'] = STR_NOTRUN
        if self.set_exetype == "manual":
            self.__runWebManualTests()
        elif self.set_type == REF_SET_TYPE:
            self.__runRefTests()
        elif self.set_type == JS_SET_TYPE:
            self.__runJSTests()
        elif self.set_type == QUNIT_SET_TYPE:
            self.__runQUNITTests()
        with EXE_LOCK:
            self.exe_status = 'DONE'

        return True

    def runTestsExecuter(self):
        if not self.set_type in [REF_SET_TYPE, JS_SET_TYPE, QUNIT_SET_TYPE]:
            self.TE_LOG.error(
                "Unsupported set type %s, exit from executer" % self.set_type)
            return False

        try:
            if not self.__initWebDriver():
                if self.web_driver:
                    self.web_driver.quit()
                    self.web_driver = None
                self.TE_LOG.error("Exit from executer")
                return False
        except Exception, e:
            if self.web_driver:
                self.web_driver.quit()
            self.TE_LOG.error(
                "Init Web Driver failed: %s, exit from executer" % e)
            return False

        while True:
            if not tr_utils.pidExists(self.runner_proc):
                if self.set_type in [REF_SET_TYPE, JS_SET_TYPE, QUNIT_SET_TYPE]:
                    if self.web_driver:
                        self.web_driver.quit()
                        self.web_driver = None
                self.TE_LOG.debug('Can not find runner, exit from executer')
                return False
            exe_command, exe_data = self.__talkWithRunnerRecv()
            if exe_command == 'GET_STATUS':
                with EXE_LOCK:
                    self.__talkWithRunnerSend(
                        {'COMMAND': exe_command, 'DATA': self.exe_status})
            elif exe_command == 'TESTS':
                with EXE_LOCK:
                    self.exe_status = 'RUNNING'
                self.tests_json = exe_data['data']
                self.exe_thread = thread.start_new_thread(
                    self.__runTests, (1, 2))
                self.__talkWithRunnerSend(
                    {'COMMAND': exe_command, 'DATA': 'OK'})
            elif exe_command == 'GET_RESULTS':
                if not self.__talkWithRunnerSend({'COMMAND': exe_command, 'DATA': self.tests_json}):
                    continue
                with EXE_LOCK:
                    self.exe_status = 'READY'
            elif exe_command == 'TERMINAL':
                if self.web_driver:
                    self.web_driver.quit()
                    self.web_driver = None
                with EXE_LOCK:
                    self.exe_status = 'DONE'
                self.__talkWithRunnerSend(
                    {'COMMAND': exe_command, 'DATA': 'OK'})
            else:
                continue

    def EndExecuter(self):
        if self.web_driver:
            self.web_driver.quit()
            self.web_driver = None
            return True
