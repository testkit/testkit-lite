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
#              Liu,chengtao <chengtaox.liu@intel.com>
"""Test connector for test instance and target instance"""

from .log import LOGGER

class InvalidDeviceException(Exception):
    """ 
    Device_Id not defined / Invalid Exception
    """
    __data = ""
    def __init__(self, data):
        self.__data = data

    def __str__(self):
        return self.__data


class Connector:

    """Communication module for test host and test remote"""

    def __init__(self, config):
        self.conn = None
        if "testmode" in config:
            try:
                exec "from impl.%s import get_target_conn" % config[
                    "testmode"]
                device_no = config.get('deviceid', None)
                if device_no is not None:
                    self.conn = get_target_conn(device_no)
                else:
                    self.conn = get_target_conn()
            except Exception as error:
                LOGGER.error("[ Error: Initialize communication failed,"
                             " exception: % s]\n" % error)

    def get_connector(self):
        """list the handler instance"""
        return self.conn
