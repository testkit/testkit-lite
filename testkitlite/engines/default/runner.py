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
#              Wang, Jing <jing.j.wang@intel.com>
#              Tian, Xu <xux.tian@intel.com>
#              Wei, Zhang <wei.z.zhang@intel.com>
#              Zhang, Huihui <huihuix.zhang@intel.com>
#
# Description:
#   test engine
#

import os
from datetime import datetime
from shutil import copyfile
from textreport import TestResultsTextReport
import xml.etree.ElementTree as etree
import ConfigParser
from xml.dom import minidom
from testkitlite.common.str2 import *
from testkitlite.common.autoexec import shell_exec

_j = os.path.join
_d = os.path.dirname
_b = os.path.basename
_e = os.path.exists
_abs = os.path.abspath

###############################################################################
class TRunner:

    textreport = TestResultsTextReport()
    """
    Parse the testdefinition.xml files.
    Apply filter for each run.
    Conduct tests execution.
    """
    def __init__(self):
        # dryrun
        self.bdryrun = False
        # result file
        self.resultfile = None
        # external test    
        self.external_test = None
        # filter rules
        self.filter_rules = None
        self.fullscreen = False

    def set_dryrun(self, bdryrun):
        self.bdryrun = bdryrun

    def set_resultfile(self, resultfile):
        self.resultfile = resultfile

    def set_external_test(self, exttest):
        self.external_test = exttest

    def add_filter_rules(self, **kargs):
        """
        kargs:  key:values - "":["",]
        """
        self.filter_rules = kargs

    def set_fullscreen(self, state):
        self.fullscreen = state

    def run(self, testxmlfile, resultdir=None):
        """
        testxmlfile: target testxml file
        execdir and resultdir: should be the absolute path since TRunner
        is the common lib
        """
        # resultdir is set to current directory by default
        if not resultdir:
            resultdir = os.getcwd()
            
        ok = True
        if ok:
            try:
                filename = testxmlfile
                filename = os.path.splitext(filename)[0]
                filename = "%s.result" % _b(filename)
                resultfile = "%s.xml" % filename
                resultfile = _j(resultdir, resultfile)
                textfile = "%s.txt" % filename 
                textfile = _j(resultdir, textfile)
                
                if not _e(resultdir):
                    os.mkdir(resultdir)
                    
                print "[ apply filter ]"
                try:
                    ep = etree.parse(testxmlfile)
                    rt = ep.getroot()
                    self.apply_filter(rt)
                    ep.write(resultfile)
                    if self.resultfile:
                        copyfile(resultfile, self.resultfile)
                except Exception, e:
                    print str(e)
                    return False
 
                print "[ xml %s ]" % _abs(resultfile)
                print "[ testing now ]"
                if self.external_test: 
                    self.execute_external_test(resultfile, resultfile)
                else:
                    self.execute(resultfile, resultfile)
                
                if _e(resultfile):
                   # report the result using xml mode
                    print "[ generate the result(XML): %s ]" % resultfile
                    # add XSL support to testkit-lite
                    first_line = os.popen("head -n 1 %s" % resultfile).readlines()
                    first_line = '<?xml-stylesheet type="text/xsl" href="./resultstyle.xsl"?>' + first_line[0]
                    os.system("sed -i '1c " + first_line + "' " + resultfile)
                    os.system("cp /opt/testkit/lite/xsd/tests.css " + resultdir)
                    os.system("cp /opt/testkit/lite/xsd/resultstyle.xsl " + resultdir)
                    
                    print "[ generate the result(TXT): %s ]" % textfile
                    print self.textreport.report(resultfile)
                    open(textfile, "w+").write(self.textreport.report(resultfile))
                    if self.resultfile:
                        copyfile(resultfile, self.resultfile)
                        copyfile(textfile, self.resultfile + '.txt')
 
            except Exception, e:
                print e
                ok &= False

        return ok

    def pretty_print(self, ep, resultfile):
        rawstr = etree.tostring(ep.getroot(), 'utf-8')
        t = minidom.parseString(rawstr)
        open(resultfile, 'w+').write(t.toprettyxml(indent="  "))

    def execute_external_test(self, testxmlfile, resultfile):
        """Run external test"""
        import subprocess, thread
        from  pyhttpd import startup
        if self.bdryrun:
            print "external test not support dryrun"
            return True
        #start http server in here
        try:
            parameters = {} 
            parameters.setdefault("testsuite", testxmlfile)
            parameters.setdefault("resultfile", resultfile)
            if self.fullscreen:
                parameters.setdefault("hidestatus", "1")
            else:
                parameters.setdefault("hidestatus", "0")
            thread.start_new_thread(startup, (), {"parameters":parameters})
            
            # timeout is 2 hours
            shell_exec(self.external_test, 36000, True)
            print "[ start test environment by executed (%s) ]" % self.external_test

        except Exception, e:
            print e
        return True

    def apply_filter(self, rt):
        def case_check(tc):
            rules = self.filter_rules
            for key in rules.iterkeys():
                if key in ["suite", "set"]:
                    continue
                #Check attribute
                t_val = tc.get(key)
                if t_val:
                    if not t_val in rules[key]:
                        return False
                else:
                    #Check sub-element
                    items = tc.getiterator(key)
                    if items: 
                        t_val = []
                        for i in items:
                            t_val.append(i.text)
                        if len(set(rules[key]) & set(t_val)) == 0:
                            return False
            return True

        suiteparent = rt.find('test_definition')
        if not suiteparent:
            suiteparent = rt
            
        rules = self.filter_rules
        for tsuite in rt.getiterator('suite'):
            if rules.get('suite'):
                if tsuite.get('name') not in rules['suite']:
                    suiteparent.remove(tsuite)
            for tset in tsuite.getiterator('set'):
                if rules.get('set'):
                    if tset.get('name') not in rules['set']:
                        tsuite.remove(tset)
                       
        for tset in rt.getiterator('set'):
            for tc in tset.getiterator('testcase'):
                if not case_check(tc):
                    tset.remove(tc)
 
    def execute(self, testxmlfile, resultfile):
        def exec_testcase(case):
            ok = True
            rt_code, stdout, stderr = None, None, None

            """ Handle manual test """
            if case.get('execution_type', '') == 'manual':
                try:
                    for attr in case.attrib:
                        print "    %s: %s" % (attr, case.get(attr))
                    notes = case.find("description/notes")
                    print "    notes: %s" % notes.text
                    descs = case.getiterator("step_desc")
                    for desc in descs:
                        print "    desc: %s" % desc.text
                except:
                    pass
                return ok

            testentry_elm = case.find('description/test_script_entry')
            expected_result = testentry_elm.get('test_script_expected_result', '0')
            # Construct result info node
            resinfo_elm = etree.Element('result_info')
            res_elm = etree.Element('actual_result')
            start_elm = etree.Element('start')
            end_elm = etree.Element('end')
            stdout_elm = etree.Element('stdout')
            stderr_elm = etree.Element('stderr')
            resinfo_elm.append(res_elm)
            resinfo_elm.append(start_elm)
            resinfo_elm.append(end_elm)
            resinfo_elm.append(stdout_elm)
            resinfo_elm.append(stderr_elm)
            
            case.append(resinfo_elm)

            start_elm.text = datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
            if self.bdryrun:
                return_code, stderr, stdout = "0", "Dryrun error info", "Dryrun output"
            else:
                return_code, stderr, stdout = \
                    shell_exec(testentry_elm.text, str2number(testentry_elm.get('timeout')), True)

            # convert all return code to string in order to compare test result
            if return_code is None:
                res_elm.text = 'None'
            else:
                res_elm.text = str(return_code)
            stdout_elm.text = stdout
            stderr_elm.text = stderr

            # record endtime
            end_elm.text = datetime.today().strftime("%Y-%m-%d_%H_%M_S")

            if expected_result != res_elm.text:
                case.set('result', 'FAIL')
            else:
                case.set('result', 'PASS')

            # Check performance test
            measures = case.getiterator('measurement')
            for m in measures:
                ind = m.get('name')
                fname = m.get('file')
                if fname and _e(fname):
                    try:
                        config = ConfigParser.ConfigParser()
                        config.read(fname)
                        val = config.get(ind, 'value')
                        m.set('value', val)
                    except Exception, e:
                        print e
                    
            return ok

        # Go
        try:
            ep = etree.parse(testxmlfile)
            rt = ep.getroot()
            for tsuite in rt.getiterator('suite'):
                print "[Suite] execute suite: %s" % tsuite.get('name')
                for tset in tsuite.getiterator('set'):
                    print "[Set] execute set: %s" % tset.get('name')
                    for tc in tset.getiterator('testcase'):
                        print "[Case] execute case: %s" % tc.get("id")
                        exec_testcase(tc)
            ep.write(resultfile)
            return True
        except Exception, e:
            print e
            return False
