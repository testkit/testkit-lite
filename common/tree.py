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
#   simple tree
#

import types

class Node(object):

    @staticmethod
    def defaultNodeKey(node):
        return node.data


    @staticmethod
    def defaultNodeShow(node):
        return node.data


    def __init__(self,
                 parent=None,
                 data=None,
                 level=-1,
                 keyfunc=None,
                 showfunc=None):
        self.__parent = parent
        self.__data = data
        self.__children= []
        self.__level = level
        if not None == keyfunc:
            self.__keyfunc = keyfunc
        else:
            self.__keyfunc = self.defaultNodeKey
        if not None == showfunc:
            self.__showfunc = showfunc
        else:
            self.__showfunc = self.defaultNodeShow

        # some other suage
        self.param1 = None
        self.param2 = None
        self.param3 = None
        self.param4 = None


    def addChild(self, node):
        '''
        Add one child

        @param node: child node
        @type node: Node

        @return: None
        '''
        childset = set(self.__children)
        childset.add(node)
        self.__children = list(childset)
        self.__children.sort(key=self.__keyfunc)


    def delChild(self, node):
        '''
        Del one child

        @param node: child node
        @type node: Node

        @return: None
        '''
        childset = set(self.__children)
        childset.remove(node)
        self.__children = list(childset)
        self.__children.sort(key=self.__keyfunc)


    def setKeyfunc(self, keyfunc):
        '''
        set keyfunc for the node
        key is for node sort and default findChild in Tree

        @param keyfunc: keyfunc
        @type keyfunc: func(Node)

        @return: None
        '''
        self.__keyfunc = keyfunc
        self.__children.sort(key=self.__keyfunc)


    def setShowfunc(self, showfunc):
        '''
        set showfunc for the node

        @param showfunc: showfunc
        @type keyfunc: func(Node)

        @return: None
        '''
        self.__showfunc = showfunc


    @property
    def key(self):
        return self.__keyfunc(self)


    @property
    def parent(self):
        return self.__parent


    @property
    def data(self):
        return self.__data

    def setData(self, data):
        self.__data = data

    @property
    def children(self):
        return self.__children


    @property
    def level(self):
        return self.__level


    def __str__(self):
        return str(self.__showfunc(self))



