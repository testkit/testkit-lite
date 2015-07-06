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
"""General Config Class"""

import os
import ConfigParser
from ConfigParser import NoOptionError, NoSectionError

CONFIG_FILE = "/opt/testkit/lite/commodule/CONFIG"
cfg = ConfigParser.ConfigParser()
if os.path.exists(CONFIG_FILE):
    cfg.read(CONFIG_FILE)
else:
    cfg.read(os.path.join(os.path.dirname(__file__), "CONFIG"))


class Config:

    LOG_LEVEL = cfg.get('LOGGING', 'log_level')

    @staticmethod
    def get_extension(extension_name):
        ret = ""
        try:
            if extension_name is not None:
                ret = cfg.get('EXTENSION', extension_name)
        except (NoOptionError, NoSectionError) as error:
            pass
        except IOError as error:
            pass
        return ret
