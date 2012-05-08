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
#   blackfilter and whilefilter
#

from testkitlite.engines.meego.unit import *

class Filter(object):

    FILTER_KEYS = []

    def __init__(self):
        self.black_rules = {}
        self.white_rules = {}


    def __add_rules(self, rules, key, *args):
        if key in self.FILTER_KEYS:
            rules.setdefault(key, []).extend(args)
        else:
            print "Not support %s:%s" %(self.__class__.__name__, key)


    def add_black_rule(self, key, *args):
        self.__add_rules(self.black_rules, key, *args)


    def add_white_rule(self, key, *args):
        self.__add_rules(self.white_rules, key, *args)


    def clear_black_rules(self):
        self.black_rules.clear()


    def clear_white_rules(self):
        self.white_rules.clear()


    def is_ok(self, key, value):
        """ apply blackfilter and whitefilter, get the intersect result
            value can be list or single value
        """
        values = (type(value) == type([]) and [value] or [[value]])[0]

        blacklist = self.black_rules.get(key)
        whitelist = self.white_rules.get(key)
        return (blacklist is None or 0 == len(set(values) & set(blacklist))) \
           and (whitelist is None or 0 != len(set(values) & set(whitelist)))


class UnitFilter(Filter):
    """ UnitFilter is abstract to CaseFilter/SetFilter/SuiteFilter only
    """

    COMMON_KEYS   = []
    GENATTRI_KEYS = []

    def __init__(self):
        self.FILTER_KEYS   = self.COMMON_KEYS + self.GENATTRI_KEYS
        Filter.__init__(self)

    def is_ok(self, unit):
        """ override FIlter's is_ok to filter one case
        """
        try:
            values = map(lambda x: unit.get(x), self.COMMON_KEYS) + \
                     map(lambda x: unit.composedgenattri.get(x), self.GENATTRI_KEYS)

            def ok(index):
                return Filter.is_ok(self, self.FILTER_KEYS[index], values[index])

            result = map(lambda x: ok(x), xrange(len(self.FILTER_KEYS)))
            return False not in result
        except Exception, e:
            print e
            return False


class CaseFilter(UnitFilter):

    COMMON_KEYS   = ["subfeature"]
    GENATTRI_KEYS = ["name", "requirement", "type", "level", "manual", "insignificant"]


class SetFilter(UnitFilter):

    COMMON_KEYS   = ["feature", "environments"]
    GENATTRI_KEYS = ["name"]


class SuiteFilter(UnitFilter):

    COMMON_KEYS   = ["domain"]
    GENATTRI_KEYS = ["name"]


class TestDefinitionFilter:
    """ Aggregation of CaseFilter/SetFilter/SuiteFilter
    """

    # filter mapping table
    FILTERS = {
        "testsuite":      ["SuiteFilter", "name"],
        "testset":        ["SetFilter",   "name"],
        "testcase":       ["CaseFilter",  "name"],
        "domain":         ["SuiteFilter", "domain"],
        "feature":        ["SetFilter",   "feature"],
        "environment":    ["SetFilter",   "environments"], # one environment allowed only, so delete 's'
        "subfeature":     ["CaseFilter",  "subfeature"],
        "requirement":    ["CaseFilter",  "requirement"],
        "type":           ["CaseFilter",  "type"],
        "level":          ["CaseFilter",  "level"],
        "manual":         ["CaseFilter",  "manual"],
        "insignificant":  ["CaseFilter",  "insignificant"]}


    def __init__(self):

        self.casefilter  = CaseFilter()
        self.setfilter   = SetFilter()
        self.suitefilter = SuiteFilter()


    def __dispatch_rules(self, mode, **kargs):
        """ mode:   blackfilter or whitefilter (True/False)
            kargs:  key:values - "":["",]
        """
        try:
            # add rules
            for kv in kargs.items():
                flttgt = self.FILTERS.get(kv[0])
                if not flttgt:
                    raise Exception("not support *%s* filter" %kv[0])
                else:
                    values = (type(kv[1]) == type([]) and [kv[1]] or [[kv[1]]])[0]

                    if mode:
                        if flttgt[0] == "SuiteFilter":
                            self.suitefilter.add_black_rule(flttgt[1], *values)
                        if flttgt[0] == "SetFilter":
                            self.setfilter.add_black_rule(flttgt[1], *values)
                        if flttgt[0] == "CaseFilter":
                            self.casefilter.add_black_rule(flttgt[1], *values)
                    else:
                        if flttgt[0] == "SuiteFilter":
                            self.suitefilter.add_white_rule(flttgt[1], *values)
                        if flttgt[0] == "SetFilter":
                            self.setfilter.add_white_rule(flttgt[1], *values)
                        if flttgt[0] == "CaseFilter":
                            self.casefilter.add_white_rule(flttgt[1], *values)

        except Exception, e:
            print e
            return None


    def add_black_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        self.__dispatch_rules(True, **kargs)


    def add_white_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        self.__dispatch_rules(False, **kargs)


    def clear_black_rules(self):
        self.suitefilter.clear_black_rules()
        self.setfilter.clear_black_rules()
        self.casefilter.clear_black_rules()


    def clear_white_rules(self):
        self.suitefilter.clear_white_rules()
        self.setfilter.clear_white_rules()
        self.casefilter.clear_white_rules()


    def apply_filter(self, testdefinition):
        """ filter out one new testdefinition, just modify "runit"
        """
        try:
            if not isinstance(testdefinition, TestDefinition):
                raise TypeError("param should be TestDefinition instance")

            for suite in testdefinition.suites:
                suite.runit = self.suitefilter.is_ok(suite)
                for set in suite.sets:
                    set.runit = self.setfilter.is_ok(set) & suite.runit
                    for case in set.cases:
                        case.runit = self.casefilter.is_ok(case) & set.runit
            return True
        except Exception, e:
            print e
            return False
