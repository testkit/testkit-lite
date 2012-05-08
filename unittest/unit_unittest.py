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
#   unittest for unitunittest for unit
#

import sys
sys.path.append("../")
from unit import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestGeneralAttributes(unittest.TestCase):

    def setUp(self):
        self.ga = GeneralAttributes()

    def tearDown(self):
        del self.ga

    def testSetAttribute(self):

        ga = copy.copy(self.ga)

        ga.name = "name"
        ga.description = "description"
        ga.requirement = "requirement"
        ga.timeout = 90.0
        ga.timeout = 90
        ga.timeout = long(90)
        ga.type = "type"
        ga.level = "level"
        ga.manual = True
        ga.insignificant = False

        self.assertEqual(ga.get("name"), "name")
        self.assertEqual(ga.get("description"), "description")
        self.assertEqual(ga.get("requirement"), "requirement")
        self.assertEqual(ga.get("timeout"), long(90))
        self.assertEqual(ga.get("type"), "type")
        self.assertEqual(ga.get("level"), "level")
        self.assertEqual(ga.get("manual"), True)
        self.assertEqual(ga.get("insignificant"), False)
        
    def testGet(self):

        ga = copy.copy(self.ga)

        ga.name = None

        self.assertEqual(ga.get("name"), ga.LIMITED_DEFAULTS["name"])
        self.assertEqual(ga.get("level"), ga.LIMITED_DEFAULTS["level"])


    def testSetAttributeNegative(self):

        count = 0

        ga = copy.copy(self.ga)

        ga.name = 1
        ga.description = 2
        ga.requirement = 3
        ga.type = 4
        ga.level = 5
        ga.timeout = "90"
        ga.manual = "false"
        ga.insignificant = "false"

        # all attributes are set to None, and *get* will return default value
        for attr in ga.LIMITED_NAMES:
            self.assertEqual(ga.__dict__[attr], None)
            self.assertEqual(ga.get(attr), ga.LIMITED_DEFAULTS[attr])


    def testCompose(self):
        child  = copy.copy(self.ga)
        parent = copy.copy(self.ga)

        child.name = "child"
        child.description = None
        child.requirement = None
        child.type = "unknown"
        child.level = "child_level"
        child.timeout = 100
        child.manual = None
        child.insignificant = False

        parent.name = "parent"
        parent.description = "parent_desc"
        parent.requirement = "parent_require"
        parent.type = "parent_type"
        parent.level = "parent_level"
        parent.timeout = 80
        parent.manual = True
        parent.insignificant = True

        ga = GeneralAttributes.compose (child, parent)

        self.assertEqual(ga.name, child.name)
        self.assertEqual(ga.description, child.description)
        self.assertEqual(ga.requirement, parent.requirement)
        self.assertEqual(ga.type, parent.type)
        self.assertEqual(ga.level, child.level)
        self.assertEqual(ga.timeout, child.timeout)
        self.assertEqual(ga.manual, parent.manual)
        self.assertEqual(ga.insignificant, child.insignificant)


class TestMisc(unittest.TestCase):

    def test1(self):
        """ test "result" in step/case/set/suite/testdefinition
        """

        step  = Step()
        case  = Case()
        set   = Set()
        suite = Suite()
        td    = TestDefinition()

        # default value check
        self.assertEqual(step.get("result"), "N/A")
        self.assertEqual(case.get("result"), "N/A")
        self.assertEqual(set.get("result"), "N/A")
        self.assertEqual(suite.get("result"), "N/A")
        self.assertEqual(td.get("result"), "N/A")

        # set value check
        step.result = "FAIL"
        case.result = "FAIL"
        set.result = "FAIL"
        suite.result = "FAIL"
        td.result = "FAIL"
        self.assertEqual(step.get("result"), "FAIL")
        self.assertEqual(case.get("result"), "FAIL")
        self.assertEqual(set.get("result"), "FAIL")
        self.assertEqual(suite.get("result"), "FAIL")
        self.assertEqual(td.get("result"), "FAIL")
        
        # illegal value check
        step.result = "NOTSUPPORT"
        case.result = "NOTSUPPORT"
        set.result = "NOTSUPPORT"
        suite.result = "NOTSUPPORT"
        td.result = "NOTSUPPORT"
        self.assertEqual(step.get("result"), "N/A")
        self.assertEqual(case.get("result"), "N/A")
        self.assertEqual(set.get("result"), "N/A")
        self.assertEqual(suite.get("result"), "N/A")
        self.assertEqual(td.get("result"), "N/A")



