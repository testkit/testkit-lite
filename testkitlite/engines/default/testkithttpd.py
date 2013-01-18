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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#              Zhang, Huihui <huihuix.zhang@intel.com>
#              Wendong,Sui  <weidongx.sun@intel.com>

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
from testkitlite.common.killall import killall
import subprocess
import signal
import urllib2
import re
import platform
import gc

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
    def __init__(self, case_node, case_order, xml_name, package_name):
        self.purpose = case_node.get("purpose")
       
        script_node = case_node.find("./description/test_script_entry")
        if script_node is not None:
            self.entry = script_node.text
            self.e_result = script_node.get("test_script_expected_result")
            if self.e_result is None:
                self.e_result = ""
        else:
            self.entry = ""
            self.e_result = ""
        self.result = ""
        self.msg = ""
        self.xml_node = case_node
        self.start_at = datetime.now()
        self.end_at = None
        self.is_executed = False
        self.time_task = None
        self.order = case_order
        self.case_id = case_node.get("id")
        self.xml_name = xml_name
        self.package_name = package_name
        
        pre_con_node  = case_node.find("./description/pre_condition")
        post_con_node = case_node.find("./description/post_condition")

        self.pre_con = ""
        self.post_con = ""
        if pre_con_node is not None:
            self.pre_con = pre_con_node.text
        if self.pre_con is None:
            self.pre_con = ""

        if post_con_node is not None:
            self.post_con = post_con_node.text
        if self.post_con is None:
            self.post_con = ""

        self.steps = []

        step_nodes = case_node.findall("./description/steps/step")
        for step_node in step_nodes:
            order = step_node.get("order")
            desc = ""
            expected = ""
            if step_node.find("./step_desc") is not None:
                desc = step_node.find("./step_desc").text
            if step_node.find("./expected") is not None:
                expected = step_node.find("./expected").text
            test_step = TestStep(desc, expected, order)
            self.steps.append(test_step.to_json())

        if case_node.get("execution_type") is None:
            self.e_type = "auto"
        else:
            self.e_type = case_node.get("execution_type")
        
        if (script_node is None) or (script_node.get("timeout") is None):
            self.timeout = 90
        else:
            self.timeout = int(script_node.get("timeout"))
    
    def print_info_string(self):
        try:
            print "\n[case] execute case:\nTestCase: %s\nTestEntry: %s" % (self.purpose, self.entry)
        except Exception, e:
            print "\n[case] execute case:\nTestCase: %s\nTestEntry: %s" % (str2str(self.purpose), str2str(self.entry))
            print "[ Error: found unprintable character in case purpose, error: %s ]\n" % e
    
    def is_manual(self):
        return self.e_type != "auto"
    
    def to_json(self):
        return {"purpose": self.purpose, "entry": self.entry, "expected": self.e_result, "case_id": self.case_id, "pre_condition": self.pre_con, "post_condition": self.post_con, "steps": self.steps, "order": self.order}
    
    def get_xml_name(self):
        return self.xml_name
    
    def set_result(self, test_result, test_msg):
        self.is_executed = True
        self.cancel_time_check()
        self.result = test_result
        self.msg = test_msg
        self.xml_node.set("result", test_result)
        if self.xml_node.find("./result_info") is not None:
            self.xml_node.remove(self.xml_node.find("./result_info"))

        result_info = ElementTree.SubElement(self.xml_node, "result_info")
        actual_result = ElementTree.SubElement(result_info, "actual_result")
        actual_result.text = str(test_result)
        
        start  = ElementTree.SubElement(result_info, "start")
        end    = ElementTree.SubElement(result_info, "end")
        stdout = ElementTree.SubElement(result_info, "stdout") 

        start.text  = str(self.start_at)
        end.text    = str(datetime.now())
        stdout.text = self.msg 
        
    def set_start_at(self, start_at):
        self.start_at = start_at
        if self.timeout > 0:
           self.time_task = threading.Timer(self.timeout, checkResult, (self,))
           self.time_task.start()
    
    def toXmlNode(self):
        return self.xml_node
    
    def cancel_time_check(self):
        if self.time_task is not None:
            self.time_task.cancel()

