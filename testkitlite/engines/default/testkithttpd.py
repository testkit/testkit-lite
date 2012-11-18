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
#              Tang, Shao-Feng <shaofeng.tang@intel.com>

import os
import time
import threading
from datetime import datetime
import cgi
import json
from urlparse import urlparse, parse_qs
from xml.etree import ElementTree
from testkitlite.common.str2 import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from testkitlite.common.autoexec import shell_exec
from testkitlite.common.killall import killall
import subprocess
import signal
import urllib2

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class TestStep:
    def __init__(self, step_desc, expected, order):
        self.step_desc = step_desc
        self.expected = expected
        self.order = order
    
    def to_json(self):
        return {"step_desc": self.step_desc, "expected": self.expected, "order": self.order}

class TestCase:
    """Test Case Model"""
    def __init__(self, case_node, dom, case_order):
        self.purpose = case_node.getAttribute("purpose")
        
        if case_node.getElementsByTagName("test_script_entry").item(0) is not None and case_node.getElementsByTagName("test_script_entry").item(0).childNodes.item(0) is not None:
            self.entry = case_node.getElementsByTagName("test_script_entry").item(0).childNodes.item(0).data
            self.e_result = case_node.getElementsByTagName("test_script_entry").item(0).getAttribute("test_script_expected_result")
        else:
            self.entry = ""
            self.e_result = ""
        self.result = ""
        self.msg = ""
        self.xml_node = case_node
        self.dom_root = dom
        self.start_at = datetime.now()
        self.end_at = None
        self.is_executed = False
        self.time_task = None
        self.order = case_order
        self.case_id = case_node.getAttribute("id")
        if case_node.getElementsByTagName("pre_condition").item(0) is not None and case_node.getElementsByTagName("pre_condition").item(0).childNodes.item(0) is not None:
            self.pre_con = case_node.getElementsByTagName("pre_condition").item(0).childNodes.item(0).data
        else:
            self.pre_con = "" 
        if case_node.getElementsByTagName("post_condition").item(0) is not None and case_node.getElementsByTagName("post_condition").item(0).childNodes.item(0) is not None:
            self.post_con = case_node.getElementsByTagName("post_condition").item(0).childNodes.item(0).data
        else:
            self.post_con = ""
        self.steps = []
        if case_node.getElementsByTagName("step") is not None:
            for this_step in case_node.getElementsByTagName("step"):
                desc = ""
                expected = ""
                order = this_step.getAttribute("order")
                if this_step.getElementsByTagName("step_desc").item(0) is not None:
                    desc = this_step.getElementsByTagName("step_desc").item(0).childNodes.item(0).data
                if this_step.getElementsByTagName("expected") is not None:
                    expected = this_step.getElementsByTagName("expected").item(0).childNodes.item(0).data
                test_step = TestStep(desc, expected, order)
                self.steps.append(test_step.to_json())
                
        if case_node.getAttribute("execution_type") is None:
            self.e_type = "auto"
        else:
            self.e_type = case_node.getAttribute("execution_type")
            
        if case_node.getElementsByTagName("test_script_entry").item(0).getAttribute("timeout") is None:
            self.timeout = 90
        elif case_node.getElementsByTagName("test_script_entry").item(0).getAttribute("timeout"):
            self.timeout = int(case_node.getElementsByTagName("test_script_entry").item(0).getAttribute("timeout"))
        else:
            self.timeout = 90
    
    def to_string(self):
        objstr = "[Case] execute case:\nTestCase: %s\nTestEntry: %s\nExpected Result: %s\nExecution Type: %s" % (self.purpose, self.entry, self.e_result, self.e_type)
        return objstr
    
    def is_manual(self):
        return self.e_type != "auto"
    
    def to_json(self):
        return {"purpose": self.purpose, "entry": self.entry, "expected": self.e_result, "case_id": self.case_id, "pre_condition": self.pre_con, "post_condition": self.post_con, "steps": self.steps, "order": self.order}
    
    def set_result(self, test_result, test_msg):
        self.is_executed = True
        self.cancel_time_check()
        self.result = test_result
        self.msg = test_msg
        self.xml_node.setAttribute("result", test_result)
        result_info = self.dom_root.createElement("result_info")
        
        for childNode in self.xml_node.childNodes:
            import xml.dom.minidom
            if childNode.nodeType is xml.dom.Node.ELEMENT_NODE and childNode.tagName is "result_info":
                self.xml_node.removeChild(childNode)
                
        self.xml_node.appendChild(result_info)
        actual_result = self.dom_root.createElement("actual_result")
        actual_result.appendChild(self.dom_root.createTextNode(test_result))
        result_info.appendChild(actual_result)
        start = self.dom_root.createElement("start")
        end = self.dom_root.createElement("end")
        start.appendChild(self.dom_root.createTextNode(str(self.start_at)))
        end.appendChild(self.dom_root.createTextNode(str(datetime.now())))
        
        result_info.appendChild(start)
        result_info.appendChild(end)
        
        stdout = self.dom_root.createElement("stdout")
        stdout.appendChild(self.dom_root.createTextNode(self.msg))
        result_info.appendChild(stdout)
    
    def set_start_at(self, start_at):
        self.start_at = start_at
        if self.timeout > 0:
           self.time_task = threading.Timer(self.timeout, checkResult, (self,))
           self.time_task.start()
    
    def toXmlNode(self):
        return self.xml_node.toprettyxml(indent="  ")
    
    def cancel_time_check(self):
        if self.time_task is not None:
            self.time_task.cancel()