class Tree(object):

    INDENT = 3

    def __init__(self,
                 tree_name,
                 node_keyfunc=None,
                 node_showfunc=None):

        self.__tree_name = tree_name
        self.__nodes_table = dict() # format: {key:[node, node ...], ...}
        self.__node_keyfunc = node_keyfunc
        self.__node_showfunc = node_showfunc
        # the head of the tree use default showfunc(just print data:root)
        self.__head = Node(None, tree_name, 0, self.__node_keyfunc)


    @property
    def tree_name(self):
        return self.__tree_name

    def getRoot(self):
        return self.__head

    def getAllKeys(self):
        return self.__nodes_table.keys()

    def addNode(self, parent, node_data):
        '''
        Add one node(child) to the specified parent node

        @param parent: parent node handler
        @type parent: Node
        @param node_data: data for this node(child)
        @type node_data: Any

        @return: node(child) handler
        @rtype: Node
        '''

        # add to parent's subtree
        child = Node(parent=parent, data=node_data,
                          level=parent.level+1,
                          keyfunc=self.__node_keyfunc,
                          showfunc=self.__node_showfunc)
        parent.addChild(child)

        # add to tree nodes table
        if (self.__nodes_table.has_key(child.key)):
            self.__nodes_table[child.key].append (child)
        else:
            self.__nodes_table[child.key] = [child]

        return child


    def delNode(self, node):
        '''
        Delete one node with child together from the tree

        @param node: node to be deleted
        @type node: Node

        @return: deleted node's parent node handler
        @rtype: Node
        '''

        # remove from parent's subtree
        node.parent.delChild(node)

        def del_from_table(_node):

            # remove from tree nodes table
            if (self.__nodes_table.has_key(_node.key)):
                self.__nodes_table[_node.key].remove (_node)
                if 0 == len(self.__nodes_table[_node.key]):
                    del self.__nodes_table[_node.key]

            for child in _node.children:
                del_from_table(child)

        del_from_table(node)


    def updateNode(self, node, node_data):
        '''
        update one node with new node_data

        @param node: node to be updated
        @type node: Node
        @param node_data: new data for this node
        @type node_data: Any

        @return: None
        '''
        old_key = node.key

        node.setData(node_data)

        # remove old from tree nodes table
        if (self.__nodes_table.has_key(old_key)):
            self.__nodes_table[old_key].remove (node)
            if 0 == len(self.__nodes_table[old_key]):
                del self.__nodes_table[old_key]

        # add new to tree nodes table
        if (self.__nodes_table.has_key(node.key)):
            self.__nodes_table[node.key].append (node)
        else:
            self.__nodes_table[node.key] = [node]


    def findNode(self, key):
        '''
        find node in the tree according to the key

        @param key: key to the node
        @type key: same with return of keyfunc

        @return: node
        @rtype: Node
        '''
        if self.__nodes_table.has_key(key):
            return self.__nodes_table[key]
        else:
            return []


    def clear(self):
        for child in self.getRoot().children:
            self.delNode(child)


    def setNodeKey(self, keyfunc):
        '''
        specify the key func of the node,
        key is for node sort and default FindChild

        @param keyfunc: key function
        @type keyfunc: func(Node)

        @return: None
        '''
        new_nodes_table = dict()
        self.__node_keyfunc = keyfunc

        self.__head.setKeyfunc(self.__node_keyfunc)

        for nodes in self.__nodes_table.values():
            for node in nodes:
                node.setKeyfunc(self.__node_keyfunc)

                if (new_nodes_table.has_key(node.key)):
                    new_nodes_table[node.key].append (node)
                else:
                    new_nodes_table[node.key] = [node]

        self.__nodes_table = new_nodes_table


    def setNodeShow(self, showfunc):
        '''
        specify the show func of the node

        @param showfunc: show function
        @type showfunc: func(Node)

        @return: None
        '''
        self.__node_showfunc = showfunc

        for nodes in self.__nodes_table.values():
            for node in nodes:
                node.setShowfunc(self.__node_showfunc)


    def findNodeBy(self, conditionfunc):
        '''
        search by conditionfunc, find out those nodes satifiy:
        conditionfunc(node) == true

        @param conditionfunc: condition function
        @type conditionfunc: func(Node), return: True/False

        @return: group of nodes
        @rtype: list with node
        '''

        # if conditionfunc specified, use conditionfunc
        returnNode = []
        for nodes in self.__nodes_table.values():
            for node in nodes:
                if conditionfunc(node):
                    returnNode.append (node)

        return returnNode


    @staticmethod
    def traverse(cb, node, *args):
        cb(node, *args)
        for child in node.children:
            Tree.traverse(cb, child, *args)


    @staticmethod
    def __printNode(node, *args):
        '''
        print one node

        @param node: node to be printed
        @type node: Node
        @param args[0]: holder dict to store holder
        @type  args[0]: dict with element int:char
        @param args[1]: string list to store print info
        @type  args[1]: list with element: string
        @param args[2]: initial level
        @type  args[2]: int

        @return: None
        '''
        if 3 == len(args) and \
           type(args[1]) == types.ListType and \
           type(args[1][0]) == types.StringType and \
           type(args[0]) == types.DictType:

            # make use of param1 to store children count
            node.param1 = len(node.children)

            def __update_holder(node):
                if node.param1 > 0:
                    args[0][node.level - args[2]] = '|'
                else:
                    args[0][node.level - args[2]] = ' '

            # set flag on holder, initially by node itself
            __update_holder(node)

            # print tree line
            for i in range(node.level - args[2]):
                if i == node.level - args[2] - 1 and \
                   1 == node.parent.param1:
                    args[1][0] += " "*Tree.INDENT + "`"
                else:
                    args[1][0] += " "*Tree.INDENT + args[0][i]
            args[1][0] += "-"*Tree.INDENT + str(node) + "\n"

            # decrease traversed child count of parent
            if node.parent and node.parent.param1:
                node.parent.param1 -= 1
                # set flag on holder, repeatedly update parent
                __update_holder(node.parent)

        else:
            raise RuntimeError("__printNode: args content is not accepted")


    @staticmethod
    def printNodeTree(node):
        '''
        print one node and its children

        @param node: node to be printed
        @type node: Node

        @return: print string
        @rtype: string
        '''
        return_str = [""]
        Tree.traverse(Tree.__printNode, node, {}, return_str, node.level)
        return return_str[0]


    @staticmethod
    def printNodeTreeReverse(node):
        '''
        print one node and its parent

        @param node: node to be printed
        @type node: Node

        @return: print string
        @rtype: string
        '''
        node_branch = []
        p = node

        while p != None:
            node_branch.append(p)
            p = p.parent

        lines = map(lambda node: node.level * 4 * ' ' + '`-- ' + str(node) + '\n', node_branch)
        lines.reverse()
        return reduce(lambda x,y: x+y, lines+[""])


    def __str__(self):
        return Tree.printNodeTree(self.__head)
