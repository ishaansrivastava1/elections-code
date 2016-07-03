# Copyright (c) 2011, Stephen Checkoway <s@cs.ucsd.edu>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
This module contains the Node class which is used to compactly represent and
modify ballots in an IRV election.
'''

import copy

class Node(object):
    '''A basic tree node with a value and children and IRV-specific methods.
    
    @type value: number
    @ivar value: The value of the node, including the sum of the values of 
    its children.
    @type _children: dict
    @ivar _children: The node's children.
    '''

    def __init__(self, value=0, children=None):
        '''Create a new node with an optional value and children nodes.
        
        @type  value: number
        @param value: The initial value of the node.
        @type  children: dict
        @param children: The initial children.
        '''
        self.value = value
        if children:
            self._children = children
        else:
            self._children = {}

    def __repr__(self):
        '''Return a representation of self.
        
        @rtype: string
        @return: Returns a string representation of the node.
        '''
        return "Node(value=%d, children=%s)" % (self.value, repr(self._children))
    
    def has_child(self, c):
        '''Return C{True} if the node has a child with name C{c}.
        
        @type  c: number
        @param c: The child.
        @rtype: boolean
        @return: Returns C{True} if the node has a child with name C{c}.
        '''
        return c in self._children

    def get_child(self, c):
        '''Return the child node, creating it first, if necessary.
        
        @type  c: number
        @param c: The child.
        @rtype: L{Node}
        @return: Returns the child node.
        '''
        if c not in self._children:
            n = Node()
            self._children[c] = n
        return self._children[c]

    def delete_child(self, c):
        '''Delete the child.

        @type  c: number
        @param c: The child.
        '''
        del self._children[c]

    def eliminate(self, c):
        '''Remove the child c and merge c's children with self's children.

        @type  c: number
        @param c: The child.
        '''
        if c in self._children:
            child = self._children[c]
            del self._children[c]
            # pylint: disable=W0212
            for name, node in child._children.iteritems():
                self.get_child(name)._merge(node)
            # pylint: enable=W0212
        for _, node in self._children.iteritems():
            node.eliminate(c)

    def _merge(self, n):
        '''Merge a node into self by adding the value and merging children.

        @type  n: L{Node}
        @param n: The node to merge in.
        '''
        self.value += n.value
        # pylint: disable=W0212
        if not self._children:
            self._children = n._children
        else:
            for name, node in n._children.iteritems():
                self.get_child(name)._merge(node)
        # pylint: enable=W0212

    def reduce(self, elim_order):
        '''Reduce the ballot tree modulo an elimination order.

        Assuming that the elimination order of the election is C{elim_order},
        reduce the number and type of ballots represented in the tree by
        weeding out ballots that do not contribute. For example, if C{i}
        preceeds C{j} in C{elim_order} and there is a ballot in which C{j}
        preceeds C{i}, then C{i} can be removed from the ballot completely.

        @type  elim_order: list
        @param elim_order: The elimination order.
        '''
        assert len(elim_order) == len(self._children)
        if len(elim_order) < 2:
            return
        for c, node in self._children.iteritems():
            # pylint: disable=W0212
            node._reduce(c, elim_order, 0)
            # pylint: enable=W0212

    def _reduce(self, c, elim_order, start):
        '''Reduce the ballot tree modulo an elimination order.'''
        # If the final round candidates appear, nothing farther down the ballot matters
        if c == elim_order[-1] or c == elim_order[-2]:
            self._children.clear()
            return
        idx = elim_order.index(c)
        for i in range(start, idx):
            self.eliminate(elim_order[i])
        start += 1
        for c, node in self._children.iteritems():
            # pylint: disable=W0212
            node._reduce(c, elim_order, start)
            # pylint: enable=W0212

    def children(self):
        '''Return a set of children names.
        
        @rtype: set
        @return: Returns the set of children.
        '''
        return set(self._children)

    def num_children(self):
        '''Return the number of children.
        
        @rtype: number
        @return: Returns the number of children.
        '''
        return len(self._children)

    def __iter__(self):
        '''Iterate over the set of children.
        
        @rtype: iterator
        @return: Returns an iterator which can be used to iterate over the
        children.
        '''
        return self._children.__iter__()

    def iterchildren(self):
        '''Iterate over the dictionary of children.
        
        @rtype: iterator
        @return: Returns an iterator that can be used to iterate over the
        children and the corresponding nodes at the same time.
        '''
        return self._children.iteritems()

    # pylint: disable=R0201
    def __copy__(self):
        '''This always raises an exception. Shallow copies are not permitted.
        
        @raise Exception: Always raises an exception.
        '''
        raise Exception( 'No copy()' )
    # pylint: enable=R0201

    def __deepcopy__(self, memo):
        '''Return a deep copy of the node.
        
        @rtype: L{Node}
        @return: Returns a deep copy.
        '''
        return Node(value=self.value, children=copy.deepcopy(self._children, memo))
    
    def deepcopy(self):
        '''Return a deep copy of the node.
        
        @rtype: L{Node}
        @return: Returns a deep copy.
        '''
        return copy.deepcopy(self)

# vim: set sw=4 sts=4 tw=0 expandtab:
