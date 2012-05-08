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
#   run all unittest
#

import sys
sys.path.append("../")
from runner import *

import unittest

class ManualTest(unittest.TestCase):

    def testRunnerManual(self):

        trunner = TRunner()
        trunner.add_white_rules(manual=[True])
        ret = trunner.run("manual.xml", os.path.dirname(__file__))
        print "Please check manual.xml.xmlresult manually"


if __name__=="__main__":
    unittest.main()
