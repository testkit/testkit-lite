#!/usr/bin/python
#
# Copyright (C) 2012 Intel Corporation
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>

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
