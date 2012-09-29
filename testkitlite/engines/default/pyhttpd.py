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
#              Xu, Tian <xux.tian@intel.com>
#              Wang, Jing <jing.j.wang@intel.com>
#              Zhang, Huihui <huihuix.zhang@intel.com>
#
# Description:
#   various data unit for testing
#

import os
import re
import time
import cgi
import ctypes
import platform
from testkitlite.common.str2 import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

CurSuite = ""
CurSet = ""

class MyHandler(BaseHTTPRequestHandler):
    """Only handle POST request """

    #set default value of parameters in response content
    Query = {"hidestatus":"0", "resultfile":"/tmp/tests-result.xml"}
    def do_RESPONSE(self):
        """Response get parameters request"""

        if self.Query.has_key("hidestatus"):
            print "[ parameter hidestatus: %s ]" % self.Query["hidestatus"]
        if self.Query.has_key("pid_log"):
            print "[ parameter pid_log: %s ]" % self.Query["pid_log"]
        if self.Query.has_key("testsuite"):
            print "[ parameter testsuite: %s ]" % self.Query["testsuite"]
        if self.Query.has_key("resultfile"):
            print "[ parameter resultfile: %s ]" % self.Query["resultfile"]
        
        xml = "<parameters>"
        if self.Query.has_key("hidestatus"):
            xml += "<hidestatus>%s</hidestatus>" % self.Query["hidestatus"]
        xml += "</parameters>"
        #Send response data out
        self.send_response(200)
        self.send_header("Content-type", "xml")
        self.send_header("Content-Length", str(len(xml)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(xml)
        return None

    def response_Testsuite(self):
        """Read testsuite xml, and response it to client"""

        if self.Query.has_key("testsuite"):
            try:
                testsuitexml = ""
                with open(self.Query["testsuite"], "r") as fd:
                    testsuitexml = fd.read()
                testsuitexml = str2str(testsuitexml)
                self.send_response(200)
                self.send_header("Content-type", "xml")
                self.send_header("Content-Length", str(len(testsuitexml)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(testsuitexml)
            except Exception, e:
                print "[ reading test suite %s failed, error: %s ]" % (self.Query["testsuite"], e)
        else:
            print "[ testsuite parameter not found ]"
        return None

    def do_POST(self):
        """Handle POST request"""

        try:
            query = {}
            ctype, pdict = cgi.parse_header(self.headers.getheader("content-type"))
            if ctype == "application/x-www-form-urlencoded":
                length = int(self.headers.getheader("content-length"))
                query = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            elif ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            #Save result xml
            if self.path.strip() == "/save_result":
                filename = self.Query["resultfile"]
                filecontent = None
                if query.has_key("filecontent"):
                    filecontent = (query.get("filecontent"))[0]
                    filecontent = str2str(filecontent)
                resultfile = self.save_RESULT(filecontent, filename)
                print "[ save result xml to %s ]" % resultfile
                
                #kill open windows
                #if process is not existed, just continue
                time.sleep(5)
                with open(self.Query["pid_log"], "r") as fd:
                    main_pid = 1
                    for line in fd.readlines():
                        if main_pid:
                            main_pid = 0
                        else:
                            pid = line.rstrip("\n")
                            if pid:
                                try:
                                    if platform.system() == "Linux":
                                        os.kill(int(pid), 9)
                                        print "[ kill execution process, pid: %s ]" % pid
                                    else:
                                        kernel32 = ctypes.windll.kernel32
                                        handle = kernel32.OpenProcess(1, 0, int(pid))
                                        kill_result = kernel32.TerminateProcess(handle, 0)
                                        print "[ kill execution process, pid: %s ]" % pid
                                except Exception, e:
                                    pattern = re.compile('No such process')
                                    match = pattern.search(str(e))
                                    if not match:
                                        print "[ fail to kill execution process, pid: %s, error: %s ]" % (int(pid), e)
                
                #send response
                if resultfile is not None:
                    self.send_response(200)
                else:
                    self.send_response(100)
                    
            if self.path.strip() == "/test_hint":
                try:
                    tcase = ""
                    tsuite = ""
                    tset = ""
                    global CurSuite
                    global CurSet
                    if query.has_key("suite"):
                        tsuite = (query.get("suite"))[0]
                        if not tsuite == CurSuite:
                            CurSuite = tsuite
                            CurSet = ""
                            print "[Suite] execute suite: %s" % tsuite
                    if query.has_key("set"):
                        tset = (query.get("set"))[0]
                        if not tset == CurSet:
                            CurSet = tset
                            print "[Set] execute set: %s" % tset
                    if query.has_key("testcase"):
                        tcase = (query.get("testcase"))[0]
                        print "[Case] execute case: %s" % tcase
                except Exception, e:
                    print "[ fail to print test hint, error: %s ]" % e
                #send response
                self.send_response(200)
                self.send_header("foo", "bar")
                self.end_headers()
            return None
        except Exception, e:
            print "[ fail to handle post request, error: %s ]" % e

    def do_GET(self):
        """ Handle GET type request """
        if self.path.strip() == "/get_testsuite":
            # response test suite xml
            self.response_Testsuite()
        elif self.path.strip() == "/get_params":
            self.do_RESPONSE()
        return None

    def save_RESULT(self, filecontent, filename):
        """Save result xml to local disk"""

        if filecontent is not None:
            try:
                with open(filename, "w") as fd:
                    fd.write(filecontent)
                return filename
            except Exception, e:
                print "[ fail to save result xml %s, error: %s ]" % (filename, e)
        return None

def startup(parameters):
    try:
        MyHandler.Query.update(parameters)
        server = HTTPServer(("127.0.0.1", 8000), MyHandler)
        print "[ started http server at %s:%d ]" % ("127.0.0.1", 8000)
        server.serve_forever()
    except:
        pass
