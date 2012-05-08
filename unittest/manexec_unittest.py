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
#  unitest for manexec
#

import sys
sys.path.append("../")
from autoexec import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestManexec(unittest.TestCase):

    # Y
    def test01(self):
        ret = shell_exec("./manexec.sh Y")[0]
        self.assertEqual(ret, 0)

    # N
    def test02(self):
        ret = shell_exec("./manexec.sh N")[0]
        self.assertNotEqual(ret, 0)

# test
if __name__ == "__main__":
    unittest.main()
