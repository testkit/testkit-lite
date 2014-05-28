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
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>
#              Yuanyuan,Zou  <zouyuanx@intel.com>
""" prepare run , split xml ,run case , merge result """

import os
import platform
import time
import sys
import traceback
import collections
from datetime import datetime
from shutil import copyfile
import xml.etree.ElementTree as etree
import ConfigParser
from tempfile import mktemp
from shutil import move
from os import remove
import copy
from testkitlite.util.log import LOGGER
from testkitlite.util.str2 import str2xmlstr
from testkitlite.util.errors import TestCaseNotFoundException

JOIN = os.path.join
DIRNAME = os.path.dirname
BASENAME = os.path.basename
EXISTS = os.path.exists
ABSPATH = os.path.abspath

# test constants
OPT_LAUNCHER = 'test-launcher'
OPT_EXTENSION = 'test-extension'
OPT_DEBUG_LOG = 'debug-log-base'
OPT_CAPABILITY = 'capability'
OPT_DEBUG = 'debug'
OPT_RERUN = 'rerun'
OPT_WIDGET = 'test-widget'
OPT_STUB  = 'stub-name'
OPT_SUITE = 'testsuite-name'
OPT_SET = 'testset-name'
OPT_test_set_src = 'test-set-src'


class TestSession:

    """
    Parse the testdefinition.xml files.
    Apply filter for each run.
    Conduct tests execution.
    """

    def __init__(self, connector, worker):
        """ init all self parameters here """
        # dryrun
        self.bdryrun = False
        # non_active
        self.non_active = False
        # result file
        self.resultfile = None
        # external test
        self.external_test = None
        # filter rules
        self.filter_rules = None
        self.debug = False
        self.resultfiles = set()
        self.core_auto_files = []
        self.core_manual_files = []
        self.unit_test_files = []        
        self.skip_all_manual = False
        self.testsuite_dict = {}
        self.exe_sequence = []
        self.testresult_dict = {"pass": 0, "fail": 0,
                                "block": 0, "not_run": 0}
        self.current_test_xml = "none"
        self.first_run = True
        self.deviceid = None
        self.session_id = None
        self.set_parameters = {}
        self.connector = connector
        self.stub_name = "testkit-stub"
        self.testworker = worker
        self.capabilities = {}
        self.has_capability = False
        self.rerun = False
        self.test_prefix = ""
        self.filter_ok = False

    def set_global_parameters(self, options):
        "get all options "
        # apply dryrun
        if options.bdryrun:
            self.bdryrun = options.bdryrun
        # Disable set the result of core manual cases from the console
        if options.non_active:
            self.non_active = options.non_active
        # apply user specify test result file
        if options.resultfile:
            self.resultfile = options.resultfile
        # set the external test
        if options.exttest:
            self.external_test = options.exttest
        if options.debug:
            self.debug = options.debug
        if options.rerun:
            self.rerun = options.rerun
        if options.test_prefix:
            self.test_prefix = options.test_prefix
        if options.worker:
            self.worker_name = options.worker

    def add_filter_rules(self, **kargs):
        """
        kargs:  key:values - "":["",]
        """
        self.filter_rules = kargs

    def set_session_id(self, session_id):
        """ set the set test session id which is get form com_module """
        self.session_id = session_id

    def set_capability(self, capabilities):
        """ set capabilitys  """
        self.capabilities = capabilities
        self.has_capability = True

    def prepare_run(self, testxmlfile, resultdir=None):
        """
        testxmlfile: target testxml file
        execdir and resultdir: should be the absolute path since TestSession
        is the common lib
        """
        # resultdir is set to current directory by default
        if not resultdir:
            resultdir = os.getcwd()
        try:
            filename = testxmlfile
            filename = os.path.splitext(filename)[0]
            os_ver = platform.system()
            if os_ver == "Linux" or os_ver == "Darwin":
                file_items = filename.split('/')
            else:
                file_items = filename.split('\\')
            if len(file_items) < 2 or file_items[-2] == "" or file_items[-1] == "":
                return False
            filename = file_items[-2] + '_' + file_items[-1]
            if self.filter_rules["execution_type"] == ["manual"]:
                resultfile = "%s.manual.xml" % filename
            else:
                resultfile = "%s.auto.xml" % filename
            resultfile = JOIN(resultdir, resultfile)
            if not EXISTS(resultdir):
                os.mkdir(resultdir)
            LOGGER.info("[ analysis test xml file: %s ]" % resultfile)
            self.__prepare_result_file(testxmlfile, resultfile)
            self.__split_test_xml(resultfile, resultdir)
        except IOError as error:
            LOGGER.error(error)
            return False
        return True

    def __split_test_xml(self, resultfile, resultdir):
        """ split_test_xml into auto and manual"""
        setfind = etree.parse(resultfile).getiterator('set')
        if setfind:
            test_file_name = "%s" % BASENAME(resultfile)
            test_file_name = os.path.splitext(test_file_name)[0]
            self.__splite_external_test(
                resultfile, test_file_name, resultdir)

    def __splite_external_test(self, resultfile, test_file_name, resultdir):
        """select external_test"""
        testsuite_dict_value_list = []
        testsuite_dict_add_flag = 0
        filename_diff = 1

        parser = etree.parse(resultfile)
        for tsuite in parser.getiterator('suite'):
            root = etree.Element('test_definition')
            suitefilename = os.path.splitext(resultfile)[0]
            suitefilename += ".suite_%s.xml" % filename_diff
            suitefilename = JOIN(resultdir, suitefilename)
            tsuite.tail = "\n"
            root.append(tsuite)
            try:
                with open(suitefilename, 'w') as output:
                    tree = etree.ElementTree(element=root)
                    tree.write(output)
            except IOError as error:
                LOGGER.error("[ Error: create filtered result file: %s failed,\
                 error: %s ]" % (suitefilename, error))
            case_suite_find = etree.parse(
                suitefilename).getiterator('testcase')
            if case_suite_find:
                if tsuite.get('launcher'):
                    testsuite_dict_value_list.append(suitefilename)
                    if testsuite_dict_add_flag == 0:
                        self.exe_sequence.append(test_file_name)
                    testsuite_dict_add_flag = 1
                    self.resultfiles.add(suitefilename)
                else:
                    if self.filter_rules["execution_type"] == ["auto"]:
                        self.core_auto_files.append(suitefilename)
                    else:
                        self.core_manual_files.append(suitefilename)
                    self.resultfiles.add(suitefilename)
            else:
                self.unit_test_files.append(suitefilename)
                self.resultfiles.add(suitefilename)                

            filename_diff += 1
        if testsuite_dict_add_flag:
            self.testsuite_dict[test_file_name] = testsuite_dict_value_list

    def __prepare_result_file(self, testxmlfile, resultfile):
        """ write the test_xml content to resultfile"""
        try:
            parse_tree = etree.parse(testxmlfile)
            suiteparent = parse_tree.getroot()
            no_test_definition = 1
            if parse_tree.getiterator('test_definition'):
                no_test_definition = 0
            if no_test_definition:
                suiteparent = etree.Element('test_definition')
                suiteparent.tail = "\n"
                for suite in parse_tree.getiterator('suite'):
                    suite.tail = "\n"
                    suiteparent.append(suite)
            self.apply_filter(suiteparent)
            try:
                with open(resultfile, 'w') as output:
                    tree = etree.ElementTree(element=suiteparent)
                    tree.write(output)
            except IOError as error:
                LOGGER.error("[ Error: create filtered result file: %s failed,\
                    error: %s ]" % (resultfile, error))
        except IOError as error:
            LOGGER.error(error)
            return False

    def run_case(self, latest_dir):
        """ run case """
        # case not found
        case_ids = self.filter_rules.get('id')
        if case_ids and not self.filter_ok:
            raise TestCaseNotFoundException('Test case %s not found!' % case_ids)

        # run core auto cases
        self.__run_core_auto()

        # run webAPI cases
        self.__run_webapi_test(latest_dir)

        # run core manual cases
        self.__run_core_manual()

        # run unit test cases
        self.__run_unit_test()

    def __run_core_auto(self):
        """ core auto cases run"""
        self.core_auto_files.sort()
        for core_auto_file in self.core_auto_files:
            temp_test_xml = os.path.splitext(core_auto_file)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml += ".auto"
            # print identical xml file name
            if self.current_test_xml != temp_test_xml:
                time.sleep(3)
                LOGGER.info("\n[ testing xml: %s.xml ]" % temp_test_xml)
                self.current_test_xml = temp_test_xml
            self.__run_with_worker(core_auto_file)

    def __run_core_manual(self):
        """ core manual cases run """
        self.core_manual_files.sort()
        for core_manual_file in self.core_manual_files:
            temp_test_xml = os.path.splitext(core_manual_file)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml += ".manual"
            # print identical xml file name
            if self.current_test_xml != temp_test_xml:
                time.sleep(3)
                LOGGER.info("\n[ testing xml: %s.xml ]" % temp_test_xml)
                self.current_test_xml = temp_test_xml
            if self.non_active:
                self.skip_all_manual = True
            else:
                self.__run_with_worker(core_manual_file)

    def __run_unit_test(self):
        """ unit test cases run """
        for ut_file in self.unit_test_files:
            temp_test_xml = os.path.splitext(ut_file)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml = os.path.splitext(temp_test_xml)[0]
            temp_test_xml += ".auto"
            # print identical xml file name
            if self.current_test_xml != temp_test_xml:
                time.sleep(3)
                LOGGER.info("\n[ testing xml: %s.xml ]" % temp_test_xml)
                self.current_test_xml = temp_test_xml
                self.__run_with_worker(ut_file)

    def __run_webapi_test(self, latest_dir):
        """ run webAPI test"""
        if self.bdryrun:
            LOGGER.info("[ Web Test mode does not support dryrun ]")
            return True

        list_auto = []
        list_manual = []
        for i in self.exe_sequence:
            if i[-4::1] == "auto":
                list_auto.append(i)
            if i[-6::1] == "manual":
                list_manual.append(i)
        list_auto.sort()
        list_manual.sort()
        self.exe_sequence = []
        self.exe_sequence.extend(list_auto)
        self.exe_sequence.extend(list_manual)

        for webapi_total_file in self.exe_sequence:
            for webapi_file in self.testsuite_dict[webapi_total_file]:
                # print identical xml file name
                if self.current_test_xml != JOIN(latest_dir, webapi_total_file):
                    time.sleep(3)
                    LOGGER.info("\n[ testing xml: %s.xml ]\n"
                                % JOIN(latest_dir, webapi_total_file))
                    self.current_test_xml = JOIN(latest_dir, webapi_total_file)

                self.__run_with_worker(webapi_file)

    def __run_with_worker(self, suite_test_xml):
        """run_with_commodule,Initialization,check status,get result"""
        try:
            # prepare test set list
            test_xml_set_list = self.__split_xml_to_set(suite_test_xml)
            # create temporary parameter
            for test_xml_set in test_xml_set_list:
                LOGGER.info("\n[ run set: %s ]" % test_xml_set)
                # prepare the test JSON
                self.__prepare_external_test_json(test_xml_set)

                # init test here
                init_status = self.__init_com_module(test_xml_set)
                if not init_status:
                    continue
                # send set JSON Data to com_module
                self.testworker.run_test(
                    self.session_id, self.set_parameters)
                while True:
                    time.sleep(1)
                    # check the test status ,if the set finished,get
                    # the set_result,and finalize_test
                    if self.__check_test_status():
                        set_result = self.testworker.get_test_result(
                            self.session_id)
                        # write_result to set_xml
                        self.__write_set_result(
                            test_xml_set, set_result)
                        # shut down server
                        self.finalize_test(self.session_id)
                        break
        except IOError as error:
            LOGGER.error(
                "[ Error: fail to run webapi test xml, error: %s ]" % error)

    def __split_xml_to_set(self, webapi_file):
        """split xml by <set>"""

        LOGGER.debug("[ split xml: %s by <set> ]" % webapi_file)
        LOGGER.debug("[ this might take some time, please wait ]")
        set_number = 1
        test_xml_set_list = []
        self.resultfiles.discard(webapi_file)
        test_xml_temp = etree.parse(webapi_file)
        for test_xml_temp_suite in test_xml_temp.getiterator('suite'):
            while set_number <= len(test_xml_temp_suite.getiterator('set')):
                copy_url = os.path.splitext(webapi_file)[0]
                copy_url += "_set_%s.xml" % set_number
                copyfile(webapi_file, copy_url)
                test_xml_set_list.append(copy_url)
                self.resultfiles.add(copy_url)
                set_number += 1
        time.sleep(3)
        set_number -= 1
        LOGGER.info("[ total set number is: %s ]" % set_number)

        # only keep one set in each xml file and remove empty set
        test_xml_set_list_empty = []
        if len(test_xml_set_list) > 1:
            test_xml_set_list.reverse()
        for test_xml_set in test_xml_set_list:
            test_xml_set_tmp = etree.parse(test_xml_set)
            set_keep_number = 1
            for temp_suite in test_xml_set_tmp.getiterator('suite'):
                for test_xml_set_temp_set in temp_suite.getiterator('set'):
                    if set_keep_number != set_number:
                        temp_suite.remove(test_xml_set_temp_set)
                    else:
                        if not test_xml_set_temp_set.getiterator('testcase'):
                            test_xml_set_list_empty.append(test_xml_set)
                    set_keep_number += 1
            set_number -= 1
            test_xml_set_tmp.write(test_xml_set)
        # for empty_set in test_xml_set_list_empty:
        #     LOGGER.debug("[ remove empty set: %s ]" % empty_set)
        #     test_xml_set_list.remove(empty_set)
        #     self.resultfiles.discard(empty_set)
        if len(test_xml_set_list) > 1:
            test_xml_set_list.reverse()
        return test_xml_set_list

    def merge_resultfile(self, start_time, latest_dir):
        """ merge_result_file """
        mergefile = mktemp(suffix='.xml', prefix='tests.', dir=latest_dir)
        mergefile = os.path.splitext(mergefile)[0]
        mergefile = os.path.splitext(mergefile)[0]
        mergefile = "%s.result" % BASENAME(mergefile)
        mergefile = "%s.xml" % mergefile
        mergefile = JOIN(latest_dir, mergefile)
        end_time = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
        LOGGER.info("\n[ test complete at time: %s ]" % end_time)
        LOGGER.debug("[ start merging test result xml files, "\
            "this might take some time, please wait ]")
        LOGGER.debug("[ merge result files into %s ]" % mergefile)
        root = etree.Element('test_definition')
        root.tail = "\n"
        totals = set()

        # merge result files
        resultfiles = self.resultfiles
        totals = self.__merge_result(resultfiles, totals)

        for total in totals:
            result_xml = etree.parse(total)
            for suite in result_xml.getiterator('suite'):
                if suite.getiterator('testcase'):
                    suite.tail = "\n"
                    root.append(suite)
        # print test summary
        self.__print_summary()
        # generate actual xml file
        LOGGER.info("[ generate result xml: %s ]" % mergefile)
        if self.skip_all_manual:
            LOGGER.info("[ some results of core manual cases are N/A,"
                        "please refer to the above result file ]")
        LOGGER.info("[ merge complete, write to the result file,"
                    " this might take some time, please wait ]")
        # get useful info for xml
        # add environment node
        # add summary node
        root.insert(0, get_summary(start_time, end_time))
        root.insert(0, self.__get_environment())
        # add XSL support to testkit-lite
        declaration_text = """<?xml version="1.0" encoding="UTF-8"?>
        <?xml-stylesheet type="text/xsl" href="testresult.xsl"?>\n"""
        try:
            with open(mergefile, 'w') as output:
                output.write(declaration_text)
                tree = etree.ElementTree(element=root)
                tree.write(output, xml_declaration=False, encoding='utf-8')
        except IOError as error:
            LOGGER.error(
                "[ Error: merge result file failed, error: %s ]" % error)
        # change &lt;![CDATA[]]&gt; to <![CDATA[]]>
        replace_cdata(mergefile)
        # copy result to -o option
        try:
            if self.resultfile:
                if os.path.splitext(self.resultfile)[-1] == '.xml':
                    if not EXISTS(DIRNAME(self.resultfile)):
                        if len(DIRNAME(self.resultfile)) > 0:
                            os.makedirs(DIRNAME(self.resultfile))
                    LOGGER.info("[ copy result xml to output file:"
                                " %s ]" % self.resultfile)
                    copyfile(mergefile, self.resultfile)
                else:
                    LOGGER.info(
                        "[ Please specify and xml file for result output,"
                        " not:%s ]" % self.resultfile)
        except IOError as error:
            LOGGER.error("[ Error: fail to copy the result file to: %s,"
                         " please check if you have created its parent directory,"
                         " error: %s ]" % (self.resultfile, error))

    def __merge_result(self, setresultfiles, totals):
        """ merge set result to total"""
        resultfiles = setresultfiles
        for resultfile in resultfiles:
            totalfile = os.path.splitext(resultfile)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = os.path.splitext(totalfile)[0]
            totalfile = "%s.total" % totalfile
            totalfile = "%s.xml" % totalfile
            total_xml = etree.parse(totalfile)
            # LOGGER.info("|--[ merge webapi result file: %s ]" % resultfile)
            result_xml = etree.parse(resultfile)
            for total_suite in total_xml.getiterator('suite'):
                for total_set in total_suite.getiterator('set'):
                    for result_suite in result_xml.getiterator('suite'):
                        for result_set in result_suite.getiterator('set'):
                            # when total xml and result xml have same suite, set
                            self.__merge_result_by_name(
                                result_set, total_set, result_suite, total_suite)
            total_xml.write(totalfile)
            totals.add(totalfile)
        return totals

    def __merge_result_by_name(
            self, result_set, total_set, result_suite, total_suite):
        ''' merge result select by name'''
        if result_set.get('name') == total_set.get('name') \
                and result_suite.get('name') == total_suite.get('name'):
            if result_set.get('set_debug_msg'):
                total_set.set("set_debug_msg", result_set.get('set_debug_msg'))
            result_case_iterator = result_set.getiterator(
                'testcase')
            if result_case_iterator:
                for result_case in result_case_iterator:
                    try:
                        self.__count_result(result_case)
                        total_set.append(result_case)
                    except IOError as error:
                        LOGGER.error("[ Error: fail to append %s, error: %s ]"
                                     % (result_case.get('id'), error))

    def __count_result(self, result_case):
        """ record the pass,failed,block,N/A case number"""
        if not result_case.get('result'):
            result_case.set('result', 'N/A')
            # add empty result node structure for N/A case
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
            result_case.append(resinfo_elm)
            res_elm.text = 'N/A'
        if result_case.get('result') == "PASS":
            self.testresult_dict["pass"] += 1
        if result_case.get('result') == "FAIL":
            self.testresult_dict["fail"] += 1
        if result_case.get('result') == "BLOCK":
            self.testresult_dict["block"] += 1
        if result_case.get('result') == "N/A":
            self.testresult_dict["not_run"] += 1

    def __get_environment(self):
        """ get environment """
        device_info = self.connector.get_device_info()
        build_infos = self.connector.get_buildinfo()
        # add environment node
        environment = etree.Element('environment')
        environment.attrib['device_id'] = device_info["device_id"]
        environment.attrib['device_model'] = device_info["device_model"]
        environment.attrib['device_name'] = device_info["device_name"]
        environment.attrib['host'] = platform.platform()
        environment.attrib['lite_version'] = get_version_info()
        environment.attrib['resolution'] = device_info["resolution"]
        environment.attrib['screen_size'] = device_info["screen_size"]
        environment.attrib['build_id'] = build_infos['buildid']
        environment.attrib['device_model'] = build_infos['model']
        environment.attrib['manufacturer'] = build_infos['manufacturer']
        other = etree.Element('other')
        other.text = ""
        environment.append(other)
        environment.tail = "\n"

        return environment

    def __print_summary(self):
        """ print test summary infomation"""
        LOGGER.info("[ test summary ]")
        total_case_number = int(self.testresult_dict["pass"]) \
            + int(self.testresult_dict["fail"]) \
            + int(self.testresult_dict["block"]) \
            + int(self.testresult_dict["not_run"])
        LOGGER.info("  [ total case number: %s ]" % (total_case_number))
        if total_case_number == 0:
            LOGGER.info("[Warning: found 0 case from the result files, "
                        "if it's not right, please check the test xml files, "
                        "or the filter values ]")
        else:
            LOGGER.info("  [ pass rate: %.2f%% ]" % (float(
                self.testresult_dict["pass"]) * 100 / int(total_case_number)))
            LOGGER.info("  [ PASS case number: %s ]" %
                        self.testresult_dict["pass"])
            LOGGER.info("  [ FAIL case number: %s ]" %
                        self.testresult_dict["fail"])
            LOGGER.info("  [ BLOCK case number: %s ]" %
                        self.testresult_dict["block"])
            LOGGER.info("  [ N/A case number: %s ]" %
                        self.testresult_dict["not_run"])

    def __prepare_external_test_json(self, resultfile):
        """Run external test"""
        parameters = {}
        xml_set_tmp = resultfile
        # split set_xml by <case> get case parameters
        LOGGER.debug("[ split xml: %s by <case> ]" % xml_set_tmp)
        LOGGER.debug("[ this might take some time, please wait ]")
        try:
            parse_tree = etree.parse(xml_set_tmp)
            root_em = parse_tree.getroot()
            case_tmp = []
            for tset in root_em.getiterator('set'):
                case_order = 1
                parameters.setdefault(
                    "casecount", str(len(tset.getiterator('testcase')))
                )
                parameters.setdefault("current_set_name", xml_set_tmp)
                if tset.get("test_set_src") is not None:
                    set_entry = self.test_prefix + tset.get("test_set_src")
                    parameters.setdefault("test_set_src", set_entry)

                for tcase in tset.getiterator('testcase'):
                    case_detail_tmp = {}
                    step_tmp = []
                    parameters.setdefault("exetype", tcase.get('execution_type'))
                    parameters.setdefault("type", tcase.get('type'))
                    case_detail_tmp.setdefault("case_id", tcase.get('id'))
                    case_detail_tmp.setdefault("purpose", tcase.get('purpose'))
                    case_detail_tmp.setdefault("order", str(case_order))
                    case_detail_tmp.setdefault("onload_delay", "3")
                    case_detail_tmp.setdefault("location", "device")

                    if tcase.find('description/test_script_entry') is not None:
                        tc_entry = tcase.find(
                            'description/test_script_entry').text
                        if not tc_entry:
                            tc_entry = ""
                        case_detail_tmp["entry"] = self.test_prefix + tc_entry
                        if tcase.find(
                                'description/test_script_entry').get('timeout'):
                            case_detail_tmp["timeout"] = tcase.find(
                                'description/test_script_entry'
                            ).get('timeout')
                        if tcase.find(
                            'description/test_script_entry'
                        ).get('test_script_expected_result'):
                            case_detail_tmp["expected_result"] = tcase.find(
                                'description/test_script_entry'
                            ).get('test_script_expected_result')
                        if tcase.find(
                            'description/test_script_entry'
                        ).get('location'):
                            case_detail_tmp["location"] = tcase.find(
                                'description/test_script_entry'
                            ).get('location')
                    for this_step in tcase.getiterator("step"):
                        step_detail_tmp = {}
                        step_detail_tmp.setdefault("order", "1")
                        step_detail_tmp["order"] = str(this_step.get('order'))

                        if this_step.find("step_desc") is not None:
                            text = this_step.find("step_desc").text
                            if text is not None:
                                step_detail_tmp["step_desc"] = text

                        if this_step.find("expected") is not None:
                            text = this_step.find("expected").text
                            if text is not None:
                                step_detail_tmp["expected"] = text

                        step_tmp.append(step_detail_tmp)

                    case_detail_tmp['steps'] = step_tmp

                    if tcase.find('description/pre_condition') is not None:
                        text = tcase.find('description/pre_condition').text
                        if text is not None:
                            case_detail_tmp["pre_condition"] = text

                    if tcase.find('description/post_condition') is not None:
                        text = tcase.find('description/post_condition').text
                        if text is not None:
                            case_detail_tmp['post_condition'] = text

                    if tcase.get('onload_delay') is not None:
                        case_detail_tmp[
                            'onload_delay'] = tcase.get('onload_delay')
                    # Check performance test
                    if tcase.find('measurement') is not None:
                        measures = tcase.getiterator('measurement')
                        measures_array = []
                        for measure in measures:
                            measure_json = {}
                            measure_json['name'] = measure.get('name')
                            measure_json['file'] = measure.get('file')
                            measures_array.append(measure_json)
                        case_detail_tmp['measures'] = measures_array
                    case_tmp.append(case_detail_tmp)
                    case_order += 1
            parameters.setdefault("cases", case_tmp)
            parameters.setdefault("exetype", "")
            parameters.setdefault("type", "")
            if self.bdryrun:
                parameters.setdefault("dryrun", True)
            self.set_parameters = parameters

        except IOError as error:
            LOGGER.error("[ Error: fail to prepare cases parameters, "
                         "error: %s ]\n" % error)
            return False
        return True

    def apply_filter(self, root_em):
        """ apply filter """
        rules = self.filter_rules
        for tsuite in root_em.getiterator('suite'):
            if rules.get('suite'):
                if tsuite.get('name') not in rules['suite']:
                    root_em.remove(tsuite)
            for tset in tsuite.getiterator('set'):
                if rules.get('set'):
                    if tset.get('name') not in rules['set']:
                        tsuite.remove(tset)

            for tsuite in root_em.getiterator('suite'):
                for tset in tsuite.getiterator('set'):
                    # if there are capabilities ,do filter
                    if self.has_capability:
                        tset_status = self.__apply_capability_filter_set(tset)
                        if not tset_status:
                            tsuite.remove(tset)
                            continue
                    for tcase in tset.getiterator('testcase'):
                        if not self.__apply_filter_case_check(tcase):
                            tset.remove(tcase)
                        else:
                            self.filter_ok = True

    def __apply_filter_case_check(self, tcase):
        """filter cases"""
        rules = self.filter_rules
        for key in rules.iterkeys():
            if key in ["suite", "set"]:
                continue
            # Check attribute
            t_val = tcase.get(key)
            if t_val:
                if not t_val in rules[key]:
                    return False
            else:
                # Check sub-element
                items = tcase.getiterator(key)
                if items:
                    t_val = []
                    for i in items:
                        t_val.append(i.text)
                    if len(set(rules[key]) & set(t_val)) == 0:
                        return False
                else:
                    return False
        return True

    def __apply_capability_filter_set(self, tset):
        """ check the set required capability with  self.capabilities """

        for tcaps in tset.getiterator('capabilities'):
            for tcap in tcaps.getiterator('capability'):
                capname = None
                capvalue = None
                capname = tcap.get('name').lower()
                if tcap.find('value') is not None:
                    capvalue = tcap.find('value').text

                if capname in self.capabilities:
                    if capvalue is not None:
                        if capvalue != self.capabilities[capname]:
                            # if capability value is not equal ,remove the case
                            return False
                else:
                    # if does not hava this capability ,remove case
                    return False
        return True

    # sdx@kooltux.org: parse measures returned by test script
    # and insert in XML result
    # see xsd/test_definition.xsd: measurementType
    _MEASURE_ATTRIBUTES = ['name', 'value', 'unit',
                           'target', 'failure', 'power']

    def __insert_measures(self, case, buf, pattern="###[MEASURE]###"):
        """ get measures """
        measures = self.__extract_measures(buf, pattern)
        for measure in measures:
            m_elm = etree.Element('measurement')
            for key in measure:
                m_elm.attrib[key] = measure[key]
            case.append(m_elm)

    def __extract_measures(self, buf, pattern):
        """
        This function extracts lines from <buf> containing the defined
        <pattern>. For each line containing the pattern, it extracts the
        string to the end of line Then it splits the content in multiple
        fields using the defined separator <field_sep> and maps the fields
        to measurement attributes defined in xsd. Finally, a list containing
        all measurement objects found in input buffer is returned
        """
        out = []
        for line in buf.split("\n"):
            pos = line.find(pattern)
            if pos < 0:
                continue

            measure = {}
            elts = collections.deque(line[pos + len(pattern):].split(':'))
            for k in self._MEASURE_ATTRIBUTES:
                if len(elts) == 0:
                    measure[k] = ''
                else:
                    measure[k] = elts.popleft()

            # don't accept unnamed measure
            if measure['name'] != '':
                out.append(measure)
        return out

    def __init_com_module(self, testxml):
        """
            send init test to com_module
            if webapi test,com_module will start testkit-stub
            else com_module send the test case to devices
        """
        starup_prms = self.__prepare_starup_parameters(testxml)
        # init stub and get the session_id
        session_id = self.testworker.init_test(starup_prms)
        if session_id == None:
            LOGGER.error("[ Error: Initialization Error]")
            return False
        else:
            self.set_session_id(session_id)
            return True

    def __prepare_starup_parameters(self, testxml):
        """ prepare_starup_parameters """

        starup_parameters = {}
        LOGGER.info("[ preparing for startup options ]")
        try:
            parse_tree = etree.parse(testxml)
            tsuite = parse_tree.getroot().getiterator('suite')[0]
            tset = parse_tree.getroot().getiterator('set')[0]
            if tset.get("launcher") is not None:
                starup_parameters[OPT_LAUNCHER] = tset.get("launcher")
            else:
                starup_parameters[OPT_LAUNCHER] = tsuite.get("launcher")
            if tsuite.get("extension") is not None:
                starup_parameters[OPT_EXTENSION] = tsuite.get("extension")
            if tsuite.get("widget") is not None:
                starup_parameters[OPT_WIDGET] = tsuite.get("widget")
            starup_parameters[OPT_SUITE] = tsuite.get("name")
            starup_parameters[OPT_SET] = tset.get("name")
            starup_parameters[OPT_STUB] = self.stub_name
            if self.external_test is not None and \
            starup_parameters[OPT_LAUNCHER].find(self.external_test) == -1:
                    starup_parameters[OPT_LAUNCHER] = self.external_test
                    starup_parameters[OPT_EXTENSION] = self.external_test.split(' ')[0]
            starup_parameters[OPT_DEBUG] = self.debug
            if self.resultfile:
                debug_dir = DIRNAME(self.resultfile)
                debug_name = os.path.splitext(BASENAME(self.resultfile))[0]
                if not EXISTS(debug_dir):
                    os.makedirs(debug_dir)
            else:
                debug_dir = DIRNAME(testxml)
                debug_name = os.path.splitext(BASENAME(testxml))[0]
            starup_parameters[OPT_DEBUG_LOG] = JOIN(debug_dir, debug_name)
            self.debug_log_file = starup_parameters[OPT_DEBUG_LOG] + '.dlog'
            if self.rerun:
                starup_parameters[OPT_RERUN] = self.rerun
            if len(self.capabilities) > 0:
                starup_parameters[OPT_CAPABILITY] = self.capabilities
        except IOError as error:
            LOGGER.error(
                "[ Error: prepare starup parameters, error: %s ]" % error)
        return starup_parameters

    def __check_test_status(self):
        '''
            get_test_status from com_module
            check the status
            if end ,return ture; else return False
        '''
        # check test running or end
        # if the status id end return True ,else return False
        session_status = self.testworker.get_test_status(self.session_id)
        if not session_status == None:
            if session_status["finished"] == "0":
                progress_msg_list = session_status["msg"]
                for line in progress_msg_list:
                    LOGGER.info(line)
                return False
            elif session_status["finished"] == "1":
                return True
        else:
            LOGGER.error("[ session status error ,pls finalize test ]\n")
            # return True to finished this set  ,becasue server error
            return True

    def finalize_test(self, sessionid):
        '''shut_down testkit-stub'''
        try:
            self.testworker.finalize_test(sessionid)
        except Exception as error:
            LOGGER.error("[ Error: fail to close webapi http server, "
                         "error: %s ]" % error)

    def get_capability(self, file_name):
        """get_capability from file """
        if file_name is None:
            return True
        capability_xml = file_name
        capabilities = {}
        try:
            parse_tree = etree.parse(capability_xml)
            root_em = parse_tree.getroot()
            for tcap in root_em.getiterator('capability'):
                capability = get_capability_form_node(tcap)
                capabilities = dict(capabilities, **capability)

            self.set_capability(capabilities)
            return True
        except IOError as error:
            LOGGER.error(
                "[ Error: fail to parse capability xml, error: %s ]" % error)
            return False

    def __write_set_result(self, testxmlfile, result):
        """
            get the result JSON form com_module,
            write them to orignal testxmlfile
        """
        # write the set_result to set_xml
        set_result_xml = testxmlfile
        # covert JOSN to python dict string
        set_result = result
        if 'resultfile' in set_result:
            write_file_result(set_result_xml, set_result, self.debug_log_file)
        else:
            write_json_result(set_result_xml, set_result, self.debug_log_file)