def checkResult(case):
    if not case.is_executed:
        print "----------------------Time is out----------------The case \"%s\" is timeout. Set the result \"BLOCK\", and start a new browser" % case.purpose
        case.set_result("BLOCK", "Time is out")
        print "[ kill existing client, pid: %s ]" % TestkitWebAPIServer.client_process.pid
        try:
            TestkitWebAPIServer.client_process.terminate()
        except:
            killall(TestkitWebAPIServer.client_process.pid)
        print "[ start new client in 10sec ]"
        time.sleep(10)
        client_command = TestkitWebAPIServer.default_params["client_command"]
        start_client(client_command)
    else:
        print "---------------------The case \"%s\" is executed in time, and result is %s." % (case.purpose, case.result)

class TestkitWebAPIServer(BaseHTTPRequestHandler):
    default_params = {"hidestatus":"0", "resultfile":"/tmp/tests-result.xml"}
    auto_test_cases = {}
    manual_test_cases = {}
    iter_params = {}
    auto_case_id_array = []
    auto_index_key = "auto_index"
    xml_dom_root = None
    this_server = None
    running_session_id = None
    client_process = None
    
    def read_test_definition(self):
        if self.default_params.has_key("testsuite"):
            try:
                from xml.dom.minidom import parse
                TestkitWebAPIServer.xml_dom_root = parse(self.default_params["testsuite"])
                self.xml_dom_root = TestkitWebAPIServer.xml_dom_root
                self.iter_params.update({self.auto_index_key: 0})
                index = 1
                for node in self.xml_dom_root.getElementsByTagName('testcase'):
                    tc = TestCase(node, self.xml_dom_root, index)
                    index = index + 1
                    if tc.is_manual():
                        self.manual_test_cases[tc.purpose] = tc
                    else:
                        self.auto_test_cases[tc.purpose] = tc
                        if tc.purpose in self.auto_case_id_array:
                            print "================================The purpose '%s' is already in the list==========================" % tc.purpose
                        else:
                            self.auto_case_id_array.append(tc.purpose)
            except Exception, e:
                print "reading test suite fail when loading test cases..."
                print e
        else:
            print "test-suite file not found..."
        print "Auto: %d\nManual: %d" % (len(self.auto_test_cases), len(self.manual_test_cases))
    
    def save_RESULT(self, filecontent, filename):
        """Save result xml to local disk"""
        if filecontent is not None:
            try:
                with open(filename, "w") as fd:
                    fd.write(filecontent)
                return filename
            except IOError, e:
                print "fail to save result xml ..."
                print e
        return None
    
    def generate_result_xml(self):
        result_xml = TestkitWebAPIServer.xml_dom_root.toprettyxml(indent="  ")
        for key, value in self.auto_test_cases.iteritems():
            value.cancel_time_check()
        self.save_RESULT(result_xml, self.default_params["resultfile"])
        self.send_response(200)
        self.send_header("Content-type", "xml")
        self.send_header("Content-Length", str(len(result_xml)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(result_xml)
        TestkitWebAPIServer.this_server.socket.close()
    
    def definition_xml(self):
        try:
            testsuitexml = ""
            with open(self.default_params["testsuite"], "r") as fd:
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
    
    def auto_test_task(self):
       parsed_path = urlparse(self.path)
       parsed_query = parse_qs(parsed_path.query)
       print "SessionID:%s in auto_test_task(), On server side, the ID is %s\n" % (parsed_query['session_id'][0], TestkitWebAPIServer.running_session_id)
       session_id = parsed_query['session_id'][0]
       if TestkitWebAPIServer.running_session_id == session_id:
           if self.iter_params[self.auto_index_key] < len(self.auto_test_cases):
               case_index = self.iter_params[self.auto_index_key]
               key = self.auto_case_id_array[case_index]
               self.iter_params.update({self.auto_index_key: (case_index + 1)})
               task = self.auto_test_cases[key]
               current = datetime.now()
               task.set_start_at(current)
               print task.to_string()
               self.send_response(200)
               self.send_header("Content-type", "application/json")
               self.end_headers()
               self.wfile.write(json.dumps(task.to_json()))
           else:
               print "No auto case is available any more"
               self.send_response(200)
               self.send_header("Content-type", "application/json")
               self.end_headers()
               self.wfile.write(json.dumps({"none": 0}))
       else:
           print "Invalid session"
           self.send_response(200)
           self.send_header("Content-type", "application/json")
           self.end_headers()
           self.wfile.write(json.dumps({"invalid": 1}))
    
    def manual_test_task(self):
       #load all manual test cases
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.end_headers()
       dictlist = []
       for key, value in self.manual_test_cases.iteritems():
          dictlist.append(value.to_json())
       self.wfile.write(json.dumps(dictlist))
    
    def commit_result(self):
       parsed_path = urlparse(self.path)
       parsed_query = parse_qs(parsed_path.query)
       
       form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
            }
        )
       
       key = None
       result = None
       msg = None
       session_id = None
       for field in form.keys():
            if "purpose" == field :
               key = form[field].value
            elif "result" == field:
               result = form[field].value
            elif "msg" == field:
               msg = form[field].value
               msg = msg[len("[Message]"):]
            elif "session_id" == field:
               session_id = form[field].value
       print "SessionID:%s in commit_result(), On server side, the ID is %s" % (session_id, TestkitWebAPIServer.running_session_id)
       if key is not None:
           from xml.sax.saxutils import unescape
           key = unescape(urllib2.unquote(key.decode("utf-8")))
       print "\t[Key]: %s" % key
       if TestkitWebAPIServer.running_session_id == session_id:
           tested_task = self.auto_test_cases[key]
           tested_task.set_result(result, msg)
           
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.end_headers()
       self.wfile.write(json.dumps({"OK": 1}))
    
    def commit_manual_result(self):
       parsed_path = urlparse(self.path)
       parsed_query = parse_qs(parsed_path.query)
       
       form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
            }
        )
       
       key = None
       result = None
       for field in form.keys():
            if "purpose" == field :
               key = form[field].value
            elif "result" == field:
               result = form[field].value
       if key is not None:
           from xml.sax.saxutils import unescape
           key = unescape(urllib2.unquote(key.decode("utf-8")))
           tested_task = self.manual_test_cases[key]
           tested_task.set_result(result, "")
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.end_headers()
       self.wfile.write(json.dumps({"OK": 1}))
    
    def init_session_id(self):
       parsed_path = urlparse(self.path)
       parsed_query = parse_qs(parsed_path.query)
       print "SessionID: %s" % parsed_query['session_id'][0]
       TestkitWebAPIServer.running_session_id = parsed_query['session_id'][0]
    
    def do_POST(self):
        """ POST request """
        if len(self.auto_test_cases) == 0 and len (self.manual_test_cases) == 0:
            self.read_test_definition()
        if self.path.strip().startswith("/auto_test_task"):
            self.auto_test_task()
        elif self.path.strip().startswith("/init_session_id"):
            self.init_session_id()
        elif self.path.strip().startswith("/manual_cases"):
            self.manual_test_task()
        elif self.path.strip().startswith("/commit_result"):
            self.commit_result()
        elif self.path.strip().startswith("/commit_manual_result"):
            self.commit_manual_result()
        elif self.path.strip() == "/generate_xml":
            self.generate_result_xml()
        elif self.path.strip() == "/check_server":
            print "---------------------------------------Checking server, the server is running.--------------------------------------------------------"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"OK": 1}))
        return None
    
    def do_GET(self):
        """ Get request """
        self.do_POST()

