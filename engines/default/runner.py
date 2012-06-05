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
#              Tian, Xu <xux.tian@intel.com>
#              Wang, Jing <jing.j.wang@intel.com>
#              Wei, Zhang <wei.z.zhang@intel.com>
#
# Description:
#   test engine
#

import os

from datetime import datetime
from shutil import copyfile

from testkitlite.engines.default.testparser import TestDefinitionParser 
from testkitlite.engines.default.xmlreport import  TestResultsXMLReport
from testkitlite.engines.default.textreport import TestResultsTextReport
from testkitlite.engines.default.testfilter import TestDefinitionFilter 
#from testkitlite.common.validate import validate_xml
from testkitlite.common.autoexec import shell_exec
#from testkitlite.common.manexec import manual_exec, QA
from testkitlite.engines.default.unit import *


###############################################################################
class TRunner:

    """
    Validate several testdefinition.xml files as input.
    Parse the testdefinition.xml files.
    Apply filter for each run.
    Conduct tests execution.
    Report testdefinition-results.xml for each testdefinition.xml.
    Report testdefinition-results.text for each testdefinition.xml.
    """

    RESULT_SCHEMA_FILE = TEST_SCHEMA_FILE = "/opt/testkit/lite/xsd/test_definition.xsd"
    parser     = TestDefinitionParser()
    xmlreport  = TestResultsXMLReport()
    textreport = TestResultsTextReport()

    def __init__(self):

        # prepare td filter
        self.tdfilter   = TestDefinitionFilter()

        # dryrun
        self.bdryrun = False

        # nokia compatible result xml
        self.bcompatibleresultxml = False

        # print all cases include those result=="N/A"
        self.bfullresultxml = True

        # if validateonly
        self.bvalidateonly = False

        # result file
        self.resultfile = None

        # reporter
        self.reporter_name = None

        self.runtime = None

    def get_reporter(self, engine_name):
        from pkg_resources import iter_entry_points
        klass = None

        dist_plugins = {}
        for ep in iter_entry_points(group="oti.reporter_plugin", name=None):
            if not dist_plugins.has_key(ep.dist):
                dist_plugins[ep.dist] = {}
            dist_plugins[ep.dist][ep.name] = ep.load()
        for k, v in dist_plugins.items():
            if v['engine_name'] == engine_name:
                klass = v['reporter_klass']
                break
        if klass:
            print "Sucess to find reporter"
        else:
            raise NameError("can not find plugin for %s" % engine_name)
        return klass

    def set_dryrun(self, bdryrun):
        self.bdryrun = bdryrun

    def set_compatible_resultxml(self, bcompatibleresultxml):
        pass

    def set_full_resultxml(self, bfullresultxml):
        self.bfullresultxml = bfullresultxml

    def set_validateonly(self, bvalidateonly):
        self.bvalidateonly = bvalidateonly

    def set_runtime(self,runtime,**parameters):
        runtime += "?"
        for key,val in parameters.items():
            if isinstance(val,list):
               val = map(lambda x:"%s"%x, val)
               val = ",".join(val)
            runtime += "&%s=%s"%(key,val)
        self.runtime = runtime

    # /* filter operations fallback to tdfilter
    FILTERS = TestDefinitionFilter.FILTERS

    def add_black_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        self.tdfilter.add_black_rules(**kargs)


    def add_white_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        self.tdfilter.add_white_rules(**kargs)


    def clear_black_rules(self):
        self.tdfilter.clear_black_rules()


    def clear_white_rules(self):
        self.tdfilter.clear_white_rules()


    # filter operations fallback to tdfilter */


    def run(self,
            testxmlfile,
            execdir=None,
            resultdir=None):

        """
        testxmlfile: target testxml file
        execdir and resultdir: should be the absolute path since TRunner
        is the common lib
        """

        # execdir is set to xml directory by default
        if execdir is None:
            execdir = os.path.dirname(os.path.abspath(testxmlfile))
        # resultdir is set to execdir by default
        if resultdir is None:
            resultdir = execdir

        # validate the xmlfile
        #print "[ validate the test xml: %s ]" % testxmlfile
        #ok = validate_xml(self.TEST_SCHEMA_FILE, testxmlfile)

        #if self.bvalidateonly:
        #    return ok
        ok = True

        if ok:
            try:
                # parse the xmlfile
                print "[ parse the test xml: %s ]" % testxmlfile
                td = self.parser.parse(testxmlfile)
                ok &= (td is not None)

                # apply filter
                print "[ apply filters ]"
                ok &= self.tdfilter.apply_filter(td)
                if self.resultfile is not None:
                   filename = self.resultfile
                else:
                   filename = testxmlfile
                filename = os.path.splitext(filename)[0]
                filename = "%s.result"%os.path.basename(filename)
                testresultxmlfile  = "%s.xml"%filename
                testresulttextfile = "%s.txt"%filename
                testresultxmlfile  = os.sep.join([resultdir, testresultxmlfile])
                testresulttextfile = os.sep.join([resultdir, testresulttextfile])
                cwd = os.getcwd()
                os.chdir(execdir)

                if not self.bdryrun:
                    if not os.path.exists(resultdir):
                       os.mkdir(resultdir)
                    with open(testresultxmlfile,"w+") as fd:
                       pass
                    #dump testcase detials to result xml file
                    self.xmlreport.initTestXML(td, testresultxmlfile)
                    if self.resultfile is not None:
                       copyfile(testresultxmlfile, self.resultfile)
                    print "[ testing now ]"
                    if self.runtime is not None:
                       self.execute_externaltest(testxmlfile, testresultxmlfile)
                       td = self.parser.parse(testresultxmlfile)
                    else:
                       ok &= self.execute(td,resultdir)
                else:
                    print "[ Dryrun ... ]"
                os.chdir(cwd)

                # get testresults
                tr = TestResults(td)

                if self.resultfile is not None:
                    copyfile(testresultxmlfile, self.resultfile)
                    testresultxmlfile = self.resultfile

                # report the result using xml mode
                print "[ generate the result(XML): %s ]" % testresultxmlfile
                # report the result using text mode
                print "[ generate the result(TEXT): %s ]" % testresulttextfile
                outfile = file(testresulttextfile, "w")
                print self.textreport.report(tr)
                print >> outfile, self.textreport.report(tr)
                outfile.close()

                if self.reporter_name:
                    reporter = self.get_reporter(self.reporter_name)()
                    reporter.report_test(testresultxmlfile,{})

            except Exception, e:
                print e
                ok &= False

        return ok

    def execute_externaltest(self,testxmlfile,testresultxmlfile):
        """Run external test"""

        import subprocess,thread
        from  testkitlite.engines.default.pyhttpd import startup

        parameters = {}
        parameters.setdefault("testsuite", testxmlfile)
        parameters.setdefault("resultfile", testresultxmlfile)
        runtime,data = self.runtime.split("?")
        items = [item.split("=") for item in data.split("&") if "=" in item]
        for item in items:
            try:
                key = item[0]
                val = item[1]
            except IndexError:
                continue
            parameters[key] = val

        #start http server in here
        try:
            thread.start_new_thread(startup,(),{"parameters":parameters})
            proc = subprocess.Popen(args="%s"%runtime, shell=True)
            print "[ start test environment by executed (%s) ]"%runtime
            while True:
                exit_code = proc.poll()
                if exit_code is not None:
                   proc.kill()
                   break
        except:
            pass
        return None

    def execute(self, testdefinition, resultdir=os.getcwd()):

        def fillresult(func):
            def ret(c, *args):
                ok = func(c, *args)
                if None == ok:
                    c.result = "N/A"
                if True == ok:
                    c.result = "PASS"
                if False == ok:
                    c.result = "FAIL"
                return ok
            return ret


        @fillresult
        def exec_testcase(case):
            """ exec_step will do the actual execution work, handle some
                failure, such as timeout, fill the key
                data (failureinfo, starttime, endtime, returncode ...)
                of step structure except the "result" section
            """
            ok = True
            case.start = case.end = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            case.return_code,case.stdout,case.stderr = None,None,None

            if case.entry is None or case.manual:
                def print_manualtest(case):
                    """ print manual test info to console """
                   
                    attrs =  ["id", "category", "component", "priority", \
                              "purpose", "status", "type", "notes", "pre_condition",\
                              "post_condition", "requirement", "steps"]

                    indent = " "*4
                    try:
                        for i in xrange (len(attrs)):
                            if isinstance(case.get(attrs[i]) , list):
                               if attrs[i] == "steps":
                                  for step in case.steps:
                                      print "%s%s:"%(indent, "Expected".center(15,' '))
                                      print "%s%s"%(indent, step.expected)
                                      print "%s%s"%(indent, "_"*75)
                                      print "%s%s:"%(indent, "Step".center(15,' '))
                                      print "%s%s"%(indent, step.step_desc)
                                      print "%s%s\n"%(indent, "_"*75)
                               else:
                                  print "%s%s: %s"%(indent, (attrs[i].title()).center(15, ' '), ",".join(case.get(attrs[i])))
                            else: 
                               print "%s%s: %s"%(indent, (attrs[i].title()).center(15, ' '), case.get(attrs[i]))
                    except:
                          pass

                print_manualtest(case)
                return None

            # record starttime
            case.start = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            case.return_code,case.stdout,case.stderr = \
                shell_exec(case.entry, case.timeout, True)
            # convert all return code to string in oder to compare test result
            case.return_code = str(case.return_code)

            # judge timeout
            if case.return_code is None:
                case.failure_info = "timeout"
                ok &= False

            """
                presteps/poststeps will ignore "return_code" if "expected_result"
                is None, while case steps would always compare "expected_result"
                even the expected_result is None (use default value)
            """
            # compare with the expected_result when:
            # it's case step or
            # it's pre/post steps and expected_result is specified
            if case.expected_result is not None:
                if case.return_code != case.get("expected_result"):
                    ok &= False

            if (case.expected_result is None):
                case.stdout +=\
                    "expected_result is not specified, so ignore result"

            # record endtime
            case.end = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

            # begin to file xml reports
            if ok is not None:
               result = (ok and ["PASS"] or ["FAIL"])[0]
            else:
               result = "N/A"

            self.xmlreport.fillTestInfo(case,result)

            return ok

        @fillresult
        def exec_set(testset):

            ok = None
            for case in testset.testcases:
                if case.runit:
                    print "   [Cases] execute case *%s* " \
                           % case.get("id")
                    exec_ok = exec_testcase(case)
                    ok = exec_ok

            # write each case's log
            try:
                cursuitelogdir = os.sep.join([resultdir, testset.psuite.name])
                cursetlogdir = os.sep.join([resultdir, testset.psuite.name, testset.name])
                if not os.path.exists(cursuitelogdir):
                    os.mkdir(cursuitelogdir)
                if not os.path.exists(cursetlogdir):
                    os.mkdir(cursetlogdir)
                for case in testset.testcases:
                    caselogpath = os.path.join(cursetlogdir, case.id)
                    caselogfile = file(caselogpath, "w")
                    print >> caselogfile, "[stdout]:"
                    print >> caselogfile, case.stdout
                    print >> caselogfile, "[stderr]:"
                    print >> caselogfile, case.stderr
                    caselogfile.close()
            except Exception, e:
                print e

            return ok


        @fillresult
        def exec_suite(suite):

            ok = None
            for testset in suite.testsets:
                if testset.runit:
                    print "  [Set] execute set *%s*" \
                           % testset.get("name")
                    exec_ok = exec_set(testset)
                    if None != ok:
                        if None != exec_ok:
                            ok &= exec_ok
                    else:
                        ok = exec_ok
            return ok


        @fillresult
        def exec_testdefinition(testdefinition):

            ok = None
            for suite in testdefinition.testsuites:
                if suite.runit:
                    print "  [Suite] execute suite *%s*" \
                           % suite.get("name")
                    exec_ok = exec_suite(suite)
                    if None != ok:
                        if None != exec_ok:
                            ok &= exec_ok
                    else:
                        ok = exec_ok
            return ok

        # go
        try:
            if isinstance(testdefinition, TestDefinition):
                exec_testdefinition(testdefinition)
            return True
        except Exception, e:
            print e
            return False

