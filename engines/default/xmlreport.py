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
#              Wei, Zhang <wei.z.zhang@intel.com>
#              Xu, Tian <xux.tian@intel.com>
#
# Description:
#   test_definition.xsd compatible xml report
#

from testkitlite.common.str2 import *
from testkitlite.engines.default.unit import *
import xml.etree.ElementTree as etree


###############################################################################
class TestResultsXMLReport:
    """testdefinition-results.xsd compatible xml report
    """

    def __init__(self):
        self.print_nacases = False
        self.resultxml = None

    def set_report_nacases(self, p_nacases=True):

        self.print_nacases = p_nacases

    def initTestXML(self,testdefinition,testresultxmlfile):
        """Dump detials about tests to result xml file
        """

        root = self.__report_testdefinition(testdefinition)
        with open(testresultxmlfile,'w') as fd:
            if len(root.getchildren()) > 0:
               fd.write(etree.tostring(root))
            pass
        self.resultxml = testresultxmlfile

    def __element_set_attribute(self, element, attri, value):

        if value is not None:
            try:
                # compatible with xml boolean
                if type(value) == BooleanType:
                    value = str(value).lower()

                element.set(attri, str2str(value))
            except:
                pass


    def __element_set_text(self, element, value):

        if value is not None:
            try:
                element.text = str2str(value)
            except:
                pass
        else:
            element.text = ""

    def __report_step(self, step):

        stepelement = etree.Element("step",order=str(step.order))
        for attr in ["step_desc","expected"]:
            et = etree.Element(attr)
            self.__element_set_text(et,step.get(attr))
            stepelement.append(et)

        return stepelement


    def __report_steps(self, steps):

        stepselement = etree.Element("steps")
        for step in steps:
            stepelement = self.__report_step(step)
            stepselement.append(stepelement)

        return stepselement

    def __report_spec(self, case):

        specelement = etree.Element("spec")
        self.__element_set_text(specelement,case.spec)
        return specelement

    def __report_categories(self, case):

        categorieselement = etree.Element("categories")
        for category in case.category:
            categoryelement = etree.Element("category")
            self.__element_set_text(categoryelement,category)
            categorieselement.append(categoryelement)
        return categorieselement

    def __report_result_info(self,case):

        resultelement = etree.Element("result_info")
        # fill result_info element tree
        actual_resultelement = etree.Element("actual_result")
        resultelement.append(actual_resultelement)

        startelement = etree.Element("start")
        resultelement.append(startelement)

        endelement = etree.Element("end")
        resultelement.append(endelement)

        outelement = etree.Element("stdout")
        resultelement.append(outelement)

        errelement = etree.Element("stderr")
        resultelement.append(errelement)

        return resultelement

    def __report_description(self, case):

        descelement = etree.Element("description")

        # set text for description element one by one
        for element in ["notes","pre_condition","post_condition"]:
            et = etree.Element(element)
            self.__element_set_text(et,case.get(element))
            descelement.append(et)
        # append steps child one for description element tree
        stepselement = self.__report_steps(case.steps)
        descelement.append(stepselement)

        # append script entry child node
        entryelement        = etree.Element("test_script_entry")
        self.__element_set_attribute(entryelement,\
        "test_script_expected_result",case.expected_result)
        self.__element_set_attribute(entryelement,\
        "timeout",case.timeout)
        self.__element_set_text(entryelement,case.get("entry"))
        descelement.append(entryelement)

        return descelement


    def __report_case(self, case):
        """create case node """

        caseelement = etree.Element("testcase")
        #set attributes for testcase one by one
        for attr in ["component","id","priority","purpose",\
                       "requirement_ref","result","status","type"]:
            if attr == "requirement_ref":
                self.__element_set_attribute(caseelement,attr, case.get("requirement"))
            elif attr == "result":
                self.__element_set_attribute(caseelement,attr, "N/A")
            else:
                self.__element_set_attribute(caseelement,attr, case.get(attr))
        #set execution_type
        if not case.get("manual"):
           self.__element_set_attribute(caseelement,"execution_type","auto")
        else:
           self.__element_set_attribute(caseelement,"execution_type","manual")

        #append descripation node to testcase element tree
        descelement = self.__report_description(case)
        caseelement.append(descelement)

        #append result_info node to testcase element tree
        resultelement = self.__report_result_info(case)
        caseelement.append(resultelement)

        #append categories node to testcase element tree
        categorieselement = self.__report_categories(case)
        caseelement.append(categorieselement)

        #append spec node into testcase element tree
        specelement = self.__report_spec(case)
        caseelement.append(specelement)

        return caseelement


    def __report_set(self, set):
        """create set element"""

        setelement = etree.Element("set")
        self.__element_set_attribute(setelement,"name",set.name)
        # deal with testcase
        for case in set.testcases:
            if case.runit == True:
               caseelement = self.__report_case(case)
               setelement.append(caseelement)
        return setelement


    def __report_testsuite(self, testsuite):
        """create suite element"""

        tselement = etree.Element("suite")
        self.__element_set_attribute(tselement,"name",testsuite.name)
        # deal with sub-element,empty setelement will be skip
        for set in testsuite.testsets:
            if set.runit == True:
               setelement = self.__report_set(set)
               if setelement.getchildren():
                  tselement.append(setelement)
        return tselement

    def __report_testdefinition(self, testdefinition):
        """create root element"""
 
        tdelement = etree.Element("test_definition", name="merged_test")
        for suite in testdefinition.testsuites:
            if suite.runit == True:
               suiteelement = self.__report_testsuite(suite)
               if suiteelement.getchildren():
                  tdelement.append(suiteelement)
        return tdelement
        

    def __getChildrenByName(self, parent , **args ):
        """ Get a child Element by name attribute
        """

        if etree.iselement(parent):
           for children in parent.getchildren():
               name = children.get("name",None)
               if name is None:
                  name = children.get("id")
               if args["name"] == name:
                  return children
        return None

    def fillTestInfo(self,testcase,result="N/A"):
        """ Update test result info to result xml file """

        if isinstance(testcase,TestCase):
           pset = testcase.pset
        else:
           raise TypeError,"parameter one should be a instance of testcase object"

        if self.resultxml is not None:
           try:
               ep = etree.parse(self.resultxml)

               set_elt = [self.__getChildrenByName(elt,name=pset.get("name")) \
                        for elt in ep.getiterator("suite") \
                        if elt.get("name") == pset.psuite.get("name")][0]

               case_elt = [self.__getChildrenByName(elt,name=testcase.get("id")) \
                        for elt in ep.getiterator("set") \
                        if elt.get("name") == pset.get("name")][0]

               if result == "N/A" and  False == self.print_nacases:
                     #clean "N/A" test
                     set_elt.remove(case_elt)
                     if len(set_elt.getchildren()) == 0:
                        #clean empty node from suite
                        for elt in ep.getiterator("suite"):
                            if elt.get("name") == pset.psuite.get("name"):
                               elt.remove(set_elt)
               else:
                     case_elt.set("result",result)
                     for rst_inf in case_elt.getiterator("result_info"):
                       for itm in rst_inf.getchildren():
                           if itm.tag == "actual_result":
                                itm.text = str2str(testcase.return_code)
                           elif itm.tag == "start":
                                itm.text = str2str(testcase.start)
                           elif itm.tag == "end":
                                itm.text = str2str(testcase.end)
                           elif itm.tag == "stdout":
                                itm.text = str2str(testcase.stdout)
                           elif itm.tag == "stderr":
                                itm.text = str2str(testcase.stderr)
               ep.write(self.resultxml)
           except Exception, e:
               print "fill testcase (%s) result info fail"%testcase.get("id")
               print e
