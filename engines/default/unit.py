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
#              Xu, Tian <xux.tian@intel.com>
#
# Description:
#   various data unit for testing
#

import os
import copy
from types import *

from testkitlite.common.basicstruct import LimitedAttributes

# the test_definition.xsd is defined here:
# "http://gitorious.org/qa-tools/test-definition/blobs/master/data/test_definition.xsd"

class Step(LimitedAttributes):
    '''
    Step Object
    '''
    def __init__(self):
       self.order     = None
       self.expected  = None
       self.step_desc = None


###############################################################################
class TestCase(LimitedAttributes):
    """
    Test Case Object
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.id                 = None
        self.priority           = None
        self.status             = None
        self.notes              = None
        self.pre_condition      = None
        self.post_condition     = None
        self.entry              = None
        self.expected_result    = None
        self.type               = None
        self.purpose            = None
        self.manual             = None
        self.component          = None
        self.requirement        = None
        self.steps              = [] # with list of instances of Step
        self.timeout            = 90
        self.pset               = None
        self.return_code        = None
        self.stdout             = None
        self.stderr             = None
        self.start              = None
        self.end                = None
        self.category           = []
        self.spec               = None
        self.result             = "N/A"
        # filter mark
        self.runit              = True

    def case_stat(self,manual =None, status=None, result=None):
        """ return case if it satisfies
        """
        if (manual is None \
            or manual == self.get("manual"))\
            and (status is None or status == self.get("status"))\
            and (result is None or result == self.get("result")):
            return [self]
        else:
            return []


###############################################################################
class TestSet(LimitedAttributes):
    """
        Test Set Object
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.name           = None
        self.testcases      = [] # with list of instances of TestCase
        self.psuite         = None

        # filter mark
        self.runit          = True


    def addtestcase(self, testcase):

        if not isinstance(testcase, TestCase):
            raise TypeError("param should be TestCase instance")

        testcase.pset = self
        self.testcases.append(testcase)

    def case_stat(self,manual=None, status=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for testcase in self.testcases:
            cases.extend(testcase.case_stat(manual, status, result))
        return cases


###############################################################################
class TestSuite(LimitedAttributes):
    """TestSuite
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.name            = None
        self.testsets        = [] # with list of instances of Suite
        self.pdefinition     = None 
        self.runit           = True


    def addtestset(self, testset):

        if not isinstance(testset, TestSet):
            raise TypeError("param should be Set instance")

        testset.psuite = self
        self.testsets.append(testset)


    def case_stat(self, manual=None, status=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for testset in self.testsets:
            cases.extend(testset.case_stat(manual, status, result))
        return cases


###############################################################################
class TestDefinition(LimitedAttributes):
    """TestDefinition
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self, xmlfile=""):

        self.xmlfile        = xmlfile
        self.name           = "" 
        self.testsuites     = [] # with list of instances of Suite
        self.runit          = True


    def addtestsuite(self, testsuite):

        if not isinstance(testsuite, TestSuite):
            raise TypeError("param should be Suite instance")

        testsuite.pdefinition = self
        self.testsuites.append(testsuite)


    def case_stat(self, manual=None, status=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for testsuite in self.testsuites:
            cases.extend(testsuite.case_stat(manual, status, result))
        return cases

###############################################################################
class TestResults(LimitedAttributes):
    """TestResults
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self, testdefinition):

        if not isinstance(testdefinition, TestDefinition):
            raise TypeError("param should be TestDefinition instance")

        self.xmlfile            = testdefinition.xmlfile
        self.testsuites         = testdefinition.testsuites
        self.result             = testdefinition.result


    def case_stat(self, manual=None, status=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for suite in self.testsuites:
            cases.extend(suite.case_stat(manual, status, result))
        return cases