class TestSuiteSetCase(unittest.TestCase):

    def init(self):

        self.case_a1 = Case()
        self.case_a2 = Case()
        self.case_a3 = Case()
        self.case_a4 = Case()
        self.case_b1 = Case()
        self.case_b2 = Case()
        self.case_b3 = Case()
        self.case_b4 = Case()

        self.case_a1.genattri.name = "case_a1"
        self.case_a2.genattri.type = "unknown"
        self.case_a3.genattri.timeout = None
        self.case_a4.genattri.requirement = None
        self.case_b1.genattri.description = None
        self.case_b2.genattri.level = "b2_level"
        self.case_b3.genattri.manual = True
        self.case_b4.genattri.insignificant = None

        self.set_a = Set()
        self.set_b = Set()

        self.set_a.genattri.name = "set_a"
        self.set_a.genattri.type = "setAType"
        self.set_a.genattri.timeout = 60
        self.set_a.genattri.requirement = None
        self.set_b.genattri.description = "set_b_description"
        self.set_b.genattri.level = "b_set_level"
        self.set_b.genattri.manual = False
        self.set_b.genattri.insignificant = None

        self.suite = Suite()

        self.suite.genattri.name = "suite"
        self.suite.genattri.type = "suiteType"
        self.suite.genattri.timeout = 20
        self.suite.genattri.requirement = "suiteRequirement"
        self.suite.genattri.description = "suite_description"
        self.suite.genattri.level = "suite_level"
        self.suite.genattri.manual = None
        self.suite.genattri.insignificant = False


    def validate(self):

        self.assertTrue(self.case_a1 in self.set_a.cases)
        self.assertTrue(self.case_a2 in self.set_a.cases)
        self.assertTrue(self.case_a3 in self.set_a.cases)
        self.assertTrue(self.case_a4 in self.set_a.cases)
        self.assertTrue(self.case_b1 in self.set_b.cases)
        self.assertTrue(self.case_b2 in self.set_b.cases)
        self.assertTrue(self.case_b3 in self.set_b.cases)
        self.assertTrue(self.case_b4 in self.set_b.cases)
        self.assertTrue(self.set_a in self.suite.sets)
        self.assertTrue(self.set_b in self.suite.sets)

        # test composedgenattri is as expected
        self.assertEqual(self.case_a1.composedgenattri.name,"case_a1")
        self.assertEqual(self.case_a2.composedgenattri.type, "setAType")
        self.assertEqual(self.case_a3.composedgenattri.timeout, 60)
        self.assertEqual(self.case_a4.composedgenattri.requirement, "suiteRequirement")
        self.assertEqual(self.case_b1.composedgenattri.description, None)
        self.assertEqual(self.case_b2.composedgenattri.level, "b2_level")
        self.assertEqual(self.case_b3.composedgenattri.manual, True)
        self.assertEqual(self.case_b4.composedgenattri.insignificant, False)

        self.assertEqual(self.set_a.composedgenattri.name, "set_a")
        self.assertEqual(self.set_a.composedgenattri.type, "setAType")
        self.assertEqual(self.set_a.composedgenattri.timeout, 60)
        self.assertEqual(self.set_a.composedgenattri.requirement, "suiteRequirement")
        self.assertEqual(self.set_b.composedgenattri.description, "set_b_description")
        self.assertEqual(self.set_b.composedgenattri.level, "b_set_level")
        self.assertEqual(self.set_b.composedgenattri.manual, False)
        self.assertEqual(self.set_b.composedgenattri.insignificant, False)

    def setUp(self):
        self.init()

    def tearDown(self):
        del self.case_a1, self.case_a2, self.case_a3, self.case_a4, \
            self.case_b1, self.case_b2, self.case_b3, self.case_b4
        del self.set_a, self.set_b
        del self.suite

    def testAdd1(self):

        self.init()

        # test add turn mode 1
        self.set_a.addcase(self.case_a1)
        self.set_a.addcase(self.case_a2)
        self.set_a.addcase(self.case_a3)
        self.set_a.addcase(self.case_a4)
        self.set_b.addcase(self.case_b1)
        self.set_b.addcase(self.case_b2)
        self.set_b.addcase(self.case_b3)
        self.set_b.addcase(self.case_b4)
        self.suite.addset(self.set_a)
        self.suite.addset(self.set_b)

        self.validate()

    def testAdd2(self):

        self.init()

        # test add turn mode 2
        self.suite.addset(self.set_a)
        self.suite.addset(self.set_b)
        self.set_a.addcase(self.case_a1)
        self.set_a.addcase(self.case_a2)
        self.set_a.addcase(self.case_a3)
        self.set_a.addcase(self.case_a4)
        self.set_b.addcase(self.case_b1)
        self.set_b.addcase(self.case_b2)
        self.set_b.addcase(self.case_b3)
        self.set_b.addcase(self.case_b4)

        self.validate()

    def testAdd3(self):

        self.init()

        # test add turn mode 2
        self.suite.addset(self.set_a)
        self.set_a.addcase(self.case_a1)
        self.set_a.addcase(self.case_a2)
        self.set_a.addcase(self.case_a3)
        self.set_a.addcase(self.case_a4)
        self.suite.addset(self.set_b)
        self.set_b.addcase(self.case_b1)
        self.set_b.addcase(self.case_b2)
        self.set_b.addcase(self.case_b3)
        self.set_b.addcase(self.case_b4)

        self.validate()

    def testStatistic1(self):
        from testparser import *
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        self.assertEqual(len(td.case_stat()), 6)
        self.assertEqual(len(td.suites[0].case_stat()), 0)
        self.assertEqual(len(td.suites[1].case_stat()), 6)
        self.assertEqual(len(td.suites[1].sets[0].case_stat()), 0)
        self.assertEqual(len(td.suites[1].sets[1].case_stat()), 5)
        self.assertEqual(len(td.suites[1].sets[2].case_stat()), 1)

    def testStatistic2(self):
        from testparser import *
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        self.assertEqual(len(td.case_stat(manual=True)), 0)
        self.assertEqual(len(td.case_stat(manual=False)), 6)
        self.assertEqual(len(td.case_stat(insignificant=False)), 4)
        self.assertEqual(len(td.case_stat(insignificant=True)), 2)
        self.assertEqual(len(td.case_stat(result="N/A")), 6)
        self.assertEqual(len(td.case_stat(result="PASS")), 0)
        self.assertEqual(len(td.case_stat(manual=False, insignificant=False)), 4)

if __name__=="__main__":
    unittest.main()
