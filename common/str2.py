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
#   string transfer utils
#

from types import *

import sys
import string

STRENCODE = "utf8"

def str2str(s):
    # unify str and unicode to str
    if isinstance(s, unicode):
        return s.encode(STRENCODE)
    if isinstance(s, str):
        s = filter(lambda x: x in string.printable, s)
        return s
    return ""

def str2val(s):

    ret = None
    try:
        ret = eval(str2str(s))
    except:
        pass

    return ret


def str2bool(s):

    if "TRUE" == str2str(s).upper():
        return True
    if "FALSE" == str2str(s).upper():
        return False

    return None


def str2number(s):

    val = str2val(str2str(s))
    if type(val) in [IntType, FloatType, LongType]:
        return val
    else:
        return None
