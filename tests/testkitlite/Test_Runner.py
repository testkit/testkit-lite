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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, 
# Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#              Yuanyuan,Zou  <yuanyuan.zou@borqs.com>

import sys
sys.path.append("../../")
from testkitlite.engines.default.runner import *
from commodule.connector import Connector
import unittest
import json
from optparse import OptionParser  

#test Class 
class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self.CONNECTOR = Connector({"testremote": "tizenMobile"}).get_connector()
        self.runner = TRunner(self.CONNECTOR)
        self.log_dir = os.path.join(os.path.expandvars('$HOME'),"testresult")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def tearDown(self):
        self.runner = None

    def test_set_pid_log(self):
        self.runner.set_pid_log('/home/test/autotest')
        self.assertEqual(self.runner.pid_log,'/home/test/autotest')

    def test_set_global_parameters(self):
        parser = OptionParser()
        parser.add_option("-D", "--dryrun",dest="bdryrun",action="store_true",help="Dry-run")
        parser.add_option("-o", "--output", dest="resultfile",
                                help=""),
        parser.add_option("-e", dest="exttest", action="store",
                                help="")
        parser.add_option("--fullscreen", dest="fullscreen", action="store_true",
                                help="Run web API test in full screen mode")
        parser.add_option("--non-active", dest="non_active", action="store_true",
                                help="")
        parser.add_option("--enable-memory-collection", dest="enable_memory_collection", action="store_true",
                                help="")
        parser.add_option("--deviceid",dest="device_serial", action="store",
                                help="set sdb device serial information" )
        parser.add_option("--stubname", dest="stubname",
                    action="store",
                    help="set stub name")

        args = ["-D", "yes","--output","/home/test/","-e","WRTLauncher cts-webapi-tizen-alarm-tests",
                "--fullscreen","none","--non-active","none","--enable-memory-collection","none",
                "--deviceid","123"]  
        (options, args) = parser.parse_args(args)  
        print options
        self.runner.set_global_parameters(options)
        self.assertEqual(self.runner.bdryrun,True)

    def test_set_session_id(self):
        self.runner.set_session_id('12345')
        self.assertEqual(self.runner.session_id,'12345')

    def test_add_filter_rules(self):
        wfilters = {}
        wfilters['execution_type'] = ["manual"]
        self.runner.add_filter_rules(**wfilters)  
          
    def test_prepare_run(self):
        wfilters = {}
        wfilters['execution_type'] = ["auto"]
        self.runner.add_filter_rules(**wfilters)
        a = self.runner.prepare_run('/usr/share/cts-webapi-tizen-alarm-tests/tests.xml',self.log_dir)
        print a
        self.assertEqual(a,True)

    def test_run_case(self):
        self.runner.exe_sequence = ['cts-webapi-tizen-alarm-tests.auto']
        self.runner.testsuite_dict = {'cts-webapi-tizen-alarm-tests.auto': ['/home/test/autotest/2013-03-11-14:17:08.864498/cts-webapi-tizen-alarm-tests.auto.xml']}
        self.runner.run_case(self.log_dir)

    def test_merge_resultfile(self):
        start_time = '2013-03-11-12:16:33.637293'#depend you start test time 
        self.runner.merge_resultfile(start_time, self.log_dir)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(RunnerTestCase("test_set_global_parameters"))
    return suite

#run test
if __name__ == "__main__":
    #unittest.main(defaultTest = 'suite')
    unittest.main()