def get_capability_form_node(capability_em):
    ''' splite capability key and value form element tree'''
    tmp_key = ''
    capability = {}
    tcap = capability_em
    if tcap.get("name"):
        tmp_key = tcap.get("name").lower()

    if tcap.get("type").lower() == 'boolean':
        if tcap.get("support").lower() == 'true':
            capability[tmp_key] = True

    if tcap.get("type").lower() == 'integer':
        if tcap.get("support").lower() == 'true':
            if tcap.getiterator(
                    "value") and tcap.find("value").text is not None:
                capability[tmp_key] = int(tcap.find("value").text)

    if tcap.get("type").lower() == 'string':
        if tcap.get("support").lower() == 'true':
            if tcap.getiterator(
                    "value") and tcap.find("value").text is not None:
                capability[tmp_key] = tcap.find("value").text

    return capability


def get_version_info():
    """
        get testkit tool version ,just read the version in VERSION file
        VERSION file must put in /opt/testkit/lite/
    """
    try:
        config = ConfigParser.ConfigParser()
        if platform.system() == "Linux":
            config.read('/opt/testkit/lite/VERSION')
        else:
            version_file = os.path.join(sys.path[0], 'VERSION')
            config.read(version_file)
        version = config.get('public_version', 'version')
        return version
    except KeyError as error:
        LOGGER.error(
            "[ Error: fail to parse version info, error: %s ]\n" % error)
        return ""