def checkResult(case):
    if not case.is_executed:
        try:
            print "[ Warning: time is out, test case \"%s\" is timeout, set the result to \"BLOCK\", and restart the client ]" % case.purpose
        except Exception, e:
            print "[ Warning: time is out, test case \"%s\" is timeout, set the result to \"BLOCK\", and restart the client ]" % str2str(case.purpose)
            print "[ Error: found unprintable character in case purpose, error: %s ]\n" % e
        case.set_result("BLOCK", "Time is out")
        TestkitWebAPIServer.start_auto_test = 0
        print "[ kill existing client, pid: %s ]" % TestkitWebAPIServer.client_process.pid
        try:
            TestkitWebAPIServer.client_process.terminate()
        except:
            killall(TestkitWebAPIServer.client_process.pid)
        killAllWidget()
        print "[ start new client in 5sec ]"
        time.sleep(5)
        TestkitWebAPIServer.start_auto_test = 1
        client_command = TestkitWebAPIServer.default_params["client_command"]
        start_client(client_command)
    else:
        try:
            print "[ test case \"%s\" is executed in time, and the result is %s ]" % (case.purpose, case.result)
        except Exception, e:
            print "[ test case \"%s\" is executed in time, and the result is %s ]" % (str2str(case.purpose), str2str(case.result))
            print "[ Error: found unprintable character in case purpose, error: %s ]\n" % e

def killAllWidget():
    OS = platform.system()
    if OS == "Linux":
        # release memory in the cache
        fi_c, fo_c, fe_c = os.popen3("echo 3 > /proc/sys/vm/drop_caches")
        # kill widget
        fi, fo, fe = os.popen3("wrt-launcher -l")
        for line in fo.readlines():
            package_id = "none"
            pattern = re.compile('\s+([a-zA-Z0-9]*?)\s*$')
            match = pattern.search(line)
            if match:
                package_id = match.group(1)
            if package_id != "none":
                pid_cmd = "ps aux | grep %s | sed -n '1,1p'" % package_id
                fi_pid, fo_pid, fe_pid = os.popen3(pid_cmd)
                for line_pid in fo_pid.readlines():
                    pattern_pid = re.compile('app\s*(\d+)\s*')
                    match_pid = pattern_pid.search(line_pid)
                    if match_pid:
                        widget_pid = match_pid.group(1)
                        print "[ kill existing widget, pid: %s ]" % widget_pid
                        killall(widget_pid)

