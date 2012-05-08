#!/usr/bin/python
# 
# Copyright (C) 2010, Intel Corporation.
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
#
# Description:
#   tool setup
#
import os
import glob
from distutils.core import setup

data_files=[('/opt/testkit/lite/xsd', ['xsd/testdefinition-syntax.xsd', 'xsd/testdefinition-results.xsd']), 
            ('/opt/testkit/lite/',    ['LICENSE']),
            ('/opt/testkit/lite/',    ['README']),
            ('/usr/share/man/man1/',  ['man/testkit-lite.1'])] 


setup(name='testkit-lite',
      description='commandline testkit runner',
      version ='1.0.5',
      long_description='',
      author='Wei, Zhang',
      author_email='wei.z.zhang@intel.com',
      license='GPL',
      url='',
      download_url='',
      scripts=['testkit-lite'],
      packages=['testkitlite'],
      package_dir={'testkitlite': '.' },
      data_files=data_files,
)
