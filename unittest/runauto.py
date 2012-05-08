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

from basicstruct_unittest import *
from runner_unittest import *
from str2_unittest import *
from testfilter_unittest import *
from testparser_unittest import *
from xmlreport_unittest import *
from textreport_unittest import *
from autoexec_unittest import *
from unit_unittest import *
from validate_unittest import *
from tree_unittest import *

if __name__=="__main__":
    unittest.main()
