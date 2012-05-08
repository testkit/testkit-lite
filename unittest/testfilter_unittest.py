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
#   unittest for filter
#

import sys
sys.path.append("../")
from testfilter import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestFilter(unittest.TestCase):

    class DemoFilter(Filter):
    
        FILTER_KEYS = ["type", "level"]

    def testAddRules(self):
        f = self.DemoFilter()

        f.add_black_rule("shape", 1,2,3)
        f.add_black_rule("type", "type1","type2")
        f.add_black_rule("type", "type3")
        f.add_black_rule("level", "level1")
        f.add_black_rule("level", "level2","level3")
        f.add_white_rule("type", "type4","type5","type6")
        f.add_white_rule("level", "level4","level5","level6")

        self.assertEqual(f.black_rules, 
                         {'type':['type1','type2','type3'],
                          'level':['level1','level2','level3']})
        self.assertEqual(f.white_rules, 
                         {'type':['type4','type5','type6'],
                          'level':['level4','level5','level6']})

        print reduce(lambda x,y: "%s=%s\n%s=%s" %(x[0],x[1],y[0],y[1]),
                      f.black_rules.items())
        print reduce(lambda x,y: "%s=%s\n%s=%s" %(x[0],x[1],y[0],y[1]),
                      f.white_rules.items())


    def testIsOK(self):

        f = self.DemoFilter()

        f.add_white_rule("type", 1,2,3)
        self.assertEqual(f.is_ok("type", 2), True)
        self.assertEqual(f.is_ok("type", 1), True)
        self.assertEqual(f.is_ok("type", 3), True)

        f.add_black_rule("level", 2)
        self.assertEqual(f.is_ok("level", 2), False)
        self.assertEqual(f.is_ok("level", 3), True)

        f.clear_white_rules()
        f.clear_black_rules()
        f.add_black_rule("type", 2)
        f.add_white_rule("type", 1,2,3)
        self.assertEqual(f.is_ok("type", 2), False)
        self.assertEqual(f.is_ok("type", 1), True)
        self.assertEqual(f.is_ok("type", 3), True)



from testparser import *
class TestCaseFilter(unittest.TestCase):

    def testIsOK(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f1 = CaseFilter()
        f2 = CaseFilter()
        f1.add_white_rule("insignificant", False)
        f1.add_black_rule("type", "functional")
        f2.add_black_rule("insignificant", False)

        for suite in td.suites:
            for set in suite.sets:
                for case in set.cases:
                    if case.composedgenattri.get("insignificant") == False:
                        if case.composedgenattri.get("type") == "functional":
                            self.assertEqual(f1.is_ok(case), False)
                        else:
                            self.assertEqual(f1.is_ok(case), True)
                        self.assertEqual(f2.is_ok(case), False)
                    else:
                        self.assertEqual(f1.is_ok(case), False)
                        self.assertEqual(f2.is_ok(case), True)


class TestSetFilter(unittest.TestCase):

    def testIsOK(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f1 = SetFilter()
        f2 = SetFilter()
        f1.add_white_rule("environments", "hardware")
        f1.add_black_rule("feature", "sample feature")
        f2.add_white_rule("name", "set1", "set2")

        for suite in td.suites:
            for set in suite.sets:
                if set.composedgenattri.get("name") == "set0":
                    self.assertEqual(f1.is_ok(set), True)
                    self.assertEqual(f2.is_ok(set), False)
                if set.composedgenattri.get("name") == "set1":
                    self.assertEqual(f1.is_ok(set), False)
                    self.assertEqual(f2.is_ok(set), True)
                if set.composedgenattri.get("name") == "set2":
                    self.assertEqual(f1.is_ok(set), False)
                    self.assertEqual(f2.is_ok(set), True)


class TestSuiteFilter(unittest.TestCase):

    def testIsOK(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f1 = SuiteFilter()
        f2 = SuiteFilter()
        f1.add_white_rule("domain", "browser")
        f2.add_black_rule("name", "trlitereg01_suite0")
        f2.add_white_rule("name", "trlitereg01_suite0", "trlitereg01_suite1")

        for suite in td.suites:
            if suite.composedgenattri.get("name") == "trlitereg01_suite0":
                self.assertEqual(f1.is_ok(suite), True)
                self.assertEqual(f2.is_ok(suite), False)
            if suite.composedgenattri.get("name") == "trlitereg01_suite1":
                self.assertEqual(f1.is_ok(suite), False)
                self.assertEqual(f2.is_ok(suite), True)


class TestTestDefinitionFilter(unittest.TestCase):

    def num_is_almost_correct(self, td, suitenum, setnum, casenum):
        """judge equal or not for testdefinitions"""
        _suitenum_, _setnum_, _casenum_ = 0, 0, 0
        _suitenum_ += len(filter(lambda x:x.runit,td.suites))
        for i in xrange(len(td.suites)):
            suite = td.suites[i]
            _setnum_ += len(filter(lambda x:x.runit,suite.sets))
            for j in xrange(len(suite.sets)):
                set = suite.sets[j]
                _casenum_ += len(filter(lambda x:x.runit,set.cases))

        self.assertEqual(_suitenum_, suitenum)
        self.assertEqual(_setnum_,   setnum)
        self.assertEqual(_casenum_,  casenum)


    def testNofilter(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f = TestDefinitionFilter()

        # filter directly
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 6)


    def testCase1(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f = TestDefinitionFilter()
        f.add_white_rules(testcase=["case1_1", "case1_2"])

        # test filter result
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 2)

        # test clear_white_rules
        f.clear_white_rules()
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 6)


    def testCase2(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f = TestDefinitionFilter()
        f.add_black_rules(testset=["set0"], feature=["sample feature"])

        # test filter result
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 1, 1)

        # test clear_black_rules
        f.clear_black_rules()
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 6)


    def testCase3(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f = TestDefinitionFilter()
        f.add_black_rules(testsuite=["trlitereg01_suite1"], domain=["browser"])

        # test filter result
        f.apply_filter(td)
        self.num_is_almost_correct(td, 0, 0, 0)

        # test clear_black_rules
        f.clear_black_rules()
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 6)


    def testCase4(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        f = TestDefinitionFilter()
        f.add_black_rules(domain=["browser"])
        f.add_white_rules(insignificant=[False])
        f.add_white_rules(type=["functional"])

        # test filter result
        f.apply_filter(td)
        self.num_is_almost_correct(td, 1, 3, 1)

        # test clear_black_rules and clear_white_rules
        f.clear_black_rules()
        f.clear_white_rules()
        f.apply_filter(td)
        self.num_is_almost_correct(td, 2, 3, 6)



if __name__=="__main__":
    unittest.main()
