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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Liu,chengtao <liux.chengtao@intel.com>


import logging,time,os,threading,sys
import logging.handlers

#logger levels
LEVELS={"CRITICAL" : 50,
        "ERROR"    : 40,
        "WARNING"  : 30,
        "INFO"     : 20,
        "DEBUG"    : 10,
        "NOTSET"   : 0
       } 

class Logger:
    '''Logger'''
    _instance=None
    _mutex=threading.Lock()

    def __init__(self, level="DEBUG"):
        '''Generate root logger'''
        self._logger = logging.getLogger("TCT")
        self._logger.setLevel(LEVELS[level])
        self._formatter = logging.Formatter("%(message)s")
        self.add_print_logger()

    def add_print_logger(self, level="INFO"):
        '''Generate console writer [StreamHandler]'''
        ch = logging.StreamHandler()
        ch.setLevel(LEVELS[level])
        ch.setFormatter(self._formatter)
        self._logger.addHandler(ch)

    @staticmethod
    def getLogger(level="DEBUG"):
        if(Logger._instance==None):
            Logger._mutex.acquire()
            if(Logger._instance==None):
                Logger._instance=Logger(level)
            else:
                pass
            Logger._mutex.release()
        else:
            pass
        return Logger._instance

    def debug(self,msg):
        if msg is not None:
            self._logger.debug(msg)

    def info(self,msg):
        if msg is not None:
            self._logger.info(msg)

    def warning(self,msg):
        if msg is not None:
            self._logger.warning(msg)

    def error(self,msg):
        if msg is not None:
            self._logger.error(msg)

    def critical(self,msg):
        if msg is not None:
            self._logger.critical(msg)
