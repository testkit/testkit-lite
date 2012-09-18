#!/usr/bin/python
#
# Copyright (C) 2012, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307 USA.
#
# Authors:
#              Wei, Zhang <wei.z.zhang@intel.com>
#              Zhang, Huihui <huihuix.zhang@intel.com>
#
# Description:
#   tool setup
#

import os
import platform
import glob
from distutils.core import setup

if platform.system() == "Linux":
    data_files = [('/opt/testkit/lite/xsd', ['xsd/test_definition.xsd', 'xsd/tests.css', 'xsd/testresult.xsl']),
            ('/opt/testkit/lite/', ['LICENSE']),
            ('/opt/testkit/lite/', ['README']),
            ('/opt/testkit/web/', ['web/jquery.js', 'web/index.html', 'web/manualharness.html']),
            ('/usr/share/man/man1/', ['man/testkit-lite.1'])]
else:
    data_files = []

setup(name='testkit-lite',
      description='command line test execution framework',
      version='2.2.3',
      long_description='',
      author='Zhang, Huihui',
      author_email='huihuix.zhang@intel.com',
      license='GPL V2',
      url='',
      download_url='',
      scripts=['testkit-lite'],
      packages=['testkitlite', 'testkitlite.engines', 'testkitlite.common', 'testkitlite.engines.default'],
      package_dir={'testkitlite': './testkitlite'},
      data_files=data_files,
)
