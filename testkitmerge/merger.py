#!/usr/bin/python
#
# Copyright (C) 2014 Intel Corporation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Authors: 
#           Nicolas Zingile <n.zingile@gmail.com>

"""Merger module for testkit xml files"""

from lxml import etree
import os

#------------------------- Global variables -------------------------#

TESTDEFATTRS  = {}
TESTDEFCHILDS = {"environment" : False, "summary" : False, "suite" : False}
ENVATTRS      = {"build_id" : False, "device_id" : False, "device_model" : False,
		"device_name" : False, "host" : False, "lite_version" : False,
		"manufacturer" : False, "resolution" : False, "screen_size" : False}
ENVCHILDS     = {"other" : False}
SUMATTRS      = {"test_plan_name" : False}
SUMCHILDS     = {"start_at" : True, "end_at" : True}
SUITEATTRS    = {"name" : True, "launcher" : False}
SUITECHILDS   = {"set" : True}
SETATTRS      = {"name" : True, "set_debug_msg" : False}
SETCHILDS     = {"testcase" : False}
TCATTRS       = {"component" : True, "execution_type" : True, "id" : True,
		"name" : False, "priority" : True, "purpose" : True,
                "result" : True, "status" : True, "type" : True}
TCCHILDS      = {"description" : False, "categories" : False, "result_info" : False,
		    "categories" : False}
DESCATTRS     = {}
DESCCHILDS    = {"pre_condition" : False, "post_condition" : False, "steps" : False,
		"notes" : False, "test_script_entry" : True}
RESINFOATTRS  = {}
RESINFOCHILDS = {"actual_result" : True, "start" : True, "end" : True,
		"stdout" : False, "stderr" : False}

class ElementError(Exception):
    """Custom class to handle the merging exceptions"""
    pass

def check_element(element, attrdico, childsdico):
    """Checks a node of the testkit result xml tree.

    Allows to verify the integrity of a testkit result xml node.
    Check if element contains allowed attributes and if the value of
    those attributes is filled if it should be.
    Check if the child nodes of element are allowed and if so, checks
    if the child node contains text if it should.

    Args:
	element : Element to check
	attrdico: A dict that contains information on attributes of element
		keys: String - allowed attributes of the element
		values: Booleans indicating if the keys should be filled
	childsdico: A dict that contains information on sub elements of element
		keys: String - allowed sub elements of element
		values: Booleans indicating if the keys should contain text
    Returns:

    Raises:
	ElementError
    """
    for attrname, attrvalue in element.attrib.items():
        if attrname in attrdico.keys():
            if not attrvalue and attrdico.get(attrname):
                raise ElementError("Attribute '" + attrname + "' of element '" + element.tag
                + "' is not defined")
        else:
            raise ElementError("Attribute '" + attrname + "' is not authorized "
            + "as an attribute of the '" + element.tag + "' element")
    for child in list(element):
        if (child.tag not in childsdico.keys()):
            raise ElementError("Element '" + child.tag + " should not be a child element of '" + element.tag + "'")
	elif (not child.text and childsdico.get(child.tag)):
            raise ElementError("The element '" + child.tag + "' should contain some text")

def create_xmltree():
    """Creates an ElementTree object.
    Args:

    Return:
	An ElementTree object that represents en empty testkit result xml file.
    """
    root = etree.Element("test_definition")
    xmltree = etree.ElementTree(root)
    print "xml tree created !"
    
    return xmltree

def create_envandsum(srcxmltree, destxmltree):
    """Creates the environment and the summary nodes of
    an ElementTree object.

    Copy the environment and the summary nodes of srcxmltree in 
    the destxmltree. The destxmltree only contains the root element.

    Args:
	srcxmltree: Source xmltree from where we want to copy some nodes.
	destxmltree: Destination xmltree to augment with some nodes.

    Returns:
	An ElementTree that partially represents a testkit result xml file.
    """
    testdef = destxmltree.getroot()
    environment = srcxmltree.find("/environment")
    summary = srcxmltree.find("/summary")
    testdef.append(environment)
    testdef.append(summary)

    return destxmltree