class TestkitWebAPIServer(BaseHTTPRequestHandler):
    default_params = {"hidestatus":"0"}
    auto_test_cases = {}
    manual_test_cases = {}
    iter_params = {}
    auto_case_id_array = []
    auto_index_key = "auto_index"
    xml_dom_root = None
    this_server = None
    running_session_id = None
    client_process = None
    current_test_xml = "none"
    last_test_result = "none"
    start_auto_test = 1
    neet_restart_client = 0
    is_finished = False
  
    def clean_up_server(self):
        TestkitWebAPIServer.auto_test_cases.clear()
        TestkitWebAPIServer.manual_test_cases.clear()
        TestkitWebAPIServer.iter_params.clear()
        del TestkitWebAPIServer.auto_case_id_array[:]
        TestkitWebAPIServer.xml_dom_root = None
        TestkitWebAPIServer.running_session_id = None
        TestkitWebAPIServer.start_auto_test = 1 
        TestkitWebAPIServer.is_finished = False
        collected = gc.collect()
        print "[ Garbage collector: collected %d objects. ]" % (collected)
    
    def read_test_definition(self):
        if TestkitWebAPIServer.default_params.has_key("testsuite"):
            try:
              suites_dict = TestkitWebAPIServer.default_params["testsuite"]
              exe_sequence = TestkitWebAPIServer.default_params["exe_sequence"]
              index = 1
              for package_name in exe_sequence:
                  suites_array = suites_dict[package_name]
                  for xml_name in suites_array:
                      single_xml_tree = ElementTree.parse(xml_name)
                      print "[XML name : %s] ------------------------------------------------------------------------------------------------------------" % xml_name
                      tmp_xml_root = single_xml_tree.getroot()
                      for tmp_suite in tmp_xml_root.findall('suite'):
                          for tmp_set in tmp_suite.findall('set'):
                              for node in tmp_set.findall('testcase'):
                                  tc = TestCase(node, index, xml_name, package_name)
                                  index = index + 1
                                  if tc.is_manual():
                                      TestkitWebAPIServer.manual_test_cases[tc.purpose] = tc
                                  else:
                                      TestkitWebAPIServer.auto_test_cases[tc.purpose] = tc
                                      if tc.purpose in TestkitWebAPIServer.auto_case_id_array:
                                          try:
                                              print "[ Warning: the purpose '%s' is already in the list ]" % tc.purpose
                                          except Exception, e:
                                              print "[ Warning: the purpose '%s' is already in the list ]" % str2str(tc.purpose)
                                              print "[ Error: found unprintable character in case purpose, error: %s ]\n" % e
                                      else:
                                          TestkitWebAPIServer.auto_case_id_array.append(tc.purpose)

                      if TestkitWebAPIServer.xml_dom_root is None:
                          TestkitWebAPIServer.xml_dom_root = tmp_xml_root
                      else:
                          for suite_node in tmp_xml_root.findall('suite'):
                              definition_node = TestkitWebAPIServer.xml_dom_root
                              if definition_node is None:
                                  definition_node = ElementTree.Element("test_definition")
                              definition_node.append(suite_node)
              TestkitWebAPIServer.xml_dom_root = TestkitWebAPIServer.xml_dom_root
              TestkitWebAPIServer.iter_params.update({TestkitWebAPIServer.auto_index_key: 0})
            except Exception, e:
              print "[ Error: reading test suite fail when loading test cases, error: %s ]\n" % e
        else:
            print "[ Error: test-suite file is not found in the parameter ]\n"
        print "[ auto case number: %d, manual case number: %d ]" % (len(TestkitWebAPIServer.auto_test_cases), len(TestkitWebAPIServer.manual_test_cases))
        collected = gc.collect()
        print "[ Garbage collector: collected %d objects. ]" % (collected)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"OK": 1}))
    
    def save_RESULT(self, filecontent, filename):
        """Save result xml to local disk"""
        if filecontent is not None:
            try:
                with open(filename, "w") as fd:
                    fd.write(filecontent)
                return filename
            except IOError, e:
                print "[ Error: fail to save result xml, error: %s ]\n" % e
        return None
    
    def generate_result_xml(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"OK": 1}))
        # kill all client process to release memory
        print "\n[ kill existing client, pid: %s ]" % TestkitWebAPIServer.client_process.pid
        try:
            TestkitWebAPIServer.client_process.terminate()
        except:
            killall(TestkitWebAPIServer.client_process.pid)
        killAllWidget()
        print "[ wait 5sec to release memory]"
        time.sleep(5)
        # write result to file
        result_xml = ElementTree.tostring(TestkitWebAPIServer.xml_dom_root, "utf-8")
        for key, value in self.auto_test_cases.iteritems():
            value.cancel_time_check()
        self.save_RESULT(result_xml, TestkitWebAPIServer.default_params["resultfile"])
        print "[ set finished flag True ]"
        TestkitWebAPIServer.is_finished = True
        # close server
        #TestkitWebAPIServer.this_server.socket.close()

    def shut_down_server(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"OK": 1}))
        
        # close server
        try:
            TestkitWebAPIServer.this_server.socket.close()
        except Exception, e:
            print "[ Error: fail to close webapi http server, error: %s ]" % e
    
    def auto_test_task(self):
        if TestkitWebAPIServer.start_auto_test:
           parsed_path = urlparse(self.path)
           parsed_query = parse_qs(parsed_path.query)
           session_id = parsed_query['session_id'][0]
           if TestkitWebAPIServer.running_session_id == session_id:
               if self.iter_params[self.auto_index_key] < len(self.auto_test_cases):
                   case_index = self.iter_params[self.auto_index_key]
                   key = self.auto_case_id_array[case_index]
                   self.iter_params.update({self.auto_index_key: (case_index + 1)})
                   task = self.auto_test_cases[key]
                   current = datetime.now()
                   task.set_start_at(current)
                   if TestkitWebAPIServer.current_test_xml != task.get_xml_name():
                       TestkitWebAPIServer.current_test_xml = task.get_xml_name()
                       time.sleep(3)
                       #print "\n[ testing xml: %s ]" % task.get_xml_name()
                   task.print_info_string()
                   try:
                       self.send_response(200)
                       self.send_header("Content-type", "application/json")
                       self.send_header("Content-Length", str(len(json.dumps(task.to_json()))))
                       self.send_header("Access-Control-Allow-Origin", "*")
                       self.end_headers()
                       self.wfile.write(json.dumps(task.to_json()))
                   except Exception, e:
                       print "[ Error: lost connection to the client, a new client will be started when the current case is timeout ]"
               else:
                   print "\n[ no auto case is available any more ]"
                   self.send_response(200)
                   self.send_header("Content-type", "application/json")
                   self.send_header("Content-Length", str(len(json.dumps({"none": 0}))))
                   self.send_header("Access-Control-Allow-Origin", "*")
                   self.end_headers()
                   self.wfile.write(json.dumps({"none": 0}))
           else:
               print "[ sessionID: %s in auto_test_task(), on server side, the ID is %s ]" % (parsed_query['session_id'][0], TestkitWebAPIServer.running_session_id)
               print "[ Error: invalid session ID ]\n"
               self.send_response(200)
               self.send_header("Content-type", "application/json")
               self.send_header("Content-Length", str(len(json.dumps({"invalid": 0}))))
               self.send_header("Access-Control-Allow-Origin", "*")
               self.end_headers()
               self.wfile.write(json.dumps({"invalid": 0}))
        else:
            print "\n[ restart client process is activated, exit current client ]"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(json.dumps({"stop": 0}))))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"stop": 0}))
    
    def manual_test_task(self):
       # load all manual test cases
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       
       manual_test_xmls = set()
       dictlist = []
       for key, value in self.manual_test_cases.iteritems():
          dictlist.append(value.to_json())
          manual_test_xmls.add(value.get_xml_name())
       self.send_header("Content-Length", str(len(json.dumps(dictlist))))
       self.send_header("Access-Control-Allow-Origin", "*")
       self.end_headers()
       self.wfile.write(json.dumps(dictlist))
       for manual_test_xml in manual_test_xmls:
           TestkitWebAPIServer.current_test_xml = manual_test_xml
           time.sleep(3)
           #print "\n[ testing xml: %s ]\n" % manual_test_xml
    
    def check_execution_progress(self):
       print "Total: %s, Current: %s\nLast Case Result: %s" % (len(self.auto_test_cases), self.iter_params[self.auto_index_key], self.last_test_result)
       execution_progress = {"total": len(self.auto_test_cases), "current": self.iter_params[self.auto_index_key], "last_test_result": self.last_test_result}
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.send_header("Content-Length", str(len(json.dumps(execution_progress))))
       self.send_header("Access-Control-Allow-Origin", "*")
       self.end_headers()
       self.wfile.write(json.dumps(execution_progress))
       TestkitWebAPIServer.last_test_result = "BLOCK"
    
    def ask_next_step(self):
        next_is_stop = 0
        OS = platform.system()
        enable_memory_collection = TestkitWebAPIServer.default_params["enable_memory_collection"]
        if enable_memory_collection:
            if OS == "Linux":
                try:
                    fi, fo, fe = os.popen3("free -m | grep \"Mem\" | awk '{print $4}'")
                    free_memory = fo.readline()[0:-1]
                    free_memory_delta = int(free_memory) - 100
                    if free_memory_delta <= 0:
                        print "[ Warning: free memory now is %sM, need to release memory ]" % free_memory
                        # release memory in the cache
                        next_is_stop = 1
                        fi, fo, fe = os.popen3("echo 3 > /proc/sys/vm/drop_caches")
                except Exception, e:
                    print "[ Error: fail to check free memory, error: %s ]\n" % e
                    print "[ Error: free memory now is critical low, need to release memory immediately ]"
                    # release memory in the cache
                    next_is_stop = 1
                    fi, fo, fe = os.popen3("echo 3 > /proc/sys/vm/drop_caches")
            else:
                if self.iter_params[self.auto_index_key] % 200 == 0:
                    print "[ Warning: the client has run %s cases, need to release memory ]" % self.iter_params[self.auto_index_key]
                    next_is_stop = 1
        if next_is_stop:
            TestkitWebAPIServer.neet_restart_client = 1
            next_step = {"step": "stop"}
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(json.dumps(next_step))))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(next_step))
        else:
            next_step = {"step": "continue"}
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(json.dumps(next_step))))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(next_step))
    
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
       if key is not None:
           from xml.sax.saxutils import unescape
           key = unescape(urllib2.unquote(key.decode("utf-8")))
       if TestkitWebAPIServer.running_session_id == session_id:
           try:
               tested_task = self.auto_test_cases[key]
               tested_task.set_result(result, msg)
           except Exception, e:
               print "[ Error: can't find any test case by key: %s, error: %s ]\n" % (key, e)
           TestkitWebAPIServer.last_test_result = result
       if TestkitWebAPIServer.neet_restart_client:
           self.send_response(200)
           self.send_header("Content-type", "application/json")
           self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
           self.send_header("Access-Control-Allow-Origin", "*")
           self.end_headers()
           self.wfile.write(json.dumps({"OK": 1}))
           # kill client
           TestkitWebAPIServer.start_auto_test = 0
           print "\n[ kill existing client, pid: %s to release memory ]" % TestkitWebAPIServer.client_process.pid
           try:
               TestkitWebAPIServer.client_process.terminate()
           except:
               killall(TestkitWebAPIServer.client_process.pid)
           killAllWidget()
           print "[ start new client in 5sec ]"
           time.sleep(5)
           TestkitWebAPIServer.start_auto_test = 1
           TestkitWebAPIServer.neet_restart_client = 0
           client_command = TestkitWebAPIServer.default_params["client_command"]
           start_client(client_command)
       else:
           self.send_response(200)
           self.send_header("Content-type", "application/json")
           self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
           self.send_header("Access-Control-Allow-Origin", "*")
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
       self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
       self.send_header("Access-Control-Allow-Origin", "*")
       self.end_headers()
       self.wfile.write(json.dumps({"OK": 1}))
    
    def init_session_id(self):
       parsed_path = urlparse(self.path)
       parsed_query = parse_qs(parsed_path.query)
       print "[ sessionID: %s is gotten from the client ]" % parsed_query['session_id'][0]
       TestkitWebAPIServer.running_session_id = parsed_query['session_id'][0]
       
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
       self.send_header("Access-Control-Allow-Origin", "*")
       self.end_headers()
       self.wfile.write(json.dumps({"OK": 1}))
    
    def check_server_status(self):
       status = 0
       if TestkitWebAPIServer.is_finished:
           status = 1
       self.send_response(200)
       self.send_header("Content-type", "application/json")
       self.send_header("Content-Length", str(len(json.dumps({"finished": status}))))
       self.send_header("Access-Control-Allow-Origin", "*")
       self.end_headers()
       self.wfile.write(json.dumps({"finished": status}))

    def do_POST(self):
        """ POST request """
        if self.path.strip() == "/load_definitions":
            self.read_test_definition()
        if self.path.strip() == "/reload_definitions":
            self.clean_up_server()
            self.read_test_definition()
        if self.path.strip() == "/check_server_status":
            self.check_server_status()
        if self.path.strip() == "/shut_down_server":
            self.shut_down_server()
        if self.path.strip().startswith("/auto_test_task"):
            self.auto_test_task()
        elif self.path.strip().startswith("/check_execution_progress"):
            self.check_execution_progress()
        elif self.path.strip().startswith("/ask_next_step"):
            self.ask_next_step()
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
            print "[ checking server, and found the server is running ]"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(json.dumps({"OK": 1}))))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"OK": 1}))
        return None
    
    def do_GET(self):
        """ Get request """
        self.do_POST()

