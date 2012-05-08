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
#   unittest for testparser
#

import sys
sys.path.append("../")
from testparser import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestTestDefinitionParser(unittest.TestCase):

    def testParse(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

    def testParseNegative(self):
        parser = TestDefinitionParser()
        td = parser.parse("no_this_file.xml")
        self.assertTrue(td == None)

    def testParseEnvironments(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        for suite in td.suites:
            for set in suite.sets:
                if set.composedgenattri.name == "set1":
                    self.assertTrue(set.environments==["hardware"])
                    return

        # cannot reach here
        self.assertTrue(False)

    def testParseGetFiles(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        for suite in td.suites:
            for set in suite.sets:
                if set.composedgenattri.name == "set1":
                    self.assertTrue(set.getfiles==["/tmp/1.txt", "/tmp/2.txt"])
                    return

        # cannot reach here
        self.assertTrue(False)


if __name__=="__main__":
    unittest.main()
