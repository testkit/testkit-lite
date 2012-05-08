#!/usr/bin/python
#
# Copyright (C) 2010, Intel Corporation.
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
#              Wei, Zhang <wei.z.zhang@intel.com>
#
# Description:
#   testdefinition-results.xsd compatible xml report
#

from testkitlite.common.str2 import *
from testkitlite.engines.meego.unit import *
from lxml import etree


###############################################################################
class TestResultsXMLReport:
    """testdefinition-results.xsd compatible xml report
    """

    """
    nokia compatible mode:
    [x]: report attribute "x" only if x is not None
      *********************************************************************:
          testresults:
              version, environment, hwproduct, hwbuild, result(TRunner only)
          suite:
              name, result(TRunner only)
          set:
              name, environment, result(TRunner only)
              [description]
          case:
              name, manual, insignificant, result
              [description], [requirement], [level], [subfeature], [comment]
          step:
              command, result
              [failure_info]

    TRunner mode:
    [x]: report attribute "x" only if x is not None
      *********************************************************************:
          testresults:
              version, environment, hwproduct, hwbuild, result
          suite:
              name, result
              [description], [requirement], [level], [type], [manual],
              [timeout], [insignificant]
          set:
              name, environment, result
              [description], [requirement], [level], [type], [manual],
              [timeout], [insignificant]
              [feature]
          case:
              name, manual, insignificant, result
              [description], [requirement], [level], [type], [timeout]
              [subfeature], [comment]
          step:
              command, result
              [failure_info]
    """

    TESTRUNNER_FORMAT = {
        "testresults":{
              "RNG":["version", "environment", "hwproduct", "hwbuild"],
              "CNG":[],
                      },
        "suite":      {
              "RG": ["name"],
              "CG": [],
              "RNG":[],
              "CNG":[],
                      },
        "set":        {
              "RG": ["name"],
              "CG": ["description"],
              "RNG":["environment"],
              "CNG":[],
                      },
        "case":       {
              "RG": ["name", "manual", "insignificant"],
              "CG": ["description", "requirement", "level"],
              "RNG":["result"],
              "CNG":["subfeature", "comment"],
                      },
        "step":       {
              "RNG":["command", "result"],
              "CNG":["failure_info"],
                      },
    }

    TRUNNER_FORMAT = {
        "testresults":{
              "RNG":["version", "environment", "hwproduct", "hwbuild"],
              "CNG":[],
                      },
        "suite":      {
              "RG": ["name"],
              "CG": ["description", "requirement", "level", "type", "manual", "timeout", "insignificant"],
              "RNG":[],
              "CNG":[],
                      },
        "set":        {
              "RG": ["name"],
              "CG": ["description", "requirement", "level", "type", "manual", "timeout", "insignificant"],
              "RNG":["environment"],
              "CNG":["feature"],
                      },
        "case":       {
              "RG": ["name", "manual", "insignificant"],
              "CG": ["description", "requirement", "level", "type", "timeout"],
              "RNG":["result"],
              "CNG":["subfeature", "comment"],
                      },
        "step":       {
              "RNG":["command", "result"],
              "CNG":["failure_info"],
                      },
    }

    def __init__(self):
        # attributes_mode: "testrunner compatible / TRunner"
        # testrunner compatible:      compatible with nokia's testrunner
        # TRunner:                    TRunner report mode, report all available
        #                             attributes, while keep the minium set of
        #                             nokia's testrunner attributes
        self.attributes_mode = "testrunner compatible"
        self.target_format = self.TESTRUNNER_FORMAT
        self.print_nacases = True


    def set_report_mode(self, mode="testrunner compatible"):

        # select format
        if   mode == "testrunner compatible":
            self.target_format = self.TESTRUNNER_FORMAT
        elif mode == "TRunner":
            self.target_format = self.TRUNNER_FORMAT
        else: return

        self.attributes_mode = mode


    def set_report_nacases(self, p_nacases=True):

        self.print_nacases = p_nacases


    def report(self, testresults):

        try:
            testresults_root = self.__report_testresults(testresults)
            return etree.tostring(testresults_root,
                                  xml_declaration=True,
                                  encoding="UTF-8",
                                  pretty_print=True)
        except Exception, e:
            print e
            return ""


    def __element_set_attribute(self, element, attri, value):

        if value is not None:
            try:
                # compatible with xml boolean
                if type(value) == BooleanType:
                    value = str(value).lower()

                element.set(attri, str(value))
            except:
                pass


    def __element_set_text(self, element, value):

        if value is not None:
            try:
                element.text = str(value)
            except:
                pass
        else:
            element.text = ""


    def __report_required_attributes_group(self, element, unit, required):
        for attri in required:
            self.__element_set_attribute(element, attri, unit.get(attri) or "")


    def __report_common_attributes_group(self, element, unit, common):
        for attri in common:
            self.__element_set_attribute(element, attri, unit.get(attri))


    def __report_required_generalattributes(self, element, genattri_container, required):

        composedgenattri = genattri_container.get("composedgenattri")
        for attri in required:
            self.__element_set_attribute(element, attri, composedgenattri.get(attri))


    def __report_common_generalattributes(self, element, genattri_container, common):

        composedgenattri = genattri_container.get("composedgenattri")
        for attri in common:
            self.__element_set_attribute(element, attri, composedgenattri.__dict__[attri])


    def __report_generalattributes(self, element, genattri_container, elementtype):
        # Suite/Set/Case only
        if elementtype in ["suite", "set", "case"]:
            self.__report_required_generalattributes(
                element, genattri_container, self.target_format[elementtype]["RG"])
            self.__report_common_generalattributes(
                element, genattri_container, self.target_format[elementtype]["CG"])


    def __report_commonattributes(self, element, unit, elementtype):
        # TestResults/Suite/Set/Case/Step only
        if elementtype in ["testresults", "suite", "set", "case", "step"]:
            self.__report_required_attributes_group(
                element, unit, self.target_format[elementtype]["RNG"])
            self.__report_common_attributes_group(
                element, unit, self.target_format[elementtype]["CNG"])


    def __report_step(self, step):

        stepelement = etree.Element("step")

        expectedresultelement = etree.Element("expected_result")
        returncodeelement     = etree.Element("return_code")
        startelement          = etree.Element("start")
        endelement            = etree.Element("end")
        stdoutelement         = etree.Element("stdout")
        stderrelement         = etree.Element("stderr")

        self.__element_set_text(expectedresultelement, step.get("expected_result"))
        self.__element_set_text(returncodeelement, step.get("return_code"))
        self.__element_set_text(startelement, step.get("start"))
        self.__element_set_text(endelement, step.get("end"))
        self.__element_set_text(stdoutelement, step.get("stdout"))
        self.__element_set_text(stderrelement, step.get("stderr"))

        stepelement.append(expectedresultelement)
        stepelement.append(returncodeelement)
        stepelement.append(startelement)
        stepelement.append(endelement)
        stepelement.append(stdoutelement)
        stepelement.append(stderrelement)

        # deal with attributes
        self.__report_commonattributes(stepelement, step, "step")

        return stepelement


    def __report_steps(self, steps, stepselement):

        for step in steps:
            stepelement = self.__report_step(step)
            stepselement.append(stepelement)


    def __report_case(self, case):

        caseelement = etree.Element("case")

        # deal with sub-element
        self.__report_steps(case.steps, caseelement)

        # deal with attributes
        self.__report_generalattributes(caseelement, case, "case")
        self.__report_commonattributes(caseelement, case, "case")

        return caseelement


    def __report_set(self, set):

        setelement = etree.Element("set")

        # add presteps
        if len(set.presteps):
            prestepelement = etree.Element("pre_steps")
            self.__report_steps(set.presteps, prestepelement)
            setelement.append(prestepelement)

        # add poststeps
        if len(set.poststeps):
            poststepelement = etree.Element("post_steps")
            self.__report_steps(set.poststeps, poststepelement)
            setelement.append(poststepelement)

        # deal with sub-element
        for case in set.cases:
            if "N/A" != case.get("result") or True == self.print_nacases:
                caseelement = self.__report_case(case)
                setelement.append(caseelement)

        # deal with attributes
        self.__report_generalattributes(setelement, set, "set")
        self.__report_commonattributes(setelement, set, "set")

        return setelement


    def __report_suite(self, suite):

        suiteelement = etree.Element("suite")

        # deal with sub-element
        for set in suite.sets:
            setelement = self.__report_set(set)
            suiteelement.append(setelement)

        # deal with attributes
        self.__report_generalattributes(suiteelement, suite, "suite")
        self.__report_commonattributes(suiteelement, suite, "suite")

        return suiteelement


    def __report_testresults(self, testresults):

        tselement = etree.Element("testresults")

        # deal with sub-element
        for suite in testresults.suites:
            suiteelement = self.__report_suite(suite)
            tselement.append(suiteelement)

        # deal with attributes
        self.__report_commonattributes(tselement, testresults, "testresults")

        return tselement