def check_testdefinition(xmltree):
    """Checks the test_definition node of a testkit result xml.

    Checkis that all the sub elements of the test_definition node are present
    and that integrity of that sub elements is good.

    Args:
	xmltree: An ElementTree that represents a testkit result xml tree.

    Returns:

    Raises:
	ElementError
    """
    print "- checking test_definition node"
    testdef = xmltree.getroot()
    check_element(testdef, TESTDEFATTRS, TESTDEFCHILDS)
    environment = testdef.find("./environment")
    summary = testdef.find("summary")
    if environment is not None:
	print " -- checking environment node"
        check_element(environment, ENVATTRS, ENVCHILDS)
    else:
	raise ElementError("Element 'test_definition' should contain an 'environment' element")
    if summary is not None:
	print " -- checking summary node"
        check_element(summary, SUMATTRS, SUMCHILDS)
    else:
	raise ElementError("Element 'test_definition' should contain a 'summary' element")
    for asuite in testdef.findall("./suite"):
	print "- checking suite node : " + asuite.get("name") 
	check_suite(asuite)
	    
def check_suite(eltsuite):
    """Checks the integrity of a suite element.

    Args:
	eltsuite: A suite element to check

    Returns:
    """
    check_element(eltsuite, SUITEATTRS, SUITECHILDS) 
    for child in list(eltsuite):
	print "- checking set node : " + child.get("name")
	check_set(child)

def check_set(eltset):
    """Checks the integrity of a set element.

    Args:
	eltset: A set element to check.

    Returns:
    """
    check_element(eltset, SETATTRS, SETCHILDS)
    for child in list (eltset):
	print "- checking testcase node : " + child.get("id")
	check_testcase(child)

def check_testcase(eltcase):
    """Checks the integrity of a testcase element.

    Also verify that the result of the eltcase is present and consistent

    Args:
	eltcase: A testcase element to check

    Returns:

    Raises:
	ElementError
    """
    print "-- checking result"
    try:
	result = eltcase.get("result")
	actual_result = eltcase.find("./result_info/actual_result").text
	allowed_results = ["PASS", "FAIL", "N/A"]
    except AttributeError:
	raise ElementError("result of the testcase is not valid !")
    if result not in allowed_results or result != actual_result:
	raise ElementError("The testcase '" + eltcase.get("id") + "' doesn't have a consistent result")
    check_element(eltcase, TCATTRS, TCCHILDS)
    for child in list (eltcase):
	if child.tag == "description":
	    print "-- checking description node"
	    check_element(child, DESCATTRS, DESCCHILDS)
	elif child.tag == "result_info":
	    print "-- checking result_info node"
	    check_element(child, RESINFOATTRS, RESINFOCHILDS)
	elif child.tag == "categories":
	    pass
	else:
	    raise ElementError("Element '" + child.tag + "' is not allowed")

def solve_conflicts(sourcecase, destcase):
    """Selects a result when same testcase is encountered in both source and destination
    testkit xml files.

    The result is chosen according to the following priority : FAIL > N/A > PASS.

    Args:
	sourcecase: A testcase element of the source testkit xml result file
	destcase: A testcase element of the destination testkit xml result file

    Returns:
    """
    srcresult = sourcecase.get('result')
    destresult = destcase.get('result')
    if (srcresult == destresult) or (destresult == 'FAIL') \
    or (srcresult == 'PASS' and destresult == 'N/A'):
	pass
    else:
	destcase.set('result', srcresult)
	destcase.find('./result_info/actual_result').text = srcresult

def merge_testkitxml (sourcexmltree, destxmltree=None):
    """Merge two testkit xml result files.

    Merge the information of sourcexmltree in destxmltree. If destxmltree is
    not definded, creates a new ElementTree and copy all the information of
    sourcexmltree in it.

    Args:
	sourcexmltree: The source ElementTree object that represents the 
		testkit result xml source file
	destxmltree: The destination ElementTree object that represents the 
		testkit result xml destination file
    Returns:
	An ElementTree that represents the result of the merging of the sourcexmltree
	and destxmltree
    """
    print "## Checking source xml file ..."
    check_testdefinition(sourcexmltree)
    print "source xml file is correct. Ok\n"
    if destxmltree is None:
        print "Destination xml file doesn't exist... will be created"
        destxmltree = create_xmltree()
        create_envandsum(sourcexmltree, destxmltree)
    for asuite in sourcexmltree.iter('suite'):
        destsuite = destxmltree.find("/suite[@name='" + asuite.get('name') + "']")
        if destsuite is not None:
            for aset in asuite.iter('set'):
                destset = destsuite.find("./set[@name='" + aset.get('name') + "']")
                if destset is not None:
                    for acase in aset.iter('testcase'):
                        destcase = destset.find("./testcase[@id='" + acase.get('id') + "']")
                        if destcase is not None:
			    solve_conflicts(acase, destcase)
                        else:
                            destset.append(acase)
		else:
                    destsuite.append(aset)
        else:
            destxmltree.getroot().append(asuite)

    return destxmltree
