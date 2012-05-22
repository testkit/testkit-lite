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
#   testdefinition-syntax.xsd compatible xml parser
#

from testkitlite.common.str2 import *
from testkitlite.engines.meego.unit import *
#from lxml import etree
import xml.etree.ElementTree as etree


###############################################################################
class TestDefinitionParser:

    """testdefinition-syntax.xsd compatible xml parser
    """

    def parse(self, xmlfile):

        try:
            tree = etree.parse(xmlfile)
            root = tree.getroot()
            return self.__parse_testdefinition(root, xmlfile)
        except Exception, e:
            print e


    def __parse_generalattributes(self, genattri, element):

        attributes = element.attrib

        genattri.name          = str2str(attributes.get("name"))
        genattri.description   = str2str(attributes.get("description"))
        genattri.requirement   = str2str(attributes.get("requirement"))
        genattri.timeout       = str2number(attributes.get("timeout"))
        genattri.type          = str2str(attributes.get("type"))
        genattri.level         = str2str(attributes.get("level"))
        genattri.manual        = str2bool(attributes.get("manual"))
        genattri.insignificant = str2bool(attributes.get("insignificant"))


    def __parse_step(self, stepelement):

        step = Step()

        step.command = str2str(stepelement.text)
        step.expected_result = str2number(stepelement.attrib.get("expected_result"))

        return step


    def __parse_steps(self, stepselement):

        steps = []

        # deal with each step
        for element in stepselement:
            if element.tag == "step":
                step = self.__parse_step(element)
                steps.append(step)

        return steps


    def __parse_getfiles(self, getelement):

        getfiles = []

        # deal with each file
        for element in getelement:
            if element.tag == "file":
                getfiles.append(str2str(element.text))

        return getfiles


    def __parse_case(self, caseelement):

        case = Case()

        # deal with generalattributes
        self.__parse_generalattributes(case.genattri, caseelement)

        # deal with sub-element
        for element in caseelement:
            if element.tag == "description":
                case.description = str2str(element.text)
            elif element.tag == "get":
                case.getfiles = self.__parse_getfiles(element)

        # deal with step group
        case.steps = self.__parse_steps(caseelement)

        # deal with other attributes
        attributes = caseelement.attrib
        case.subfeature = str2str(attributes.get("subfeature"))

        return case


    def __parse_set(self, setelement):

        set = Set()

        # deal with generalattributes
        self.__parse_generalattributes(set.genattri, setelement)

        # deal with sub-element
        for element in setelement:
            if element.tag == "case":
                case = self.__parse_case(element)
                set.addcase(case)
            elif element.tag == "description":
                set.description = str2str(element.text)
            elif element.tag == "pre_steps":
                set.presteps = self.__parse_steps(element)
            elif element.tag == "post_steps":
                set.poststeps = self.__parse_steps(element)
            elif element.tag == "get":
                set.getfiles = self.__parse_getfiles(element)
            elif element.tag == "environments":
                for e in element:
                    if str2str(e.text) == "true":
                        set.environments.append(e.tag)

        # deal with other attributes
        attributes = setelement.attrib
        set.feature = str2str(attributes.get("feature"))

        return set


    def __parse_suite(self, suiteelement):

        suite = Suite()

        # deal with generalattributes
        self.__parse_generalattributes(suite.genattri, suiteelement)

        # deal with sub-element
        for element in suiteelement:
            if element.tag == "set":
                set = self.__parse_set(element)
                suite.addset(set)
            elif element.tag == "description":
                suite.description = str2str(element.text)

        # deal with other attributes
        attributes = suiteelement.attrib
        suite.domain = str2str(attributes.get("domain"))

        return suite


    def __parse_testdefinition(self, tdelement, xmlfile):

        testdefinition = TestDefinition(xmlfile)

        # deal with sub-element
        for element in tdelement:
            if element.tag == "suite":
                suite = self.__parse_suite(element)
                testdefinition.addsuite(suite)
            elif element.tag == "description":
                testdefinition.description = str2str(element.text)

        # deal with attributes
        attributes = tdelement.attrib
        testdefinition.version = str2str(attributes.get("version"))

        return testdefinition