def start_client(command):
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        TestkitWebAPIServer.client_process = proc
        print "[ start client with pid: %s ]" % proc.pid
    except Exception, e:
        print "Exception occurs while invoking \"%s\"" % command
        sys.exit(-1)

def startup(parameters):
    try:
        TestkitWebAPIServer.default_params.update(parameters)
        # update default value when start it again
        TestkitWebAPIServer.auto_test_cases = {}
        TestkitWebAPIServer.manual_test_cases = {}
        TestkitWebAPIServer.iter_params = {}
        TestkitWebAPIServer.auto_case_id_array = []
        TestkitWebAPIServer.auto_index_key = "auto_index"
        TestkitWebAPIServer.xml_dom_root = None
        TestkitWebAPIServer.this_server = None
        TestkitWebAPIServer.running_session_id = None
        TestkitWebAPIServer.client_process = None
        
        server = HTTPServer(("127.0.0.1", 8000), TestkitWebAPIServer)
        TestkitWebAPIServer.this_server = server
        print "[ started http server at %s:%d ]" % ("127.0.0.1", 8000)
        hidestatus = TestkitWebAPIServer.default_params["hidestatus"]
        pid_log = TestkitWebAPIServer.default_params["pid_log"]
        testsuite = TestkitWebAPIServer.default_params["client_command"]
        resultfile = TestkitWebAPIServer.default_params["resultfile"]
        client_command = TestkitWebAPIServer.default_params["client_command"]
        print "[ parameter hidestatus: %s ]" % hidestatus
        print "[ parameter pid_log: %s ]" % pid_log
        print "[ parameter testsuite: %s ]" % testsuite
        print "[ parameter resultfile: %s ]" % resultfile
        print "[ parameter client_command: %s ]" % client_command
        # start widget and http server
        start_client(client_command)
        server.serve_forever()
    except KeyboardInterrupt:
        print "\n[ existing http server on user cancel ]\n"
        server.socket.close()
    except:
        pass
