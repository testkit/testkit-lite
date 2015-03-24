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
#           Chengtao,Liu  <chengtaox.liu@intel.com>
""" The implementation test result"""

import os
import threading
from testkitlite.util.log import LOGGER
from testkitlite.util.str2 import str2str


class TestSetResut(object):

    """ test result """

    _progress = "execute case: %s # %s...(%s)"
    _mutex = threading.Lock()

    def __init__(self, testsuite_name="", testset_name=""):
        self._suite_name = testsuite_name
        self._set_name = testset_name
        self._result = {"cases": []}
        self._finished = 0

    def set_status(self, flag=0):
        """set finished tag"""
        self._mutex.acquire()
        self._finished = flag
        self._mutex.release()

    def get_status(self):
        """return finished tag"""
        self._mutex.acquire()
        flag = self._finished
        self._mutex.release()
        return flag

    def set_result(self, tresult):
        """set cases result to result buffer"""
        self._mutex.acquire()
        self._result = tresult
        self._mutex.release()

    def extend_result(self, cases_result=None, print_out=True):
        """update cases result to the result buffer"""
        self._mutex.acquire()
        if cases_result is not None:
            self._result["cases"].extend(cases_result)

        if print_out:
            for case_it in cases_result:
                LOGGER.info(self._progress %
                            (self._suite_name, case_it['case_id'], case_it['result']))
                if case_it['result'].lower() in ['fail', 'block'] and 'stdout' in case_it:
                    if os.path.isdir(case_it['stdout']):
                        continue
                    else:
                        LOGGER.info(str2str(case_it['stdout']))
        self._mutex.release()

    def get_result(self):
        """get cases result from the result buffer"""
        self._mutex.acquire()
        result = self._result
        self._mutex.release()

        return result
