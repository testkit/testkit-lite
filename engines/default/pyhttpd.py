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
#
# Description:
#   various data unit for testing
#


import os
import cgi
from testkitlite.common.str2 import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class MyHandler(BaseHTTPRequestHandler):
    """Only handle POST request """

    #set default value of parameters in response content
    Query = {"hidestatus":"0","resultfile":"/tmp/tests-result.xml"}

    def do_RESPONSE(self,**kwargs):
        """Response get parameters request"""

        xml = "<parameters>"
        for key,val in kwargs.items():
            xml += "<%s>%s</%s>"%(key,val,key)
        xml += "</parameters>"

        #Send response data out
        self.send_response(200)
        self.send_header("Content-type","xml")
        self.send_header("Content-Length",str(len(xml)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(xml)
        return None

    def response_Testsuite(self):
        """Read testsuite xml, and respone it to client"""

        if self.Query.has_key("testsuite"):
            try:
                testsuitexml = ""
                with open(self.Query["testsuite"],"r") as fd:
                    testsuitexml = fd.read()
                testsuitexml = str2str(testsuitexml)
                self.send_response(200)
                self.send_header("Content-type", "xml")
                self.send_header("Content-Length", str(len(testsuitexml)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(testsuitexml)
            except Exception, e:
                print "reading test suite fail..."
                print e
        else:
            print "test-suite file not found..."

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
                query=cgi.parse_multipart(self.rfile, pdict)
            #Save result xml
            filename = self.Query["resultfile"]
            filecontent = None
            if query.has_key("filecontent"):
                filecontent = (query.get("filecontent"))[0]
                filecontent = str2str(filecontent)
            resultfile = self.save_RESULT(filecontent,filename)
            print "[ save result xml to %s ]"%resultfile
            #send response
            if resultfile is not None:
                self.send_response(200)
            else:
                self.send_response(100)
            return None
        except Exception,e:
            #print e
            pass

    def do_GET(self):
        """ Handle GET type request """

        if self.path.strip() == "/get_testsuite":
           # response test suite xml
           self.response_Testsuite()
        else:
           data = self.Query.copy()
           self.do_RESPONSE(**data)
        return None

    def save_RESULT(self,filecontent,filename):
        """Save result xml to local disk"""

        if filecontent is not None:
           try:
              with open(filename,"w") as fd:
                 fd.write(filecontent)
              return filename
           except IOError,e:
                print "fail to save result xml ..."
                print e
        return None

def startup(parameters):
    try:
        MyHandler.Query.update(parameters)
        server = HTTPServer(("127.0.0.1", 8000), MyHandler)
        print "[ started http server at %s:%d ]"%("127.0.0.1",8000)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
