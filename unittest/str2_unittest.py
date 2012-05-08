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
#   unittest for str2
#

import sys
sys.path.append("../")
from str2 import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestStr2(unittest.TestCase):

    def teststr2val(self):

        self.assertTrue(str2val("#@") == None)
        self.assertTrue(str2val("False") == False)
        self.assertTrue(str2val("FAlse") == None)
        self.assertTrue(str2val("1") == 1)
        self.assertTrue(str2val("1L") == 1L)
        self.assertTrue(str2val("1.0") == 1.0)

    def teststr2bool(self):

        self.assertTrue(str2bool("True") == True)
        self.assertTrue(str2bool("False") == False)
        self.assertTrue(str2bool("FAlse") == False)

    def teststr2number(self):

        self.assertTrue(str2number("a1") == None)
        self.assertTrue(str2number("1") == 1)
        self.assertTrue(str2number("1L") == 1L)
        self.assertTrue(str2number("1.0") == 1.0)

if __name__=="__main__":
    unittest.main()
