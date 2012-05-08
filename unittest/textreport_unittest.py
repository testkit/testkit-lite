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
#   unittest for testreport
#

import sys
sys.path.append("../")
from textreport import *
from testparser import *
from runner import TRunner

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestTestResultsTextReport(unittest.TestCase):

    def Report(self, xmlfile):
        parser = TestDefinitionParser()
        td = parser.parse(xmlfile)
        ts = TestResults(td)
        self.assertTrue(ts != None)
        runner = TRunner()
        runner.execute(td)
        report = TestResultsTextReport()

        tr = TestResults(td)

        print "default IWIDTH=%d" %report.MIN_IWIDTH
        print "\n" + report.report(tr)

        print "set IWIDTH=50"
        report.MIN_IWIDTH=50
        print "\n" + report.report(tr)

        print "set IWIDTH=70"
        report.MIN_IWIDTH=70
        print "\n" + report.report(tr)

    def testNormal(self):
        self.Report("simple.xml")

    def testLongLong(self):
        self.Report("simplelonglonglonglonglonglonglonglonglonglonglonglonglonglonglonglonglonglonglonglong.xml")

if __name__=="__main__":
    unittest.main()