def start_client(command):
    try:
        pid_log = TestkitWebAPIServer.default_params["pid_log"]
        proc = subprocess.Popen(command, shell=True)
        if pid_log is not "no_log":
            try:
                with open(pid_log, "a") as fd:
                    pid = str(proc.pid)
                    fd.writelines(pid + '\n')
            except:
                pass
        TestkitWebAPIServer.client_process = proc
        print "[ start client with pid: %s ]\n" % proc.pid
    except Exception, e:
        print "[ Error: exception occurs while invoking \"%s\", error: %s ]\n" % (command, e)
        sys.exit(-1)

def send_http_request_to_case_server(url):
    import urllib, urllib2
    print "[ sending reading request to %s]" % url
    req = urllib2.Request(url, None)
    response = urllib2.urlopen(req)
    print response.geturl()
    print response.info()

def send_loading_definition_request(client_command):
    send_http_request_to_case_server("http://127.0.0.1:8000/load_definitions")
    print "[ client command %s ]" % client_command
    start_client(client_command)

def sub_task(client_command):
    time_task = threading.Timer(3, send_loading_definition_request, (client_command, ))
    time_task.start()

def reload_xml(t):
    xml_name = t[0]
    package_name = t[1]
    resultfile = t[2]
    print "[ reloading test case definitions with the XML %s ]" % xml_name 
    suites_dict = {}
    exe_sequence = [package_name]
    suite_array = [xml_name]
    suites_dict[package_name] = suite_array

    TestkitWebAPIServer.default_params["testsuite"] = suites_dict
    print "[]"
    TestkitWebAPIServer.default_params["exe_sequence"] = exe_sequence
    TestkitWebAPIServer.default_params["resultfile"] = resultfile
    
    client_command = TestkitWebAPIServer.default_params["client_command"]
    send_http_request_to_case_server("http://127.0.0.1:8000/reload_definitions")
    print "[ client command %s ]" % client_command
    start_client(client_command)

