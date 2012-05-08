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
#   test engine
#

import os
import sys
from datetime import datetime
from shutil import copyfile

from testkitlite.engines.meego.testparser import TestDefinitionParser
from testkitlite.engines.meego.xmlreport import TestResultsXMLReport
from testkitlite.engines.meego.textreport import TestResultsTextReport
from testkitlite.engines.meego.testfilter import TestDefinitionFilter
from testkitlite.engines.meego.unit import *

from testkitlite.common.validate import validate_xml
from testkitlite.common.autoexec import shell_exec
from testkitlite.common.manexec import manual_exec, QA


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

    TEST_SCHEMA_FILE   = "/opt/testkit/lite/xsd/testdefinition-syntax.xsd"
    RESULT_SCHEMA_FILE = "/opt/testkit/lite/xsd/testdefinition-results.xsd"

    parser     = TestDefinitionParser()
    xmlreport  = TestResultsXMLReport()
    textreport = TestResultsTextReport()

    def __init__(self):

        # prepare td filter
        self.tdfilter   = TestDefinitionFilter()
        # selected environment, fill to the TestResults/Set unit before report
        self.env    = None

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
        self.bcompatibleresultxml = bcompatibleresultxml

    def set_full_resultxml(self, bfullresultxml):
        self.bfullresultxml = bfullresultxml

    def set_validateonly(self, bvalidateonly):
        self.bvalidateonly = bvalidateonly


    # /* filter operations fallback to tdfilter

    FILTERS = TestDefinitionFilter.FILTERS

    def add_black_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        if kargs.get("environment") is not None:
            raise ValueError("environment is not allowed in black filter")
        self.tdfilter.add_black_rules(**kargs)


    def add_white_rules(self, **kargs):
        """ kargs:  key:values - "":["",]
        """
        if kargs.get("environment") is not None:
            if len(kargs["environment"]) == 1:
                self.env = kargs["environment"][0]
            else:
                raise ValueError("ONE environment value allowed only")
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
        print "[ validate the test xml: %s ]" % testxmlfile
        ok = validate_xml(self.TEST_SCHEMA_FILE, testxmlfile)

        if self.bvalidateonly:
            return ok

        if ok:

            try:
                # parse the xmlfile
                print "[ parse the test xml: %s ]" % testxmlfile
                td = self.parser.parse(testxmlfile)
                ok &= (td is not None)

                # apply filter
                print "[ apply filters ]"
                ok &= self.tdfilter.apply_filter(td)

                testresultxmlfile = os.path.basename(testxmlfile)
                fname = os.path.splitext(testresultxmlfile)[0]
                testresultxmlfile = "%s.result%s"%(fname,".xml")
                testresulttextfile = "%s.result%s"%(fname,".txt")
                testresultxmlfile = os.sep.join([resultdir,testresultxmlfile])
                testresulttextfile = os.sep.join([resultdir,testresulttextfile])

                # conduct execution
                print "[ testing now ]"
                cwd = os.getcwd()
                os.chdir(execdir)
                if not self.bdryrun:
                    ok &= self.execute(td, resultdir)
                else:
                    print "Dryrun ..."
                os.chdir(cwd)

                # get testresults
                tr = TestResults(td)

                # other operations
                # 1) fill environment in TestResults unit
                tr.environment = self.env

                # prepare report
                if not os.path.exists(resultdir):
                    os.mkdir(resultdir)

                # report the result to xml
                print "[ generate the result(XML): %s ]" % testresultxmlfile
                if self.bcompatibleresultxml:
                    self.xmlreport.set_report_mode("testrunner compatible")
                else:
                    self.xmlreport.set_report_mode("TRunner")
                self.xmlreport.set_report_nacases(self.bfullresultxml)
                outfile = file(testresultxmlfile, "w")
                print >> outfile, self.xmlreport.report(tr)
                outfile.close()

                # validate the resultfile
                print "[ validate result(XML): %s ]" % testresultxmlfile
                ok &= validate_xml(self.RESULT_SCHEMA_FILE, testresultxmlfile)

                # report the result using text mode
                print "[ generate the result(TEXT): %s ]" % testresulttextfile
                outfile = file(testresulttextfile, "w")
                print self.textreport.report(tr)
                print >> outfile, self.textreport.report(tr)
                outfile.close()

                # Make another copy to user specified result file
                if self.resultfile:
                    print "resultfile=%s" % self.resultfile
                    copyfile(testresultxmlfile, self.resultfile)

                if self.reporter_name:
                    reporter = self.get_reporter(self.reporter_name)()
                    reporter.report_test(testresultxmlfile,{})


            except Exception, e:
                print e
                ok &= False

        return ok


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
        def exec_step(step, timeout, presteps_ok, manual):
            """ exec_step will do the actual execution work, handle some
                failure, such as timeout/pre_steps_failed, fill the key
                data (failureinfo, starttime, endtime, returncode ...)
                of step structure except the "result" section
            """
            """ presteps_ok:
                None:  Don't care about presteps_ok
                True:  presteps are PASS
                False: presteps are FAIL
            """
            ok = True

            # record starttime
            step.start = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

            # judge pre_steps
            if False == presteps_ok:
                step.return_code,step.stdout,step.stderr = \
                    (None, "", "pre_steps failed")
                step.failure_info = "pre_steps failed"
                ok &= False
            else:
                # run step
                # 1) manual steps
                if manual:
                    ok &= manual_exec(step.command)
                # 2) auto steps
                else:
                    step.return_code,step.stdout,step.stderr = \
                        shell_exec(step.command, timeout, True)
                    # judge timeout
                    if step.return_code is None:
                        step.failure_info = "timeout"
                        ok &= False

                    """
                        presteps/poststeps will ignore "return_code" if "expected_result"
                        is None, while case steps would always compare "expected_result"
                        even the expected_result is None (use default value)
                    """
                    # compare with the expected_result when:
                    # it's case step or
                    # it's pre/post steps and expected_result is specified
                    if  presteps_ok is not None or \
                       (presteps_ok is None and step.expected_result is not None):
                        if step.return_code != step.get("expected_result"):
                            ok &= False

                    if (presteps_ok is None and step.expected_result is None):
                        step.stdout +=\
                            "expected_result is not specified, so ignore result"

            # record endtime
            step.end = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

            return ok


        def exec_steps(steps, timeout, presteps_ok, manual):
            ok = True
            for i in xrange(len(steps)):
                print "    [Step] execute step (%d/%d): %s" %(i+1, len(steps), steps[i].command)
                ok &= exec_step(steps[i], timeout, presteps_ok, manual)
                # one step fail will lead to steps exit
                if False == ok:
                    return ok

            return ok


        @fillresult
        def exec_case(case, presteps_ok):
            # deal with manual tests which has description element
            #(XXX it's the requirement of tests.xml exported from testlink,
            # all the test steps are in "description"
            if case.description and case.composedgenattri.get("manual"):
                print ("check the description:\n" + case.description)
            # deal with each steps
            ok = exec_steps(case.steps,
                            case.composedgenattri.get("timeout"),
                            presteps_ok,
                            case.composedgenattri.get("manual"))
            # deal with comment in manual exectuion
            if False == ok and case.composedgenattri.get("manual"):
                case.comment = QA("Please enter comments:")

            return ok


        @fillresult
        def exec_set(set):

            ok = None

            # fill environment in Set unit
            set.environment = self.env

            # execute pre_steps
            print "   [PreSteps] execute pre steps of set *%s*" \
                   % set.composedgenattri.get("name")
            presteps_ok =\
                exec_steps(set.presteps,
                           set.composedgenattri.get("timeout"),
                           None,
                           False) # pre_steps are always automated

            # execute cases
            for case in set.cases:
                if case.runit:
                    print "   [Cases] execute case *%s* " \
                           % case.composedgenattri.get("name")
                    exec_ok = exec_case(case, presteps_ok)
                    if not case.composedgenattri.get("insignificant"):
                        if None != ok:
                            if None != exec_ok:
                                ok &= exec_ok
                        else:
                            ok = exec_ok
                    if case.getfiles:
                        for f in case.getfiles:
                            f = f.strip(' \n\t')
                            f = f.replace('\n', '')
                            print "    [GetFile] store file %s to %s" % (f, resultdir)
                            shell_exec("cp %s %s -rf" %(f, resultdir), boutput=True)


            # deal with get files
            print "   [GetFiles] get needed files of set *%s*" \
                   % set.composedgenattri.get("name")
            if set.getfiles:
                for f in set.getfiles:
                    f = f.strip(' \n\t')
                    f = f.replace('\n', '')
                    print "    [GetFile] store file %s to %s" % (f, resultdir)
                    shell_exec("cp %s %s -rf" %(f, resultdir), boutput=True)

            # execute post_steps
            print "   [PostSteps] execute post steps of set *%s*" \
                   % set.composedgenattri.get("name")
            exec_steps(set.poststeps,
                       set.composedgenattri.get("timeout"),
                       None,
                       False) # post_steps are always automated

            # write each case's log
            try:
                cursuitelogdir = os.sep.join([resultdir, set.psuite.genattri.name])
                cursetlogdir = os.sep.join([resultdir, set.psuite.genattri.name, set.genattri.name])
                if not os.path.exists(cursuitelogdir):
                    os.mkdir(cursuitelogdir)
                if not os.path.exists(cursetlogdir):
                    os.mkdir(cursetlogdir)
                for case in set.cases:
                    for i in xrange(len(case.steps)):
                        caselogpath = os.path.join(cursetlogdir, case.genattri.name)
                        caselogfile = file(caselogpath, "w")
                        print >> caselogfile, "[stdout]:"
                        print >> caselogfile, case.steps[i].stdout
                        print >> caselogfile, "[stderr]:"
                        print >> caselogfile, case.steps[i].stderr
                        caselogfile.close()
            except Exception, e:
                print e

            return ok


        @fillresult
        def exec_suite(suite):

            ok = None
            for set in suite.sets:
                if set.runit:
                    print "  [Set] execute set *%s*" \
                           % set.composedgenattri.get("name")
                    exec_ok = exec_set(set)
                    if not set.composedgenattri.get("insignificant"):
                        if None != ok:
                            if None != exec_ok:
                                ok &= exec_ok
                        else:
                            ok = exec_ok
            return ok


        @fillresult
        def exec_testdefinition(td):
            ok = None
            for suite in td.suites:
                if suite.runit:
                    print " [Suite] execute suite *%s*" \
                           % suite.composedgenattri.get("name")
                    exec_ok = exec_suite(suite)
                    if not suite.composedgenattri.get("insignificant"):
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

