#!/usr/bin/python
#
# Copyright (C) 2012, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307 USA.
#
# Authors:
#              Tian, Xu <xux.tian@intel.com>
#              Wang, Jing <jing.j.wang@intel.com>
#              Wei, Zhang <wei.z.zhang@intel.com>
#
# Description:
#   test_definition.xsd  compatible xml parser
#

from testkitlite.common.str2 import *
from testkitlite.engines.default.unit import *
from lxml import etree


###############################################################################
class TestSuiteParser:

    """testsuite-syntax.xsd compatible xml parser
    """

    def parse(self, xmlfile):

        try:
            tree = etree.parse(xmlfile)
            root = tree.getroot()
            return self.__parse_testsuite(root, xmlfile)
        except Exception, e:
            print e

    def __parse_step(self,stepelement):

        step = Step()
        # deal with each step
        for element in stepelement:
            if element.tag == "step_desc":
                step.step_desc = str2str(element.text)
            elif element.tag == "expected":
                step.expected = str2str(element.text)
        step.order = str2number(stepelement.get("order"))
        return step

    def __parse_steps(self, stepselement):

        steps = []
        # deal with each file
        for element in stepselement:
            if element.tag == "step":
               step = self.__parse_step(element)
               steps.append(step)

        return steps

    def __parse_testcase(self, testcaseelement):
        '''
        This function parse testcase element tag by tag and fill
        testcase's attribue with elements' attribue one by one,
        if execute type of testcase is auto, get testcase entry
        file,else set entry of testcase to None;
        '''

        testcase = TestCase()

        testcase.purpose = str2str(testcaseelement.get("purpose"))
        exec_type = str2str(testcaseelement.get("execution_type"))
        if exec_type == "auto":
            testcase.manual = False
        elif exec_type == "manual":
            testcase.manual = True
        else:
            raise ValueError,"testcase execute type should be auto or manual"


        # deal with sub-element
        for element in testcaseelement:
            if element.tag == "description":
                # deal description
                for subelement in element:
                    if subelement.tag == "notes":
                        testcase.notes = str2str(subelement.text)
                    elif subelement.tag == "pre_condition":
                        testcase.pre_condition = str2str(subelement.text)
                    elif subelement.tag == "post_condition":
                        testcase.post_condition = str2str(subelement.text)
                    elif subelement.tag == "test_script_entry":
                        if exec_type == "auto":
                            testcase.entry = str2str(subelement.text)
                        else:
                            testcase.entry = None
                        testcase.expected_result = str2str(subelement.get('test_script_expected_result','0'))
                        testcase.timeout = str2number(subelement.get('timeout','90'))
                    elif subelement.tag == "steps":
                        testcase.steps = self.__parse_steps(subelement)
            if element.tag == "categories":
                for subelement in element:
                    testcase.category.append(str2str(subelement.text))
                category = set(testcase.category)
                testcase.category = list(category)
            if element.tag == "spec":
                testcase.spec = str2str(element.text)

        testcase.component = str2str(testcaseelement.get("component"))
        testcase.id = str2str(testcaseelement.get("id"))

        priority = str2str(testcaseelement.get("priority"))
        testcase.priority = priority

        status = str2str(testcaseelement.get("status"))
        testcase.status = status

        type = str2str(testcaseelement.get("type"))
        testcase.type = type

        result =str2str(testcaseelement.get("result", "N/A"))
        testcase.result = result

        testcase.requirement = str2str(testcaseelement.get("requirement_ref"))
        return testcase


    def __parse_testset(self, testsetelement):

        testset = TestSet()
        setname = testsetelement.get("name")
        testset.name = str2str(setname)

        # deal with sub-element
        for element in testsetelement:
            if element.tag == "testcase":
                testcase= self.__parse_testcase(element)
                testset.addtestcase(testcase)

        return testset


    def __parse_testsuite(self, testsuiteelement, xmlfile):

        testsuite = TestSuite(xmlfile)
        suitename = testsuiteelement.get("name")
        testsuite.name = str2str(suitename)
        # deal with sub-element
        for element in testsuiteelement:
            if element.tag == "set":
                testset = self.__parse_testset(element)
                testsuite.addtestset(testset)

        return testsuite
