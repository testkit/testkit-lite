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
#              Jing,Wang  <jing.j.wang@intel.com>
#              Yuanyuan,Zou  <zouyuanx@intel.com>

from setuptools import setup, find_packages

setup(
    name = "testkit-lite",
    description = "Test runner for test execution",
    url = "https://github.com/testkit/testkit-lite",
    author = "Cathy Shen",
    author_email = "cathy.shen@intel.com",
    version = "2.3.22",
    include_package_data = True,
    data_files = [('/opt/testkit/lite/',
              ('VERSION', 'doc/testkit-lite_user_guide_for_tct.pdf'))],
    scripts = ('testkit-lite',),
    packages = find_packages(),
)
