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

import sys
###############################################################################

def QA(question):
    """ questions and answer
    """
    sys.stdout.write(question)
    sys.stdout.flush()

    return sys.stdin.readline().strip()


def manual_exec(step_desc):
    """ manual executor, return PASS/FAIL
    """
    ans = QA("[ CHECK ] %s\n[ RESULT ] Is it correct?(Y/N)" % step_desc)

    if ans in ['', 'Y', 'y', 'Yes', 'yes', 'YES']:
        sys.stdout.write("manual execution PASS\n")
        return True
    else:
        sys.stdout.write("manual execution FAIL\n")
        return False
