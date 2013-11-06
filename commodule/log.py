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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#              Liu,chengtao <liux.chengtao@intel.com>
"""General Implementation"""

import threading
import logging
import logging.handlers
import sys
import os

# logger levels
LEVELS = {"CRITICAL": 50,
          "ERROR": 40,
          "WARNING": 30,
          "INFO": 20,
          "DEBUG": 10,
          "NOTSET": 0
          }


class Logger:

    """General Logger Class"""
    _instance = None
    _mutex = threading.Lock()

    def __init__(self, level="DEBUG", format_str="%(message)s"):
        """Generate root logger"""
        self._logger = logging.getLogger("TCT")
        self._logger.setLevel(LEVELS[level])
        self._formatter = logging.Formatter(format_str)
        self.add_print_logger()

    def add_print_logger(self, level="INFO"):
        """Generate console writer [StreamHandler]"""
        writer = logging.StreamHandler(sys.stdout)
        writer.setLevel(LEVELS[level])
        writer.setFormatter(self._formatter)
        self._logger.addHandler(writer)

    @staticmethod
    def get_logger(level="DEBUG", format_str="%(message)s"):
        """sinlgeton of Logger"""
        if Logger._instance is None:
            Logger._mutex.acquire()
            if Logger._instance is None:
                Logger._instance = Logger(level, format_str)
            else:
                pass
            Logger._mutex.release()
        return Logger._instance

    def debug(self, msg):
        """debug level message"""
        if msg is not None:
            sys.stdout.write(msg + '\r\n')
            sys.stdout.flush()

    def info(self, msg):
        """info level message"""
        if msg is not None:
            sys.stdout.write(msg + '\r\n')
            sys.stdout.flush()

    def warning(self, msg):
        """warning level message"""
        if msg is not None:
            self._logger.warning(msg)

    def error(self, msg):
        """error level message"""
        if msg is not None:
            sys.stdout.write(msg + '\r\n')
            sys.stdout.flush()

    def critical(self, msg):
        """critical level message"""
        if msg is not None:
            self._logger.critical(msg)


LOGGER = Logger.get_logger(level=os.environ.get('LOG_LEVEL', 'INFO'))