def replace_cdata(file_name):
    """ replace some character"""
    try:
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
    except IOError as error:
        LOGGER.error("[ Error: fail to replace cdata in the result file, "
                     "error: %s ]\n" % error)


def extract_notes(buf, pattern):
    """util func to split lines in buffer, search for pattern on each line
    then concatenate remaining content in output buffer"""
    out = ""
    for line in buf.split("\n"):
        pos = line.find(pattern)
        if pos >= 0:
            out += line[pos + len(pattern):] + "\n"
    return out

# sdx@kooltux.org: parse notes in buffer and insert them in XML result


def insert_notes(case, buf, pattern="###[NOTE]###"):
    """ insert notes"""
    desc = case.find('description')
    if desc is None:
        return

    notes_elm = desc.find('notes')
    if notes_elm is None:
        notes_elm = etree.Element('notes')
        desc.append(notes_elm)
    if notes_elm.text is None:
        notes_elm.text = extract_notes(buf, pattern)
    else:
        notes_elm.text += "\n" + extract_notes(buf, pattern)


def get_summary(start_time, end_time):
    """ set summary node """
    summary = etree.Element('summary')
    summary.attrib['test_plan_name'] = "Empty test_plan_name"
    start_at = etree.Element('start_at')
    start_at.text = start_time
    end_at = etree.Element('end_at')
    end_at.text = end_time
    summary.append(start_at)
    summary.append(end_at)
    summary.tail = "\n  "
    return summary