def shut_down_server():
    print "[ shutting down the server ]"
    send_http_request_to_case_server("http://127.0.0.1:8000/shut_down_server")

def check_server_running():
    print "[ checking if the server task is finished ]"
    import urllib, urllib2
    req = urllib2.Request("http://127.0.0.1:8000/check_server_status", None)
    response = urllib2.urlopen(req)
    html = response.read()
    status_json = json.loads(html)
    if status_json["finished"] == 1:
       print "[ The server finished tasks now]"
       return True
    else:
       print "[ not yet ]"
       return False

def start_server_up(server):
    try:
        server.serve_forever()
    except IOError:
        print "\n[ warnning, a IO error is raised, if the server is shutting down, please ignore it. ]"

def startup(parameters):
    try:
        TestkitWebAPIServer.default_params.update(parameters)
        # print server parameters for user to check
        server = HTTPServer(("127.0.0.1", 8000), TestkitWebAPIServer)
        TestkitWebAPIServer.this_server = server
        print "[ started http server at %s:%d ]" % ("127.0.0.1", 8000)
        hidestatus = TestkitWebAPIServer.default_params["hidestatus"]
        resultfile = TestkitWebAPIServer.default_params["resultfile"]
        pid_log = TestkitWebAPIServer.default_params["pid_log"]
        testsuite = TestkitWebAPIServer.default_params["testsuite"]
        exe_sequence = TestkitWebAPIServer.default_params["exe_sequence"]
        client_command = TestkitWebAPIServer.default_params["client_command"]
        enable_memory_collection = TestkitWebAPIServer.default_params["enable_memory_collection"]
        print "[ parameter hidestatus: %s ]" % hidestatus
        print "[ parameter resultfile: %s ]" % resultfile
        print "[ parameter pid_log: %s ]" % pid_log
        print "[ parameter testsuite ]"
        for key in testsuite:
            print "  [ package name: %s ]" % key
            print "  [ xml files: %s ]" % testsuite[key]
        print "[ parameter exe_sequence: %s ]" % exe_sequence
        print "[ parameter client_command: %s ]" % client_command
        print "[ parameter enable_memory_collection: %s ]" % enable_memory_collection
        # check read test definition done, before start client
        print "[ analysis testsuite, this might take some time, please wait ]"
        sub_task(client_command)
        time_task = threading.Timer(1, start_server_up, (server, ))
        time_task.start()

        # start client
        #start_client(client_command)
        #server.serve_forever()
    except KeyboardInterrupt:
        print "\n[ existing http server on user cancel ]\n"
        server.socket.close()
    except:
        pass
