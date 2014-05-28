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
#              Yuanyuan,Zou  <yuanyuanx.zou@intel.com>

""" kill testkit-lite """
import os
import re
import dbus
import time
from testkitlite.util.log import LOGGER
from testkitlite.util.killall import killall
from testkitlite.util.autoexec import shell_command

DEVICE_DBUS = "testkit-lite-dbus"
DEVICE_WHITE_LIST = ['localhost', '127.0.0.1']


def kill_testkit_lite(pid_file):
    """ kill testkit lite"""
    try:
        with open(pid_file, "r") as pidfile:
            pid = pidfile.readline().rstrip("\n")
            if pid:
                killall(pid)
    except IOError as error:
        pattern = re.compile('No such file or directory|No such process')
        match = pattern.search(str(error))
        if not match:
            LOGGER.info("[ Error: fail to kill existing testkit-lite, "\
                "error: %s ]\n" % error)
    return None

def launch_dbus_deamon():
    exit_code, ret = shell_command(DEVICE_DBUS + '&')
    time.sleep(3)

def get_device_lock(device_id):
    """ set device lock for current testkit lite"""
    if device_id in DEVICE_WHITE_LIST:
        return True
    bus = dbus.SessionBus()
    try:
        device_service = bus.get_object('com.intel.testkit', '/com/intel/testkit/devices')
    except Exception as error:
        launch_dbus_deamon()
        device_service = bus.get_object('com.intel.testkit', '/com/intel/testkit/devices')

    try:
        ret = device_service.addDevice(device_id)
        return bool(ret)
    except Exception as error:
        return False

def release_device_lock(device_id):
    """ kill testkit lite"""
    if device_id in DEVICE_WHITE_LIST:
        return True
    bus = dbus.SessionBus()
    try:
        device_service = bus.get_object('com.intel.testkit', '/com/intel/testkit/devices')
        ret = device_service.removeDevice(device_id)
        return True
    except Exception as error:
        return False

def clean_testxml(testxmls,remote_test):
    """clean all test xmls"""
    if remote_test:
        EXISTS = os.path.exists
        for testxml in testxmls:
            if EXISTS(testxml):
                fd_name = os.path.dirname(testxml)
                os.remove(testxml)
                os.rmdir(fd_name)
    return None
