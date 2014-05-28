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

from testkitlite.util.log import LOGGER


class ConnectorBuilder:

    """Communication module for test host and test remote"""

    def __init__(self, config):
        self.conn = None
        if "commodule" in config:
            try:
                exec "from testkitlite.commodule.%s import get_target_conn" % config[
                    "commodule"]
                device_no = config.get('deviceid', None)
                if device_no is not None:
                    self.conn = get_target_conn(device_no)
                else:
                    self.conn = get_target_conn()
            except Exception as error:
                LOGGER.error("[ Error: Initialize commodule failed: '%s']\n" % error)

    def get_connector(self):
        """list the handler instance"""
        return self.conn