def write_file_result(set_result_xml, set_result, debug_log_file):
    """write xml result file"""
    result_file = set_result['resultfile']
    try:
        test_tree = etree.parse(set_result_xml)
        test_em = test_tree.getroot()
        result_tree = etree.parse(result_file)
        result_em = result_tree.getroot()
        dubug_file = BASENAME(debug_log_file)
        for result_suite in result_em.getiterator('suite'):
            for result_set in result_suite.getiterator('set'):
                for test_suite in test_em.getiterator('suite'):
                    for test_set in test_suite.getiterator('set'):
                        if result_set.get('name') == \
                                test_set.get('name'):
                            result_set.set("set_debug_msg", dubug_file)
                            test_suite.remove(test_set)
                            test_suite.append(result_set)
        test_tree.write(set_result_xml)
        os.remove(result_file)
        LOGGER.info("[ cases result saved to resultfile ]\n")
    except OSError as error:
        traceback.print_exc()
        LOGGER.error(
            "[ Error: fail to write cases result, error: %s ]\n" % error)


def __expand_subcases(tset, tcase, sub_num, result_msg):
    sub_case_result = result_msg.split("[assert]")[1:]
    for i in range(sub_num):
        sub_case = copy.deepcopy(tcase)
        sub_case.set("id", "/".join([tcase.get("id"), str(i+1)]))
        sub_case.set("purpose", "/".join([tcase.get("purpose"), str(i+1)]))
        sub_case.remove(sub_case.find("./result_info"))
        result_info = etree.SubElement(sub_case, "result_info")
        actual_result = etree.SubElement(result_info, "actual_result")
        stdout = etree.SubElement(result_info, "stdout")
        if i < len(sub_case_result):
            sub_info = sub_case_result[i].split('[message]')
            print sub_info
            sub_case.set("result", sub_info[0].upper())
            actual_result.text = sub_info[0].upper()
            stdout.text = sub_info[1]
        else:
            sub_case.set("result", "")
            actual_result.text = ""
            stdout.text = ""
        tset.append(sub_case)
    tset.remove(tcase)


