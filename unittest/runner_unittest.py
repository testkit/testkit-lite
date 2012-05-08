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
#   unittest for runner
#

import sys
sys.path.append("../")
from runner import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestTRunner(unittest.TestCase):

    def testRun(self):

        trunner = TRunner()

        ret = trunner.run("informal.xml", os.path.dirname(__file__))

        self.assertTrue(ret == False)

        ret = trunner.run("simple.xml", os.path.dirname(__file__))

        self.assertTrue(ret == True)

    def testEnvironmentFilter(self):

        # cannot set more than one values to white rules for environment
        trunner = TRunner()
        try:
            trunner.add_white_rules(environment = ["hardware", "scratchbox"])
            self.assertTrue(False) # cannot reach here
        except:
            pass

        # black rules for environment is not allowed
        try:
            trunner.add_black_rules(environment = ["scratchbox"])
            self.assertTrue(False) # cannot reach here
        except:
            pass

        # normal
        trunner.add_white_rules(environment = ["scratchbox"])
        ret = trunner.run("simple.xml", os.path.dirname(__file__))
        self.assertTrue(ret == True)


    def testGetfiles(self):

        try:
            os.remove("/tmp/1.txt")
            os.remove("/tmp/2.txt")
            os.remove("./1.txt")
            os.remove("./2.txt")
        except:
            pass
        trunner = TRunner()
        trunner.add_white_rules(testcase=["case1_3"])
        ret = trunner.run("simple.xml", os.path.dirname(__file__))
        self.assertTrue(ret == True)

        self.assertTrue(os.path.exists("1.txt"))
        self.assertTrue(os.path.exists("2.txt"))
        

if __name__=="__main__":
    unittest.main()
