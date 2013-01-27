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
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>

import os
import platform
import time
import sys, traceback
import collections
from datetime import datetime
from shutil import copyfile
import xml.etree.ElementTree as etree
import ConfigParser
from xml.dom import minidom
from tempfile import mktemp
from testkitlite.common.str2 import *
from testkitlite.common.autoexec import shell_exec
from testkitlite.common.killall import killall
from shutil import move
from os import remove
import re
import subprocess

_j = os.path.join
_d = os.path.dirname
_b = os.path.basename
_e = os.path.exists
_abs = os.path.abspath

class TRunner:
    """
    Parse the testdefinition.xml files.
    Apply filter for each run.
    Conduct tests execution.
    """
    def __init__(self):
        # dryrun
        self.bdryrun = False
        # non_active
        self.non_active = False
        # enable_memory_collection
        self.enable_memory_collection = False
        # result file
        self.resultfile = None
        # external test    
        self.external_test = None
        # filter rules
        self.filter_rules = None
        self.fullscreen = False
        self.resultfiles = set()
        self.core_auto_files = []
        self.core_manual_files = []
        self.skip_all_manual = False
        self.testsuite_dict = {}
        self.exe_sequence = []
        self.testresult_dict = {"pass" : 0, "fail" : 0, "block" : 0, "not_run" : 0}
        self.current_test_xml = "none"
        self.first_run = True

    def set_pid_log(self, pid_log):
        self.pid_log = pid_log

    def set_dryrun(self, bdryrun):
        self.bdryrun = bdryrun

    def set_non_active(self, non_active):
        self.non_active = non_active

    def set_enable_memory_collection(self, enable_memory_collection):
        self.enable_memory_collection = enable_memory_collection

    def set_resultfile(self, resultfile):
        self.resultfile = resultfile

    def set_external_test(self, exttest):
        self.external_test = exttest

    def add_filter_rules(self, **kargs):
        """
        kargs:  key:values - "":["",]
        """
        self.filter_rules = kargs

    def set_fullscreen(self, state):
        self.fullscreen = state

    def prepare_run(self, testxmlfile, resultdir=None):
        """
        testxmlfile: target testxml file
        execdir and resultdir: should be the absolute path since TRunner
        is the common lib
        """
        # resultdir is set to current directory by default
        if not resultdir:
            resultdir = os.getcwd()
        ok = True
        if ok:
            try:
                filename = testxmlfile
                filename = os.path.splitext(filename)[0]
                if platform.system() == "Linux":
                    filename = filename.split('/')[-1]
                else:
                    filename = filename.split('\\')[-1]
                if self.filter_rules["execution_type"] == ["manual"]:
                    resultfile = "%s.manual.xml" % filename
                else:
                    resultfile = "%s.auto.xml" % filename
                resultfile = _j(resultdir, resultfile)
                if not _e(resultdir):
                    os.mkdir(resultdir)
                print "[ analysis test xml file: %s ]" % resultfile
                try:
                    ep = etree.parse(testxmlfile)
                    suiteparent = ep.getroot()
                    no_test_definition = 1
                    for tf in ep.getiterator('test_definition'):
                        no_test_definition = 0
                    if no_test_definition:
                        suiteparent = etree.Element('test_definition')
                        suiteparent.tail = "\n"
                        for suite in ep.getiterator('suite'):
                            suite.tail = "\n"
                            suiteparent.append(suite)
                    self.apply_filter(suiteparent)
                    try:
                        with open(resultfile, 'w') as output:
                            tree = etree.ElementTree(element=suiteparent)
                            tree.write(output)
                    except IOError, e:
                        print "[ Error: create filtered result file: %s failed, error: %s ]" % (resultfile, e)
                except Exception, e:
                    print e
                    return False
                casefind = etree.parse(resultfile).getiterator('testcase')
                if casefind:
                    file = "%s" % _b(resultfile)
                    file = os.path.splitext(file)[0]
                    testsuite_dict_value_list = []
                    testsuite_dict_add_flag = 0
                    execute_suite_one_way = 1
                    if self.external_test:
                        parser = etree.parse(resultfile)
                        no_wrtlauncher = 1
                        suite_total_count = 0 
                        suite_wrt_launcher_count = 0
                        for tsuite in parser.getiterator('suite'):
                            suite_total_count += 1
                            if tsuite.get('launcher'):
                                if not tsuite.get('launcher').find('WRTLauncher'):
                                    no_wrtlauncher = 0
                                    suite_wrt_launcher_count += 1
                        if no_wrtlauncher:
                            if self.filter_rules["execution_type"] == ["auto"]:
                                self.core_auto_files.append(resultfile)
                            else:
                                self.core_manual_files.append(resultfile)
                        elif suite_total_count == suite_wrt_launcher_count:
                            testsuite_dict_value_list.append(resultfile) 
                            testsuite_dict_add_flag = 1
                            self.exe_sequence.append(file)
                        else:
                            filename_diff = 1
                            execute_suite_one_way = 0
                            for tsuite in parser.getiterator('suite'):
                                root = etree.Element('test_definition')
                                suitefilename = os.path.splitext(resultfile)[0]
                                suitefilename += ".suite_%s.xml" % filename_diff
                                suitefilename = _j(resultdir, suitefilename)
                                tsuite.tail = "\n"
                                root.append(tsuite)
                                try:
                                    with open(suitefilename, 'w') as output:
                                        tree = etree.ElementTree(element=root)
                                        tree.write(output)
                                except IOError, e:
                                    print "[ Error: create filtered result file: %s failed, error: %s ]" % (suitefilename, e)
                                case_suite_find = etree.parse(suitefilename).getiterator('testcase')
                                if case_suite_find:
                                    if tsuite.get('launcher'):
                                        if tsuite.get('launcher').find('WRTLauncher'):
                                            if self.filter_rules["execution_type"] == ["auto"]:
                                                self.core_auto_files.append(suitefilename)
                                            else:
                                                self.core_manual_files.append(suitefilename)
                                            self.resultfiles.add(suitefilename)
                                        else:
                                            testsuite_dict_value_list.append(suitefilename) 
                                            if testsuite_dict_add_flag == 0:
                                                self.exe_sequence.append(file)
                                            testsuite_dict_add_flag = 1
                                            self.resultfiles.add(suitefilename)
                                    else:
                                        if self.filter_rules["execution_type"] == ["auto"]:
                                            self.core_auto_files.append(suitefilename)
                                        else:
                                            self.core_manual_files.append(suitefilename)
                                        self.resultfiles.add(suitefilename)
                                filename_diff += 1
                        if testsuite_dict_add_flag:
                            self.testsuite_dict[file] = testsuite_dict_value_list 
                    else:
                        if self.filter_rules["execution_type"] == ["auto"]:
                            self.core_auto_files.append(resultfile)
                        else:
                            self.core_manual_files.append(resultfile)
                    if execute_suite_one_way:
                        self.resultfiles.add(resultfile)
            except Exception, e:
                traceback.print_exc()
                print e
                ok &= False
        return ok

    def run_and_merge_resultfile(self, start_time, latest_dir):
        # run core auto cases
        for core_auto_file in self.core_auto_files:
            temp_test_xml = os.path.splitext(core_auto_file)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml += ".auto"
            # print identical xml file name
            if self.current_test_xml != temp_test_xml:
                time.sleep(3)
                print "\n[ testing xml: %s.xml ]" % temp_test_xml
                self.current_test_xml = temp_test_xml
            self.execute(core_auto_file, core_auto_file)
            
        # run webAPI cases
        for webapi_total_file in self.exe_sequence:
            for webapi_file in self.testsuite_dict[webapi_total_file]:
                # print identical xml file name
                if self.current_test_xml != _j(latest_dir, webapi_total_file):
                    time.sleep(3)
                    print "\n[ testing xml: %s.xml ]\n" % _j(latest_dir, webapi_total_file)
                    self.current_test_xml = _j(latest_dir, webapi_total_file)
                try:
                    # split xml by <set>
                    print "[ split xml: %s by <set> ]" % webapi_file
                    print "[ this might take some time, please wait ]"
                    set_number = 1
                    test_xml_set_list = []
                    self.resultfiles.discard(webapi_file)
                    test_xml_temp = etree.parse(webapi_file)
                    for test_xml_temp_suite in test_xml_temp.getiterator('suite'):
                        for test_xml_temp_set in test_xml_temp_suite.getiterator('set'):
                            copy_url = os.path.splitext(webapi_file)[0]
                            copy_url += "_set_%s.xml" % set_number
                            copyfile(webapi_file, copy_url)
                            test_xml_set_list.append(copy_url)
                            self.resultfiles.add(copy_url)
                            set_number += 1
                    time.sleep(3)
                    set_number -= 1
                    print "[ total set number is: %s ]" % set_number
                    # only keep one set in each xml file and remove empty set
                    test_xml_set_list_empty = []
                    for test_xml_set in test_xml_set_list:
                        test_xml_set_tmp = etree.parse(test_xml_set)
                        set_keep_number = 1
                        print "[ process set: %s ]" % test_xml_set
                        for test_xml_set_temp_suite in test_xml_set_tmp.getiterator('suite'):
                            for test_xml_set_temp_set in test_xml_set_temp_suite.getiterator('set'):
                                if set_keep_number != set_number:
                                    test_xml_set_temp_suite.remove(test_xml_set_temp_set)
                                else:
                                    temp_case = test_xml_set_temp_set.getiterator('testcase')
                                    if not temp_case:
                                        test_xml_set_list_empty.append(test_xml_set)
                                set_keep_number += 1
                        set_number -= 1
                        with open(test_xml_set, 'w') as output:
                            root = test_xml_set_tmp.getroot()
                            tree = etree.ElementTree(element=root)
                            tree.write(output)
                    for empty_set in test_xml_set_list_empty:
                        print "[ remove empty set: %s ]" % empty_set
                        test_xml_set_list.remove(empty_set)
                        self.resultfiles.discard(empty_set)
                    # create temporary parameter
                    from testkithttpd import check_server_running
                    for test_xml_set in test_xml_set_list:
                        print "\n[ run set: %s ]" % test_xml_set
                        if self.first_run:
                            exe_sequence_tmp = []
                            exe_sequence_tmp.append(webapi_total_file)
                            testresult_dict_tmp = {}
                            testresult_dict_item_tmp = []
                            testresult_dict_item_tmp.append(test_xml_set)
                            testresult_dict_tmp[webapi_total_file] = testresult_dict_item_tmp
                            # start server with temporary parameter
                            self.execute_external_test(testresult_dict_tmp, exe_sequence_tmp, test_xml_set)
                        else:
                            xml_package = (test_xml_set, webapi_total_file, test_xml_set)
                            self.reload_xml_to_server(xml_package)
                        while True:
                            time.sleep(5)
                            if check_server_running():
                                break
                except Exception, e:
                    print "[ Error: fail to run webapi test xml, error: %s ]" % e
        # shut down server
        try:
            if not self.first_run:
                from testkithttpd import shut_down_server
                shut_down_server()
        except Exception, e:
            print "[ Error: fail to close webapi http server, error: %s ]" % e
        
        # run core manual cases
        for core_manual_file in self.core_manual_files:
            temp_test_xml = os.path.splitext(core_manual_file)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml += ".manual"
            # print identical xml file name
            if self.current_test_xml != temp_test_xml:
                time.sleep(3)
                print "\n[ testing xml: %s.xml ]" % temp_test_xml
                self.current_test_xml = temp_test_xml
            if self.non_active:
                self.skip_all_manual = True
            self.execute(core_manual_file, core_manual_file)
            
        mergefile = mktemp(suffix='.xml', prefix='tests.', dir=latest_dir)
        mergefile = os.path.splitext(mergefile)[0]
        mergefile = os.path.splitext(mergefile)[0]
        mergefile = "%s.result" % _b(mergefile)
        mergefile = "%s.xml" % mergefile
        mergefile = _j(latest_dir, mergefile)
        end_time = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
        print "\n[ test complete at time: %s ]" % end_time
        print "[ start merging test result xml files, this might take some time, please wait ]"
        print "[ merge result files into %s ]" % mergefile
        root = etree.Element('test_definition')
        root.tail = "\n"
        totals = set()
        # create core and webapi set
        resultfiles_core = set()
        for auto_file in self.core_auto_files:
            resultfiles_core.add(auto_file)
        for manual_file in self.core_manual_files:
            resultfiles_core.add(manual_file)
        resultfiles_webapi = self.resultfiles
        for resultfile_core in resultfiles_core:
            resultfiles_webapi.discard(resultfile_core)
        # merge core result files
        for resultfile_core in resultfiles_core:
            totalfile = os.path.splitext(resultfile_core)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = "%s.total" % totalfile
            totalfile = "%s.xml" % totalfile
            total_xml = etree.parse(totalfile)
            
            result_xml = etree.parse(resultfile_core)
            print "|--[ merge core result file: %s ]" % resultfile_core
                    
            for total_suite in total_xml.getiterator('suite'):
                for total_set in total_suite.getiterator('set'):
                    for result_suite in result_xml.getiterator('suite'):
                        for result_set in result_suite.getiterator('set'):
                            # when total xml and result xml have same suite name and set name
                            if result_set.get('name') == total_set.get('name') and result_suite.get('name') == total_suite.get('name'):
                                # set cases that doesn't have result in result set to N/A
                                # append cases from result set to total set
                                result_case_iterator = result_set.getiterator('testcase')
                                if result_case_iterator:
                                    print "`----[ suite: %s, set: %s, time: %s ]" % (result_suite.get('name'), result_set.get('name'), datetime.today().strftime("%Y-%m-%d_%H_%M_%S"))
                                    for result_case in result_case_iterator:
                                        try:
                                            if not result_case.get('result'):
                                                result_case.set('result', 'N/A')
                                            if result_case.get('result') == "PASS":
                                                self.testresult_dict["pass"] += 1
                                            if result_case.get('result') == "FAIL":
                                                self.testresult_dict["fail"] += 1
                                            if result_case.get('result') == "BLOCK":
                                                self.testresult_dict["block"] += 1
                                            if result_case.get('result') == "N/A":
                                                self.testresult_dict["not_run"] += 1
                                            total_set.append(result_case)
                                        except Exception, e:
                                            print "[ Error: fail to append %s, error: %s ]" % (result_case.get('id'), e)
            total_xml.write(totalfile)
            totals.add(totalfile)
        # merge webapi result files
        for resultfile_webapi in resultfiles_webapi:
            totalfile = os.path.splitext(resultfile_webapi)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = "%s.total" % totalfile
            totalfile = "%s.xml" % totalfile
            total_xml = etree.parse(totalfile)
            
            print "|--[ merge webapi result file: %s ]" % resultfile_webapi
            result_xml = etree.parse(resultfile_webapi)
            for total_suite in total_xml.getiterator('suite'):
                for total_set in total_suite.getiterator('set'):
                    for result_suite in result_xml.getiterator('suite'):
                        for result_set in result_suite.getiterator('set'):
                            # when total xml and result xml have same suite name and set name
                            if result_set.get('name') == total_set.get('name') and result_suite.get('name') == total_suite.get('name'):
                                # set cases that doesn't have result in result set to N/A
                                # append cases from result set to total set
                                result_case_iterator = result_set.getiterator('testcase')
                                if result_case_iterator:
                                    print "`----[ suite: %s, set: %s, time: %s ]" % (result_suite.get('name'), result_set.get('name'), datetime.today().strftime("%Y-%m-%d_%H_%M_%S"))
                                    for result_case in result_case_iterator:
                                        try:
                                            if not result_case.get('result'):
                                                result_case.set('result', 'N/A')
                                            if result_case.get('result') == "PASS":
                                                self.testresult_dict["pass"] += 1
                                            if result_case.get('result') == "FAIL":
                                                self.testresult_dict["fail"] += 1
                                            if result_case.get('result') == "BLOCK":
                                                self.testresult_dict["block"] += 1
                                            if result_case.get('result') == "N/A":
                                                self.testresult_dict["not_run"] += 1
                                            total_set.append(result_case)
                                        except Exception, e:
                                            print "[ Error: fail to append %s, error: %s ]" % (result_case.get('id'), e)
            total_xml.write(totalfile)
            totals.add(totalfile)
        for total in totals:
            result_xml = etree.parse(total)
            for suite in result_xml.getiterator('suite'):
                suite.tail = "\n"
                root.append(suite)
        try:
            with open(mergefile, 'w') as output:
                tree = etree.ElementTree(element=root)
                tree.write(output)
        except IOError, e:
            print "[ Error: merge result file failed, error: %s ]" % e
        # report the result using xml mode
        print "[ generate result xml: %s ]" % mergefile
        if self.skip_all_manual:
            print "[ some results of core manual cases are N/A, the result file is at %s ]" % mergefile
        print "[ test summary ]"
        total_case_number = int(self.testresult_dict["pass"]) + int(self.testresult_dict["fail"]) + int(self.testresult_dict["block"]) + int(self.testresult_dict["not_run"])
        print "  [ total case number: %s ]" % (total_case_number)
        if total_case_number == 0:
            print "[Warning: found 0 case from the result files, if it's not right, please check the test xml files, or the filter values ]"
        else:
            print "  [ pass rate: %.2f%% ]" % (int(self.testresult_dict["pass"]) * 100 / int(total_case_number))
            print "  [ PASS case number: %s ]" % self.testresult_dict["pass"]
            print "  [ FAIL case number: %s ]" % self.testresult_dict["fail"]
            print "  [ BLOCK case number: %s ]" % self.testresult_dict["block"]
            print "  [ N/A case number: %s ]" % self.testresult_dict["not_run"]
        print "[ merge complete, write to the result file, this might take some time, please wait ]"
        
        ep = etree.parse(mergefile)
        rt = ep.getroot()
        device_info = self.get_device_info()
        environment = etree.Element('environment')
        environment.attrib['device_id'] = "Empty device_id"
        environment.attrib['device_model'] = device_info["device_model"]
        environment.attrib['device_name'] = device_info["device_name"]
        environment.attrib['firmware_version'] = "Empty firmware_version"
        environment.attrib['host'] = "Empty host"
        environment.attrib['os_version'] = device_info["os_version"]
        environment.attrib['resolution'] = device_info["resolution"]
        environment.attrib['screen_size'] = device_info["screen_size"]
        other = etree.Element('other')
        other.text = "Here is a String for testing"
        environment.append(other)
        environment.tail = "\n"
        summary = etree.Element('summary')
        summary.attrib['test_plan_name'] = "Empty test_plan_name"
        start_at = etree.Element('start_at')
        start_at.text = start_time
        end_at = etree.Element('end_at')
        end_at.text = end_time
        summary.append(start_at)
        summary.append(end_at)
        summary.tail = "\n  "
        rt.insert(0, summary)
        rt.insert(0, environment)
        # add XSL support to testkit-lite
        DECLARATION = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="testresult.xsl"?>\n"""
        with open(mergefile, 'w') as output:
            output.write(DECLARATION)
            ep.write(output, xml_declaration=False, encoding='utf-8')
        # change &lt;![CDATA[]]&gt; to <![CDATA[]]>
        self.replace_cdata(mergefile)
        
        try:
            if self.resultfile:
                copyfile(mergefile, self.resultfile)
        except Exception, e:
            print "[ Error: fail to copy the result file to: %s, please check if you have created its parent directory, error: %s ]" % (self.resultfile, e)

    def get_device_info(self):
        device_info = {}
        resolution_str = "Empty resolution"
        screen_size_str = "Empty screen_size"
        device_model_str = "Empty device_model"
        device_name_str = "Empty device_name"
        os_version_str = ""
        # get resolution and screen size
        fi, fo, fe = os.popen3("xrandr")
        for line in fo.readlines():
            pattern = re.compile('connected (\d+)x(\d+).* (\d+mm) x (\d+mm)')
            match = pattern.search(line)
            if match:
                resolution_str = "%s x %s" % (match.group(1), match.group(2))
                screen_size_str = "%s x %s" % (match.group(3), match.group(4))
        # get architecture
        fi, fo, fe = os.popen3("uname -m")
        device_model_str_tmp = fo.readline()
        if len(device_model_str_tmp) > 1:
            device_model_str = device_model_str_tmp[0:-1]
        # get hostname
        fi, fo, fe = os.popen3("uname -n")
        device_name_str_tmp = fo.readline()
        if len(device_name_str_tmp) > 1:
            device_name_str = device_name_str_tmp[0:-1]
        # get os version
        fi, fo, fe = os.popen3("cat /etc/issue")
        for line in fo.readlines():
            if len(line) > 1:
                os_version_str = "%s %s" % (os_version_str, line)
        os_version_str = os_version_str[0:-1]
        
        device_info["resolution"] = resolution_str
        device_info["screen_size"] = screen_size_str
        device_info["device_model"] = device_model_str
        device_info["device_name"] = device_name_str
        device_info["os_version"] = os_version_str
        
        return device_info

    def pretty_print(self, ep, resultfile):
        rawstr = etree.tostring(ep.getroot(), 'utf-8')
        t = minidom.parseString(rawstr)
        open(resultfile, 'w+').write(t.toprettyxml(indent="  "))

    def execute_external_test(self, testsuite, exe_sequence, resultfile):
        """Run external test"""
        from testkithttpd import startup
        if self.bdryrun:
            print "[ WRTLauncher mode does not support dryrun ]"
            return True
        # start http server in here
        try:
            parameters = {}
            parameters.setdefault("pid_log", self.pid_log)
            parameters.setdefault("testsuite", testsuite)
            parameters.setdefault("exe_sequence", exe_sequence)
            parameters.setdefault("client_command", self.external_test)
            if self.fullscreen:
                parameters.setdefault("hidestatus", "1")
            else:
                parameters.setdefault("hidestatus", "0")
            parameters.setdefault("resultfile", resultfile)
            parameters.setdefault("enable_memory_collection", self.enable_memory_collection)
            # kill existing http server
            http_server_pid = "none"
            fi, fo, fe = os.popen3("netstat -tpa | grep 8000")
            for line in fo.readlines():
                pattern = re.compile('([0-9]*)\/python')
                match = pattern.search(line)
                if match:
                    http_server_pid = match.group(1)
                    print "[ kill existing http server, pid: %s ]" % http_server_pid
                    killall(http_server_pid)
            if http_server_pid == "none":
                print "[ start new http server ]"
            else:
                print "[ start new http server in 3 seconds ]"
                time.sleep(3)
            self.first_run = False
            startup(parameters)
        except Exception, e:
            print "[ Error: fail to start http server, error: %s ]\n" % e
        return True

    def reload_xml_to_server(self, xml_package):
        from testkithttpd import reload_xml
        try:
            print "[ reload xml file to the http server ]"
            reload_xml(xml_package)
        except Exception, e:
            print "[ Error: fail to reload xml to the http server, error: %s ]\n" % e
        return True

    def apply_filter(self, rt):
        def case_check(tc):
            rules = self.filter_rules
            for key in rules.iterkeys():
                if key in ["suite", "set"]:
                    continue
                # Check attribute
                t_val = tc.get(key)
                if t_val:
                    if not t_val in rules[key]:
                        return False
                else:
                    # Check sub-element
                    items = tc.getiterator(key)
                    if items: 
                        t_val = []
                        for i in items:
                            t_val.append(i.text)
                        if len(set(rules[key]) & set(t_val)) == 0:
                            return False
            return True
        
        rules = self.filter_rules
        for tsuite in rt.getiterator('suite'):
            if rules.get('suite'):
                if tsuite.get('name') not in rules['suite']:
                    rt.remove(tsuite)
            for tset in tsuite.getiterator('set'):
                if rules.get('set'):
                    if tset.get('name') not in rules['set']:
                        tsuite.remove(tset)
                       
        for tset in rt.getiterator('set'):
            for tc in tset.getiterator('testcase'):
                if not case_check(tc):
                    tset.remove(tc)

    def execute(self, testxmlfile, resultfile):
        def exec_testcase(case, total_number, current_number):
            case_result = "BLOCK"
            return_code = None
            stderr = "none"
            stdout = "none"
            # print case info
            test_script_entry = "none"
            expected_result = "0"
            actual_result = "none"
            testentry_elm = case.find('description/test_script_entry')
            if testentry_elm is not None:
                test_script_entry = testentry_elm.text
                expected_result = testentry_elm.get('test_script_expected_result', "0")
            print "\n[case] execute case:\nTestCase: %s\nTestEntry: %s\nExpected Result: %s\nTotal: %s, Current: %s" % (case.get("id"), test_script_entry, expected_result, total_number, current_number)
            # execute test script
            if testentry_elm is not None:
                if self.bdryrun:
                    return_code, stderr, stdout = "none", "Dryrun error info", "Dryrun output"
                else:
                    print "[ execute test script, this might take some time, please wait ]"
                    if testentry_elm.text is None:
                        print "[ Warnning: test script is empty, please check your test xml file ]"
                    else:
                        try:
                            if testentry_elm.get('timeout'):
                                return_code, stdout, stderr = \
                                shell_exec(testentry_elm.text, "no_log", str2number(testentry_elm.get('timeout')), False)
                            else:
                                return_code, stdout, stderr = \
                                shell_exec(testentry_elm.text, "no_log", 90, False)
                            if return_code is not None:
                                actual_result = str(return_code)
                            print "Script Return Code: %s" % actual_result
                        except Exception, e:
                            print "[ Error: fail to execute test script, error: %s ]\n" % e
            # Construct result info node
            resinfo_elm = etree.Element('result_info')
            res_elm = etree.Element('actual_result')
            start_elm = etree.Element('start')
            end_elm = etree.Element('end')
            stdout_elm = etree.Element('stdout')
            stderr_elm = etree.Element('stderr')
            resinfo_elm.append(res_elm)
            resinfo_elm.append(start_elm)
            resinfo_elm.append(end_elm)
            resinfo_elm.append(stdout_elm)
            resinfo_elm.append(stderr_elm)
            case.append(resinfo_elm)
            start_elm.text = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
            res_elm.text = actual_result
            stdout_elm.text = stdout
            stderr_elm.text = stderr

            # sdx@kooltux.org: add notes to xml result
            self.insert_notes(case,stdout)
            self.insert_measures(case,stdout)

            # handle manual core cases
            if case.get('execution_type') == 'manual':
                case.set('result', 'BLOCK')
                try:
                    # print pre-condition info
                    precondition_elm = case.find('description/pre_condition')
                    if precondition_elm is not None:
                        print "\n********************\nPre-condition: %s\n********************\n" % precondition_elm.text
                    # print step info
                    for this_step in case.getiterator("step"):
                        step_desc = "none"
                        expected = "none"
                        order = this_step.get("order")
                        stepdesc_elm = this_step.find("step_desc")
                        expected_elm = this_step.find("expected")
                        if stepdesc_elm is not None:
                            step_desc = stepdesc_elm.text
                        if expected_elm is not None:
                            expected = expected_elm.text
                        print "********************\nStep Order: %s" % order
                        print "Step Desc: %s" % step_desc
                        print "Expected: %s\n********************\n" % expected
                    if self.skip_all_manual:
                        case_result = "N/A"
                    else:
                        while True:
                            test_result = raw_input('[ please input case result ](p^PASS, f^FAIL, b^BLOCK, n^Next, d^Done):')
                            if test_result == 'p':
                                case_result = "PASS"
                                break
                            elif test_result == 'f':
                                case_result = "FAIL"
                                break
                            elif test_result == 'b':
                                case_result = "BLOCK"
                                break
                            elif test_result == 'n':
                                case_result = "N/A"
                                break
                            elif test_result == 'd':
                                case_result = "N/A"
                                self.skip_all_manual = True
                                break
                            else:
                                print "[ Warnning: you input: '%s' is invalid, please try again ]" % test_result
                except Exception, e:
                    print "[ Error: fail to get core manual test step, error: %s ]\n" % e
            # handle auto core cases
            else:
                case_result = "BLOCK"
                end_elm.text = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
                # set test result
                if return_code is not None:
                    # sdx@kooltux.org: if retcode is 69 ("service unavailable" in sysexits.h), test environment is not correct
                    if actual_result == "69": 
                        case_result = "N/A"
                    elif actual_result == "time_out":
                        case_result = "BLOCK"
                    else:
                        if expected_result == actual_result:
                            case_result = "PASS"
                        else:
                            case_result = "FAIL"
            case.set('result', case_result)
            end_elm.text = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
            print "Case Result: %s" % case_result
            # Check performance test
            measures = case.getiterator('measurement')
            for m in measures:
                ind = m.get('name')
                fname = m.get('file')
                if fname and _e(fname):
                    try:
                        config = ConfigParser.ConfigParser()
                        config.read(fname)
                        val = config.get(ind, 'value')
                        m.set('value', val)
                    except Exception, e:
                        print "[ Error: fail to parse performance value, error: %s ]\n" % e
        # execute cases
        try:
            ep = etree.parse(testxmlfile)
            rt = ep.getroot()
            total_number = 0
            current_number = 0
            for tsuite in rt.getiterator('suite'):
                for tset in tsuite.getiterator('set'):
                    for tc in tset.getiterator('testcase'):
                        total_number += 1
            for tsuite in rt.getiterator('suite'):
                for tset in tsuite.getiterator('set'):
                    for tc in tset.getiterator('testcase'):
                        current_number += 1
                        exec_testcase(tc, total_number, current_number)
            ep.write(resultfile)
            return True
        except Exception, e:
            print "[ Error: fail to run core test case, error: %s ]\n" % e
            traceback.print_exc()
            return False

    def replace_cdata(self, file_name):
        abs_path = mktemp()
        new_file = open(abs_path, 'w')
        old_file = open(file_name)
        for line in old_file:
            line_temp = line.replace('&lt;![CDATA', '<![CDATA')
            new_file.write(line_temp.replace(']]&gt;', ']]>'))
        new_file.close()
        old_file.close()
        remove(file_name)
        move(abs_path, file_name)

    # sdx@kooltux.org: parse notes in buffer and insert them in XML result
    def insert_notes(self,case,buf,pattern="###[NOTE]###"):
        desc=case.find('description')
        if desc is None:
            return

        notes_elm=desc.find('notes')
        if notes_elm is None:
           notes_elm=etree.Element('notes')
           desc.append(notes_elm)
        notes_elm.text += "\n"+self._extract_notes(buf,pattern)

    def _extract_notes(self,buf,pattern):
        # util func to split lines in buffer, search for pattern on each line
        # then concatenate remaining content in output buffer
        out="" 
        for line in buf.split("\n"):
           pos=line.find(pattern)
           if pos>=0:
              out+=line[pos+len(pattern):]+"\n"
        return out

    # sdx@kooltux.org: parse measures returned by test script and insert in XML result
    # see xsd/test_definition.xsd: measurementType
    _MEASURE_ATTRIBUTES=['name','value','unit','target','failure','power']

    def insert_measures(self,case,buf,pattern="###[MEASURE]###",field_sep=":"): 
        # get measures
        measures=self._extract_measures(buf,pattern,field_sep)
        for m in measures:
            m_elm=etree.Element('measurement')
            for k in m:
                m_elm.attrib[k]=m[k]
            case.append(m_elm)
         
    def _extract_measures(self,buf,pattern,field_sep): 
        """ 
        This function extracts lines from <buf> containing the defined <pattern>.
        For each line containing the pattern, it extracts the string to the end of line
        Then it splits the content in multiple fields using the defined separator <field_sep>
        and maps the fields to measurement attributes defined in xsd
        Finally, a list containing all measurement objects found in input buffer is returned
        """
        out=[]
        for line in buf.split("\n"):
            pos=line.find(pattern)
            if pos<0:
                continue

            measure={}
            elts=collections.deque(line[pos+len(pattern):].split(':'))
            for k in self._MEASURE_ATTRIBUTES:
                if len(elts) == 0:
                    measure[k]=''
                else:
                    measure[k]=elts.popleft()
                    
            # don't accept unnamed measure
            if measure['name'] != '':
                out.append(measure)
        return out

