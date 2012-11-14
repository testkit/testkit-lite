/*
 *Copyright (C) 2012, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU General Public License,
 * version 2, as published by the Free Software Foundation.
 * 
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * for more details.
 * 
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc., 59 Temple
 * Place - Suite 330, Boston, MA 02111-1307 USA.
 * 
 *  Authors:
 *         Tang, Shao-Feng <shaofeng.tang@intel.com>
 */

function init_test() {
	var session_id = Math.round(Math.random() * 10000);
	save_session_id(session_id);
	sync_session_id(session_id);
	start_test();
}

function save_session_id(session_id) {
	statusFrame = document.getElementById('statusframe');
	statusWin = statusFrame.contentWindow;
	sessionIdNode = statusWin.document.getElementById('session_id_div');
	if (null == sessionIdNode) {
		sessionIdNode = statusWin.document.createElement("div");
		sessionIdNode.id = "session_id_div";
		statusWin.document.body.appendChild(sessionIdNode);
		sessionIdNode.innerHTML = "Session ID: <div id=\"session_id\">"
				+ session_id + "</div><br/>";
	}
}

function sync_session_id(session_id) {
	var server_url = "http://127.0.0.1:8000/init_session_id";
	var task = null;
	server_url += "?session_id=" + session_id;

	jQuery.ajax({
		async : false,
		url : server_url,
		type : "GET",
		success : function(result) {
		}
	});
}

function get_session_id() {
	statusFrame = document.getElementById('statusframe');
	statusWin = statusFrame.contentWindow;
	sessionIdNode = statusWin.document.getElementById('session_id');
	return sessionIdNode.innerHTML;
}

function start_test() {
	var task = ask_test_task();
	if (1 == task) {
		// alert("Invalid session.");
		window.open('', '_self', '');
		window.close();
	} else if (task != null) {
		execute_test_task(task);
	} else {
		execute_manual_test();
	}
}

function ask_generate_xml() {
	jQuery.ajax({
		async : false,
		url : "http://127.0.0.1:8000/generate_xml",
		type : "GET",
		success : function(result) {
			// alert("XML is generated");
		}
	});
	setTimeout("window.open('','_self','');window.close()", 5000);
}

function extract_all_manual() {
	var server_url = "http://127.0.0.1:8000/manual_cases";
	var tasks = null;

	AJAX = createAjaxRequest();

	if (AJAX) {
		AJAX.open("GET", server_url, false);
		AJAX.send(null);
		var strReturn = AJAX.responseText;
		tasks = $.parseJSON(strReturn);

		if (0 == tasks.none) {
			tasks = null;
		}
	} else {
		alert("Fail to get the test task, this browser is't supported");
	}

	return tasks;
}

function createAjaxRequest() {
	AJAX = null;
	if (window.XMLHttpRequest) {
		AJAX = new XMLHttpRequest();
	} else {
		AJAX = new ActiveXObject("Microsoft.XMLHTTP");
	}
	return AJAX;
}

function ask_test_task() {
	var server_url = "http://127.0.0.1:8000/auto_test_task";
	var task = null;
	session_id = get_session_id();
	server_url += "?session_id=" + session_id;

	AJAX = createAjaxRequest();

	if (AJAX) {
		AJAX.open("GET", server_url, false);
		AJAX.send(null);
		var strReturn = AJAX.responseText;
		task = $.parseJSON(strReturn);
		if (0 == task.none) {
			return null;
		}
		if (1 == task.invalid) {
			return 1;
		}
	} else {
		alert("Fail to get the test task, this browser is't supported");
	}

	return task;
}

function init_status_frame() {
	statusFrame = document.getElementById('statusframe');
	statusWin = statusFrame.contentWindow;
	statusNode = statusWin.document.getElementById('status_div');
	if (null == statusNode) {
		statusNode = statusWin.document.createElement("div");
		statusNode.id = "status_div";
		statusWin.document.body.appendChild(statusNode);
	}
	return statusNode;
}

function execute_test_task(json_task) {
	oTestFrame = document.getElementById('testframe');
	statusNode = init_status_frame();

	statusNode.innerHTML = "Test Purpose: <div id=\"purpose_div\">"
			+ json_task.purpose + "</div><br/>Entry: " + json_task.entry;
	oTestFrame.src = json_task.entry;
	if (oTestFrame.attachEvent) {
		oTestFrame.attachEvent("onload", function() {
			extract_case_result();
		});
	} else {
		oTestFrame.onload = function() {
			extract_case_result();
		};
	}
}