def __write_by_create(tset, case_results):
    for case_result in case_results:
        tcase = etree.Element('testcase')
        tcase.set('id', case_result['case_id'])
        tcase.set('purpose', case_result['purpose'])
        tcase.set('result', case_result['result'].upper())
        result_info = etree.SubElement(tcase, "result_info")
        actual_result = etree.SubElement(result_info, "actual_result")
        actual_result.text = case_result['result'].upper()
        start = etree.SubElement(result_info, "start")
        end = etree.SubElement(result_info, "end")
        stdout = etree.SubElement(result_info, "stdout")
        stderr = etree.SubElement(result_info, "stderr")
        if 'start_at' in case_result:
            start.text = case_result['start_at']
        if 'end_at' in case_result:
            end.text = case_result['end_at']
        if 'stdout' in case_result:
            stdout.text = str2xmlstr(case_result['stdout'])
        if 'stderr' in case_result:
            stderr.text = str2xmlstr(case_result['stderr'])
        tset.append(tcase)


def __write_by_caseid(tset, case_results):
    for tcase in tset.getiterator('testcase'):
        for case_result in case_results:
            if tcase.get("id") == case_result['case_id']:
                tcase.set('result', case_result['result'].upper())
                # Check performance test
                if tcase.find('measurement') is not None:
                    for measurement in tcase.getiterator(
                            'measurement'):
                        if 'measures' in case_result:
                            m_results = case_result['measures']
                            for m_result in m_results:
                                if measurement.get('name') == \
                                        m_result['name'] and 'value' in m_result:
                                    measurement.set(
                                        'value', m_result[
                                            'value'])
                if tcase.find("./result_info") is not None:
                    tcase.remove(tcase.find("./result_info"))
                result_info = etree.SubElement(tcase, "result_info")
                actual_result = etree.SubElement(
                    result_info, "actual_result")
                actual_result.text = case_result['result'].upper()
                start = etree.SubElement(result_info, "start")
                end = etree.SubElement(result_info, "end")
                stdout = etree.SubElement(result_info, "stdout")
                stderr = etree.SubElement(result_info, "stderr")
                if 'start_at' in case_result:
                    start.text = case_result['start_at']
                if 'end_at' in case_result:
                    end.text = case_result['end_at']
                if 'stdout' in case_result:
                    stdout.text = str2xmlstr(case_result['stdout'])
                if 'stderr' in case_result:
                    stderr.text = str2xmlstr(case_result['stderr'])
                if tcase.get("subcase") is not None:
                    sub_num = int(tcase.get("subcase"))
                    result_msg = case_result['stdout']
                    __expand_subcases(tset, tcase, sub_num, result_msg)


def write_json_result(set_result_xml, set_result, debug_log_file):
    ''' fetch result form JSON'''

    case_results = set_result["cases"]
    try:
        parse_tree = etree.parse(set_result_xml)
        root_em = parse_tree.getroot()
        dubug_file = BASENAME(debug_log_file)
        for tset in root_em.getiterator('set'):
            tset.set("set_debug_msg", dubug_file)
            if tset.get('test_set_src') is not None:
                __write_by_create(tset, case_results)
            else:
                __write_by_caseid(tset, case_results)
        parse_tree.write(set_result_xml)
        LOGGER.info("[ cases result saved to resultfile ]\n")
    except IOError as error:
        traceback.print_exc()
        LOGGER.error(
            "[ Error: fail to write cases result, error: %s ]\n" % error)
