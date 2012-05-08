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
#   text report for TRunner
#

from testkitlite.common.str2 import *
from testkitlite.engines.meego.unit import *
from testkitlite.common.tree import *

###############################################################################
class TestResultsTextReport:
    """text report
    """

    COLUMN = ["TYPE", "PASS", "FAIL", "N/A"]
    MIN_IWIDTH = 10

    def report(self, testresults):

        try:
            tr = testresults

            # figure out rwidthfmt and iwidthfmt
            # rwidth: width of column for result type
            # iwidth: width of column for item(testresult/suite/set/case...)

            iwidth = self.MIN_IWIDTH
            iwidth = max(iwidth, Tree.INDENT + len(tr.xmlfile))
            iwidth = max(iwidth, Tree.INDENT*2 + 1 + max([0]+map(lambda x:len(x.composedgenattri.get("name")), tr.suites)) + 1)
            for suite in tr.suites:
                iwidth = max(iwidth, Tree.INDENT*3 + 2 + max([0]+map(lambda x:len(x.composedgenattri.get("name")), suite.sets)) + 1)
                for set in suite.sets:
                    iwidth = max(iwidth, Tree.INDENT*4 + 3 + max([0]+map(lambda x:len(x.composedgenattri.get("name")), set.cases)) + 1)

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
            line = eval('"'+iwidthfmt1 + '"% tr.xmlfile')
            line += eval('"'+rwidthfmt + '" % "XML"')
            for c in self.COLUMN[1:]:
                line += eval('"'+rwidthfmt + '"% str(len(tr.case_stat(result=c)))')
            tree = Tree(line)
            for suite in tr.suites:
                line = eval('"'+iwidthfmt2 + '"% suite.composedgenattri.get("name")')
                line += eval('"'+rwidthfmt + '" % "SUITE"')
                for c in self.COLUMN[1:]:
                    line += eval('"'+rwidthfmt + '"% str(len(suite.case_stat(result=c)))')
                suitenode = tree.addNode(tree.getRoot(), line)
                for set in suite.sets:
                    line = eval('"'+iwidthfmt3 + '"% set.composedgenattri.get("name")')
                    line += eval('"'+rwidthfmt + '" % "SET"')
                    for c in self.COLUMN[1:]:
                        line += eval('"'+rwidthfmt + '"% str(len(set.case_stat(result=c)))')
                    setnode = tree.addNode(suitenode, line)
                    for case in set.cases:
                       line = eval('"'+iwidthfmt4 + '"% case.composedgenattri.get("name")')
                       line += eval('"'+rwidthfmt + '" % "CASE"')
                       for c in self.COLUMN[1:]:
                           line += eval('"'+rwidthfmt + '"% str(len(case.case_stat(result=c)))')
                       casenode = tree.addNode(setnode, line)

            return summary + str(tree)

        except Exception, e:
            print e
            return ""
