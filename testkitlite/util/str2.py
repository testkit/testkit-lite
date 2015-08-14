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
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>
""" string convertor"""

from types import IntType, FloatType, LongType
import string


def str2str(src):
    """string to printable string"""
    if isinstance(src, unicode):
        return src.encode("utf8")

    if isinstance(src, str):
        accept = string.punctuation + string.letters + string.digits + ' \r\n'
        return filter(lambda x: x in accept, src)

    return ""


def str2val(src):
    """string to program value"""
    ret = None
    try:
        ret = eval(str2str(src))
    except:
        pass
    return ret


def str2bool(src):
    """string to boolean"""
    if "TRUE" == str2str(src).upper():
        return True
    if "FALSE" == str2str(src).upper():
        return False
    return None


def str2number(src):
    """string to boolean"""
    val = str2val(str2str(src))
    if type(val) in [IntType, FloatType, LongType]:
        return val
    else:
        return None

escape_dic = { "\xef\xbf\xbe": "u(65534)",
    "\xef\xbf\xbf": "u(65535)",
    "\x1b[": " ["
}

def str2xmlstr(src):
    """string to xml string value"""
    src = src.strip('\n')
    for key, v in escape_dic.iteritems():
        src = src.replace(key, v)
    return src
