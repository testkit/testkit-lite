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
#  unitest for autoexec
#

import sys
sys.path.append("../")
from autoexec import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest

class TestTexec(unittest.TestCase):

    def test01(self):
        print "test output -------"
        ret = shell_exec("echo 'success' && cat nofile", None, True)
        print ret
        self.assertEqual(ret, [1, 'success', 'cat: nofile: No such file or directory'])

    def test02(self):
        print "test no output -------"
        ret = shell_exec("echo 'success' && cat nofile", None, False)
        print ret
        self.assertEqual(ret, [1, 'success', 'cat: nofile: No such file or directory'])

    def test03(self):
        print "test timeout 1-------"
        ret = shell_exec("echo 'timeout=2' && sleep 1 && echo 'sleep 1 DONE' && sleep 2 && echo 'sleep 2 DONE'", 2, True)
        print ret
        self.assertEqual(ret, [None, 'timeout=2\nsleep 1 DONE', ''])

    def test04(self):
        print "test timeout 2-------"
        ret = shell_exec("echo 'timeout=5' && sleep 1 && echo 'sleep 1 DONE' && sleep 2 && echo 'sleep 2 DONE'", 5, True)
        print ret
        self.assertEqual(ret, [0, 'timeout=5\nsleep 1 DONE\nsleep 2 DONE', ''])


# test
if __name__ == "__main__":
    unittest.main()
