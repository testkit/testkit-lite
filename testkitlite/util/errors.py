#!/usr/bin/python
#
# Copyright (C) 2013 Intel Corporation
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
#              Liu,chengtao <liux.chengtao@intel.com>
""" The definition of exceptions"""


class InvalidDeviceException(Exception):
    """
    Device_Id not defined / Invalid Exception
    """
    __data = ""
    def __init__(self, data):
        self.__data = data

    def __str__(self):
        return self.__data

class TestCaseNotFoundException(Exception):
    """
    Test case not found Exception
    """
    __data = ""
    def __init__(self, data):
        self.__data = data

    def __str__(self):
        return self.__data

class TestEngineException(Exception):
    """
    Test case not found Exception
    """
    def __init__(self, name):
        self.__engine = name

    def __str__(self):
        return "Failed to load test engine '%s'" % self.__engine
