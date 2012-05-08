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
#   various data unit for testing
#


import copy
from types import *

from basicstruct import LimitedAttributes

# the testdefinition-syntax.xsd is defined here:
# "http://gitorious.org/qa-tools/test-definition/blobs/master/data/testdefinition-syntax.xsd"



###############################################################################
class GeneralAttributes(LimitedAttributes):
    """GeneralAttributes are used in suite/set/case
    """

    LIMITED_NAMES    = ["name", "description", "requirement", "timeout",
                        "type", "level", "manual", "insignificant"]
    LIMITED_DEFAULTS = {"name":          "",
                        "description":   "",
                        "requirement":   "",
                        "timeout":       90,
                        "type":          "unknown",
                        "level":         "unknown",
                        "manual":        False,
                        "insignificant": False}
    LIMITED_TYPES    = {"name":          [StringType],
                        "description":   [StringType],
                        "requirement":   [StringType],
                        "timeout":       [IntType, LongType, FloatType],
                        "type":          [StringType],
                        "level":         [StringType],
                        "manual":        [BooleanType],
                        "insignificant": [BooleanType]}
    LIMITED_VALUES   = {}


    @staticmethod
    def compose(child, parent):
        """compose one new GeneralAttribute from one child GeneralAttribute 
           and one parent GeneralAttribute
           (child, parent) is like:
                                   (case, set)
                                   (case, suite)
                                   (set, suite)
           The compose method could be customized
        """

        new = copy.copy(child)

        for attr in new.__dict__:

            if attr in ["name", "description"]:
                continue

            if attr in ["type", "level"] \
            and ("unknown" == new.__dict__[attr] or new.__dict__[attr] is None):
                new.__dict__[attr] = parent.__dict__[attr]
                continue

            if attr in ["timeout", "manual", "insignificant", "requirement"] \
            and new.__dict__[attr] is None:
                new.__dict__[attr] = parent.__dict__[attr]
                continue

        return new



###############################################################################
class Step(LimitedAttributes):
    """Step
    """

    LIMITED_NAMES    = ["expected_result", "result"]
    LIMITED_DEFAULTS = {"expected_result": 0, 
                        "result":          "N/A"}
    LIMITED_TYPES    = {"expected_result": [IntType], 
                        "result":          [StringType]}
    LIMITED_VALUES   = {"result":          ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.command      = None
        self.return_code  = None
        self.start        = None
        self.end          = None
        self.stdout       = None
        self.stderr       = None
        self.failure_info = None



###############################################################################
class Case(LimitedAttributes):
    """Case
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.genattri         = GeneralAttributes()
        self.composedgenattri = self.genattri

        self.description    = None
        self.subfeature     = None
        self.steps          = [] # with list of instances of Step

        self.comment        = None

        self.pset           = None

        # filter mark
        self.runit          = True
        self.getfiles       = [] # with list of file path strings


    def refreshgenattri(self):

        # update own composedgenattri
        self.composedgenattri = \
            GeneralAttributes.compose(self.genattri, self.pset.composedgenattri)


    def case_stat(self, manual=None, insignificant=None, result=None):
        """ return case if it satisfies
        """
        if (manual is None or \
            manual == self.composedgenattri.get("manual")) and \
           (insignificant is None or \
            insignificant == self.composedgenattri.get("insignificant")) and \
           (result is None or \
            result == self.get("result")):
            return [self]
        else:
            return []


###############################################################################
class Set(LimitedAttributes):
    """Set
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.genattri         = GeneralAttributes()
        self.composedgenattri = self.genattri

        self.description    = None
        self.presteps       = [] # with list of instances of Step
        self.poststeps      = [] # with list of instances of Step
        self.getfiles       = [] # with list of file path strings
        self.feature        = None
        self.cases          = [] # with list of instances of Case

        # environments is from testdefinition.xml
        self.environments   = [] # with list of string of environment
        # environment is the selected exectuion one in result.testdefinition.xml
        self.environment    = None

        self.psuite         = None

        # filter mark
        self.runit          = True


    def addcase(self, case):

        if not isinstance(case, Case):
            raise TypeError("param should be Case instance")

        case.pset = self
        case.refreshgenattri()
        self.cases.append(case)


    def refreshgenattri(self):

        # update own composedgenattri
        self.composedgenattri = \
            GeneralAttributes.compose(self.genattri, self.psuite.genattri)

        # notify each sub case to refresh genattri
        for case in self.cases:
            case.refreshgenattri()


    def case_stat(self, manual=None, insignificant=None, result=None):
        """ return satisfied case[]
        """
#        return filter(lambda x:
#               (manual is None or \
#                manual == x.composedgenattri.get("manual")) and \
#               (insignificant is None or \
#                insignificant == x.composedgenattri.get("insignificant")) and \
#               (result is None or \
#                result == x.get("result")),
#               self.cases)

        cases = []
        for case in self.cases:
            cases.extend(case.case_stat(manual, insignificant, result))
        return cases


###############################################################################
class Suite(LimitedAttributes):
    """Suite
    """

    LIMITED_NAMES    = ["result"]
    LIMITED_DEFAULTS = {"result":         "N/A"}
    LIMITED_TYPES    = {"result":         [StringType]}
    LIMITED_VALUES   = {"result":         ["PASS", "FAIL", "N/A"]}

    def __init__(self):

        self.genattri         = GeneralAttributes()
        self.composedgenattri = self.genattri

        self.description    = None
        self.domain         = None
        self.sets           = [] # with list of instances of Set

        self.ptestdefinition= None

        # filter mark
        self.runit          = True


    def addset(self, set):

        if not isinstance(set, Set):
            raise TypeError("param should be Set instance")

        set.psuite = self
        set.refreshgenattri()
        self.sets.append(set)


    def refreshgenattri(self):

        # notify each sub set to refresh genattri
        for set in self.sets:
            set.refreshgenattri()


    def case_stat(self, manual=None, insignificant=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for set in self.sets:
            cases.extend(set.case_stat(manual, insignificant, result))
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

        self.description    = None
        self.version        = None
        self.suites         = [] # with list of instances of Suite


    def addsuite(self, suite):

        if not isinstance(suite, Suite):
            raise TypeError("param should be Suite instance")

        suite.ptestdefinition = self
        suite.refreshgenattri()
        self.suites.append(suite)


    def case_stat(self, manual=None, insignificant=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for suite in self.suites:
            cases.extend(suite.case_stat(manual, insignificant, result))
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

        self.environment    = None
        self.hwproduct      = None
        self.hwbuild        = None

        self.xmlfile        = testdefinition.xmlfile
        self.version        = testdefinition.version
        self.suites         = testdefinition.suites
        self.result         = testdefinition.result


    def case_stat(self, manual=None, insignificant=None, result=None):
        """ return satisfied cases number
        """
        cases = []
        for suite in self.suites:
            cases.extend(suite.case_stat(manual, insignificant, result))
        return cases

