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
#   unittest for tree
#

import sys
sys.path.append("../")
from tree import *

###############################################################################
#                                    unittest                                 #
###############################################################################

import unittest
from autoexec import shell_exec
class TestTree(unittest.TestCase):

    def setUp(self):
        l=Tree('demo')
        child = l.addNode(l.getRoot(),1)
        child = l.addNode(child,2)
        child = l.addNode(child,3)
        child1 = l.addNode(child,31)
        child2 = l.addNode(child1,31)
        child3 = l.addNode(child1,31)
        child4 = l.addNode(child3,1)
        child5 = l.addNode(child3,2)
        child6 = l.addNode(child3,3)
        child7 = l.addNode(child3,4)
        child8 = l.addNode(child3,5)
        child9 = l.addNode(child3,6)
        child10 = l.addNode(child3,7)
        child11 = l.addNode(child3,8)
        child12 = l.addNode(child3,9)
        child = l.addNode(child,4)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child2,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,5)
        child = l.addNode(child,6)
        child = l.addNode(l.getRoot(),6)
        child = l.addNode(child,7)
        child = l.addNode(child,8)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(child,9)
        child = l.addNode(l.getRoot(),12)
 
        self.l = l
        self.child1 = child1
   
    def test1PrintTree(self):   
        print "*** original tree ***\n"
        print self.l
        print >> open("tree_test_graph/test1PrintTree", "w"), self.l
        self.assertTrue(shell_exec("diff tree_test_graph/test1PrintTree tree_test_graph/test1PrintTree.graph")[0] == 0)


    def test2SetNodeKey(self):   
        print "*** setNodeKey = -node.data ***\n"
        def node_key(node):
             #return str(node.data)
             return -node.data
        
        self.l.setNodeKey(node_key)
        print self.l
        print >> open("tree_test_graph/test2SetNodeKey", "w"), self.l
        self.assertTrue(shell_exec("diff tree_test_graph/test2SetNodeKey tree_test_graph/test2SetNodeKey.graph")[0] == 0)


    def test3SetNodeShow(self):   
        print "*** setNodeShow = \"node is\" + node.data ***\n"
        def node_show(node):
             return "node is " + str(node.data)
        self.l.setNodeShow(node_show)
        print self.l
        print >> open("tree_test_graph/test3SetNodeShow", "w"), self.l
        self.assertTrue(shell_exec("diff tree_test_graph/test3SetNodeShow tree_test_graph/test3SetNodeShow.graph")[0] == 0)

   
    def test4PrintNodeTreeReverse(self):   
        print "*** printNodeTreeReverse ***\n"
        print Tree.printNodeTreeReverse(self.child1)
        print >> open("tree_test_graph/test4PrintNodeTreeReverse", "w"), Tree.printNodeTreeReverse(self.child1)
        self.assertTrue(shell_exec("diff tree_test_graph/test4PrintNodeTreeReverse tree_test_graph/test4PrintNodeTreeReverse.graph")[0] == 0)


    def test5DelNode(self):   
        print "*** delNode = (node.data == 1) ***\n"
        def conditionfunc(node):
            return node.data == 1
        for i in self.l.findNodeBy(conditionfunc):
            self.l.delNode(i)
        print self.l
        print >> open("tree_test_graph/test5DelNode", "w"), self.l
        self.assertTrue(shell_exec("diff tree_test_graph/test5DelNode tree_test_graph/test5DelNode.graph")[0] == 0)


    def test6UpdateNode(self):   
        print "*** updateNode (data from 9 to 99)***\n"
        for i in self.l.findNode(9)[:]:
            self.l.updateNode(i, 99)
        print self.l
        print >> open("tree_test_graph/test6UpdateNode", "w"), self.l
        self.assertTrue(shell_exec("diff tree_test_graph/test6UpdateNode tree_test_graph/test6UpdateNode.graph")[0] == 0)

    def test7PrintNodeTree(self):   
        print "*** printNodeTree ***\n"
        print Tree.printNodeTree(self.child1)
        print >> open("tree_test_graph/test7PrintNodeTree", "w"), Tree.printNodeTree(self.child1)
        self.assertTrue(shell_exec("diff tree_test_graph/test7PrintNodeTree tree_test_graph/test7PrintNodeTree.graph")[0] == 0)


if __name__=="__main__":
    unittest.main()
