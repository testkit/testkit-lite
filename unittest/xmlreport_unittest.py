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
from xmlreport import *
from testparser import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestTestResultsXMLReport(unittest.TestCase):

    def testReport1(self):
        parser = TestDefinitionParser()
        td = parser.parse("complex.xml")
        self.assertTrue(td != None)

        ts = TestResults(td)

        report = TestResultsXMLReport()
        print "\n" + report.report(ts)

    def testReport2(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)

        ts = TestResults(td)

        report = TestResultsXMLReport()
        print "\n" + report.report(ts)

    def testSetReportMode(self):
        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)
        report = TestResultsXMLReport()

        ts = TestResults(td)

        report.set_report_mode("testrunner compatible")
        print "\n" + report.report(ts)
        report.set_report_mode("TRunner")
        print "\n" + report.report(ts)

    def testValidate(self):

        parser = TestDefinitionParser()
        td = parser.parse("simple.xml")
        self.assertTrue(td != None)
        report = TestResultsXMLReport()

        tr = TestResults(td)

        report.set_report_mode("testrunner compatible")
        print >> file("forvalidate-1.xml", "w"), report.report(tr)

        from validate import validate_xml
        ret = validate_xml("../xsd/testdefinition-results.xsd", "forvalidate-1.xml")
        self.assertTrue(ret == True)

        report.set_report_mode("TRunner")
        print >> file("forvalidate-2.xml", "w"), report.report(tr)

        from validate import validate_xml
        ret = validate_xml("../xsd/testdefinition-results.xsd", "forvalidate-2.xml")
        self.assertTrue(ret == True)

if __name__=="__main__":
    unittest.main()
