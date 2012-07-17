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
#              Wang, Jing <jing.j.wang@intel.com>
#
# Description:
#   text report for TRunner
#
import os
import xml.etree.ElementTree as etree
from testkitlite.common.str2 import *
from testkitlite.common.tree import *


###############################################################################
class TestResultsTextReport:
    """text report
    """

    COLUMN = ["TYPE", "PASS", "FAIL", "N/A"]
    MIN_IWIDTH = 10

    def report(self, xmlfile):
        try:
            ep = etree.parse(xmlfile)
            testsuites = ep.getiterator('suite')
            xmlfile = os.path.basename(xmlfile) 
            # figure out rwidthfmt and iwidthfmt
            # rwidth: width of column for result type
            # iwidth: width of column for item(testresult/suite/set/case...)

            iwidth = self.MIN_IWIDTH
            iwidth = max(iwidth, Tree.INDENT + len(xmlfile))
            iwidth = max(iwidth, Tree.INDENT*2 + 1 + max([0]+map(lambda x:len(x.get("name")), testsuites)) + 1)
            for suite in testsuites:
                testsets = suite.getiterator('set')
                iwidth = max(iwidth, Tree.INDENT*3 + 2 + max([0]+map(lambda x:len(x.get("name")), testsets)) + 1)
                for set in testsets:
                    testcases = set.getiterator('testcase')
                    iwidth = max(iwidth, Tree.INDENT*4 + 3 + max([0]+map(lambda x:len(x.get("id")), testcases)) + 1)

            rwidth = (80 - iwidth)/len(self.COLUMN)
            rwidth = max(rwidth, max(map(lambda x:len(x), self.COLUMN)) + 1)
            width  = iwidth + (rwidth)*len(self.COLUMN)
            rwidthfmt  = "%%%ds" %(rwidth)
            iwidthfmt  = "%%-%ds" %(iwidth)
            iwidthfmt1 = "%%-%ds" %(iwidth - Tree.INDENT)
            iwidthfmt2 = "%%-%ds" %(iwidth - Tree.INDENT*2 - 1)
            iwidthfmt3 = "%%-%ds" %(iwidth - Tree.INDENT*3 - 2)
            iwidthfmt4 = "%%-%ds" %(iwidth - Tree.INDENT*4 - 3)

            tiprow = " "*iwidth + reduce(lambda x,y:eval('"'+rwidthfmt*2+'"%(x,y)'), self.COLUMN) + "\n"
            summary = "="*35 + "TestReport" + "="*35 + "\n"
            summary += tiprow

            # generate tree
            xmlline = ""
            tree = Tree(xmlline)
            casesum, setsum, suitesum, xmlsum = {}, {}, {}, {}
            for suite in testsuites:
                suitenode = tree.addNode(tree.getRoot(), "")
                testsets = suite.getiterator('set')
                suitesum = {}
                for set in testsets:
                    setnode = tree.addNode(suitenode, "")
                    testcases = set.getiterator('testcase')
                    setsum = {}
                    for case in testcases:
                        casesum = {}
                        caseline = eval('"'+iwidthfmt4 + '"% case.get("id")')
                        result = case.get("result")
                        caseline += eval('"'+rwidthfmt + '" % "CASE"')
                        for c in self.COLUMN[1:]:
                            if result==c:
                                cur = casesum.get(c, 0)
                                casesum[c] = cur + 1
                                cur = setsum.get(c, 0)
                                setsum[c] = cur + 1
                            caseline += eval('"'+rwidthfmt + '"% str(casesum.get(c, 0))')
                        casenode = tree.addNode(setnode, caseline)
                    setline = eval('"'+iwidthfmt3 + '"% set.get("name")')
                    setline += eval('"'+rwidthfmt + '" % "SET"')
                    for c in self.COLUMN[1:]:
                        cur = suitesum.get(c, 0)
                        num = setsum.get(c, 0)
                        suitesum[c] = cur + num
                        setline += eval('"'+rwidthfmt + '"% str(num)')
                    tree.updateNode(setnode, setline)
                suiteline = eval('"'+iwidthfmt2 + '"% suite.get("name")')
                suiteline += eval('"'+rwidthfmt + '" % "SUITE"')
                for c in self.COLUMN[1:]:
                    cur = xmlsum.get(c, 0)
                    num = suitesum.get(c, 0)
                    xmlsum[c] = cur + num
                    suiteline += eval('"'+rwidthfmt + '"% str(num)')
                tree.updateNode(suitenode, suiteline)
            xmlline = eval('"'+iwidthfmt1 + '"% xmlfile')
            xmlline += eval('"'+rwidthfmt + '" % "XML"')
            for c in self.COLUMN[1:]:
                xmlline += eval('"'+rwidthfmt + '"% str(xmlsum.get(c, 0))')
            tree.updateNode(tree.getRoot(), xmlline) 
            return summary + str(tree)

        except Exception, e:
            print e
            return ""
