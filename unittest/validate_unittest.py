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
#   validate xml utiles
#

import sys
sys.path.append("../")
from validate import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestValidator(unittest.TestCase):

    def testValidateFail(self):
        ret = validate_xml("../xsd/testdefinition-syntax.xsd", "informal.xml")
        self.assertTrue(ret == False)

    def testValidateSchemaNegative(self):
        ret = validate_xml("../xsd/testdefinition-syntax1.xsd", "informal.xml")
        self.assertTrue(ret == False)

    def testValidateSchema(self):
        ret = validate_xml("../xsd/testdefinition-syntax.xsd", "simple.xml")
        self.assertTrue(ret == True)

if __name__=="__main__":
    unittest.main()
