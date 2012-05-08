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
#   unittest for basicstruct
#

import sys
sys.path.append("../")
from basicstruct import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest
from types import *

class TestAttributes(LimitedAttributes):

    LIMITED_NAMES    = ["result", "timeout", "freely"]

    LIMITED_DEFAULTS = {"result" : "no",
                        "timeout": 60}

    LIMITED_TYPES    = {"result":  [StringType],
                        "timeout": [IntType, LongType, FloatType]}

    LIMITED_VALUES   = {"result":    ["yes","no"]}


class TestLimitedAttributes(unittest.TestCase):

    def test1(self):
        """ normal test
        """
        ta = TestAttributes()
        ta.result = "yes"
        ta.timeout = 80

        self.assertEqual(ta.result, "yes")
        self.assertEqual(ta.get("result"), "yes")
        self.assertEqual(ta.timeout, 80)
        self.assertEqual(ta.get("timeout"), 80)

    def test2(self):
        """ test non-set attribute
        """
        ta = TestAttributes()

        self.assertEqual(ta.result, None)
        self.assertEqual(ta.get("result"), "no")
        self.assertEqual(ta.timeout, None)
        self.assertEqual(ta.get("timeout"), 60)

    def test3(self):
        """ test TYPE error
        """
        ta = TestAttributes()

        ta.result = 0

        self.assertEqual(ta.result, None)
        self.assertEqual(ta.get("result"), "no")

    def test4(self):
        """ test VALUE error
        """
        ta = TestAttributes()

        ta.result = "unknown"

        self.assertEqual(ta.result, None)
        self.assertEqual(ta.get("result"), "no")

    def test5(self):
        """ test NAME error
        """
        ta = TestAttributes()

        self.assertEqual(ta.get("notinnames"), None)

        ta.notinnames = 0

        self.assertEqual(ta.notinnames, 0)
        self.assertEqual(ta.get("notinnames"), 0)


    def test6(self):
        """ test set to None
        """
        ta = TestAttributes()

        ta.timeout = None

        self.assertEqual(ta.timeout, None)
        self.assertEqual(ta.get("timeout"), 60)


    def test7(self):
        """ test set value with no value limitation
        """
        ta = TestAttributes()

        ta.timeout = 50

        self.assertEqual(ta.timeout, 50)
        self.assertEqual(ta.get("timeout"), 50)


    def test8(self):
        """ test type/value non-limitation attribute
        """
        ta = TestAttributes()

        ta.freely = 1
        self.assertEqual(ta.freely, 1)
        self.assertEqual(ta.get("freely"), 1)

        ta.freely = "1"
        self.assertEqual(ta.freely, "1")
        self.assertEqual(ta.get("freely"), "1")


    def test9(self):
        """ test attribute of no-default value
        """
        ta = TestAttributes()
        self.assertEqual(ta.freely, None)
        self.assertEqual(ta.get("freely"), None)


    def test10(self):
        """ test if copiable
        """
        import copy
        ta1 = TestAttributes()
        ta2 = copy.copy(ta1)

if __name__=="__main__":
    unittest.main()