function extract_case_result() {
	oTestFrame = document.getElementById('testframe');
	var oTestWin = oTestFrame.contentWindow;
	var oTestDoc = oTestFrame.contentWindow.document;
	var result = "BLOCK";
	var case_msg = "";

	oPass = $(oTestDoc).find(".pass");
	oFail = $(oTestDoc).find(".fail");
	case_uri = oTestFrame.src.toString();

	total_num = getTestPageParam(case_uri, "total_num");
	locator_key = getTestPageParam(case_uri, "locator_key");
	value = getTestPageParam(case_uri, "value");

	if (total_num != "" && locator_key != "" && value != "") {
		if (locator_key == "id") {
			var results;
			var passes;
			var fails;

			var oRes = $(oTestDoc).find("table#results");
			if (oRes) {
				results = $(oRes).find('tr');
				passes = $(oRes).find('tr.pass');
				fails = $(oRes).find('tr.fail');
			}
			if (passes.length + fails.length == total_num) {
				var i = 1;
				for (i = 1; i <= total_num; i++) {
					if (i.toString() != value) {
						continue;
					}
					var rest = results[i].childNodes[0].innerText;
					var desc = results[i].childNodes[1].innerText;
					case_msg = results[i].childNodes[2].innerText;

					if (rest && rest.toUpperCase() == "PASS") {
						result = "PASS";
					} else {
						result = "FAIL";
					}
					break;
				}
			} else {
				var i;
				for (i = 0; i < fails.length; i++) {
					var desccell = fails[i].childNodes[1];
					if (desccell) {
						case_msg += "###Test Start###" + desccell.innerText
								+ "###Test End###";
					}
					var msgcell = fails[i].childNodes[2];
					if (msgcell) {
						case_msg += "###Error1 Start###" + msgcell.innerText
								+ "###Error1 End###";
					}
				}
				result = "FAIL";
			}
		}
	} else if (oPass.length > 0 && oFail.length == 0) {
		if (oTestWin.resultdiv) {
			case_msg = oTestWin.resultdiv.innerHTML;
		}
		result = "PASS";
	} else if (oFail.length > 0) {
		var oRes = $($(oTestDoc).find("table#results")).get(0);
		// Get error log
		if (oRes) {
			var fails = $(oRes).find('tr.fail');
			var i;
			for (i = 0; i < fails.length; i++) {
				var desccell = fails[i].childNodes[1];
				if (desccell) {
					case_msg += "###Test Start###" + desccell.innerText
							+ "###Test End###";
				}
				var msgcell = fails[i].childNodes[2];
				if (msgcell) {
					case_msg += "###Error2 Start###" + msgcell.innerText
							+ "###Error2 End###";
				}
			}
		}
		result = "FAIL";
	}

	commit_test_result(result, case_msg);
	start_test();
}

var manual_test_step = function() {
	this.order = 0;
	this.desc = "";
	this.expected = "";
};

var manual_cases = function() {
	this.casesid = "";
	this.index = 0;
	this.result = "";
	this.entry = "";
	this.pre_con = "";
	this.post_con = "";
	this.purpose = "";
	this.steps = new Array();
};

function execute_manual_test() {
	manualcaseslist = new Array();
	tasks = extract_all_manual();
	for ( var i = 0; i < tasks.length; i++) {
		// alert("task["+i+"]:\n" + "Entry:" + tasks[i].entry +"\nPurpose:" +
		// tasks[i].purpose+"\nExpected Result:" + tasks[i].expected);
		parent.document.getElementById("statusframe").height = 385 + "px";
		manualcaseslist[i] = new manual_cases();
		manualcaseslist[i].casesid = tasks[i].case_id;
		manualcaseslist[i].index = i;
		manualcaseslist[i].entry = tasks[i].entry;
		manualcaseslist[i].pre_con = tasks[i].pre_condition;
		manualcaseslist[i].post_con = tasks[i].post_condition;
		manualcaseslist[i].purpose = tasks[i].purpose;

		if (tasks[i].steps != undefined) {
			for ( var j = 0; j < tasks[i].steps.length; j++) {
				this_manual_step = new manual_test_step();
				this_manual_step.order = parseInt(tasks[i].steps[j].order);
				this_manual_step.desc = tasks[i].steps[j].step_desc;
				this_manual_step.expected = tasks[i].steps[j].expected;
				manualcaseslist[i].steps[this_manual_step.order - 1] = this_manual_step;
			}
		}
	}

	if (tasks.length > 0) {
		winCloseTimeout = 50000;
		statusFrame.src = "./manual_harness.html";
		$($($('#main')).get(0)).attr('rows', "100,*");
	} else {
		// No manual cases, generate the result.
		ask_generate_xml();
	}
	oTestFrame = document.getElementById('testframe');
	oTestFrame.src = '';
}

function getTestPageParam(uri, param) {
	var uri_local = uri;
	var iLen = param.length;
	var iStart = uri_local.indexOf(param);
	if (iStart == -1)
		return "";
	iStart += iLen + 1;
	var iEnd = uri_local.indexOf("&", iStart);
	if (iEnd == -1)
		return uri_local.substring(iStart);

	return uri_local.substring(iStart, iEnd);
}

function commit_test_result(result, msg) {
	statusFrame = document.getElementById('statusframe');
	purposeNode = statusWin.document.getElementById('purpose_div');
	session_id = get_session_id();
	var purpose_str = purposeNode.innerHTML

	var server_url = "http://127.0.0.1:8000/commit_result";
	jQuery.ajax({
		async : false,
		url : server_url,
		type : "POST",
		data : {
			"purpose" : purpose_str,
			"result" : result,
			"msg" : "[Message]" + msg,
			"session_id" : session_id
		},
		dataType : "json",
		beforeSend : function(x) {
			if (x && x.overrideMimeType) {
				x.overrideMimeType("application/j-son;charset=UTF-8");
			}
		},
		success : function(result) {
		}
	});
}
