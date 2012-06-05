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
#              Tian, Xu <xux.tian@intel.com>

import xml.etree.ElementTree as etree

def mergexmls(testxmls,bigxml='tests.xml'):
    '''
    append all child suite into bigtree
    '''

    testxmls   = set(testxmls)
    suites     = getsuites(testxmls)

    try:
        with open(bigxml, 'w') as fd:
            root = etree.Element('test_definition', name="merged_test")
            for suite in suites:
                root.append(suite)
            tree = etree.ElementTree(element=root)
            tree.write(bigxml)
        print "[ merged testxmls into %s ]"%bigxml
    except IOError,e:
        print "[ **merge testxmls failed**(%s) ]"%e

def getsuites(testxmls):
    suites = set()
    for testxml in testxmls:
        parser = etree.parse(testxml)
        for suite in parser.getiterator('suite'):
            suites.add(suite)
    return suites

