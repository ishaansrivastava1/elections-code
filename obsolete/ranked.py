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

import copy
import sys
import re
import string
import numpy
import cPickle
import os
import itertools
import heapq

BaseIRVRules, SFRCVRules = range(2)

class Node(object):
    '''A basic tree node with a value and children and IRV-specific methods.'''

    def __init__(self, value=0, children=None):
        '''Create a new node with an optional value and children nodes.'''
        self.value = value
        if children:
            self.children = children
        else:
            self.children = {}

    def __repr__(self):
        '''Return a representation of self.'''
        return "Node(value=%d, children=%s)" % (self.value, repr(self.children))
    
    def hasChild(self, c):
        '''Return True if the node has a child with name c.'''
        return c in self.children

    def getChild(self, c):
        '''Return the child node, creating it first, if necessary.'''
        if c not in self.children:
            n = Node()
            self.children[c] = n
        return self.children[c]

    def distribute(self, c):
        '''Remove the child c and merge c's children with self's children.'''
        if c in self.children:
            child = self.children[c]
            del self.children[c]
            for name, node in child.children.items():
                self.getChild(name)._merge(node)
        for _, node in self.children.items():
            node.distribute(c)

    def _merge(self, n):
        '''Merge a node into self by adding the value and merging children.'''
        self.value += n.value
        if not self.children:
            self.children = n.children
        else:
            for name, node in n.children.items():
                self.getChild(name)._merge(node)

    def sortedChildren(self):
        '''Return a list of children, sorted by value.'''
        return sorted( self.children, key=lambda c: self.children[c].value )

    def __copy__(self):
        '''No shallow copies.'''
        raise Exception( 'No copy()' )

    def __deepcopy__(self, memo):
        '''Return a deep copy of the node.'''
        n = Node()
        n.children = copy.deepcopy( self.children, memo )
        n.value = self.value
        return n
    
    def deepcopy(self):
        '''Return a deep copy of the node.'''
        return copy.deepcopy(self)

# So little error checking!
def _parseBLT(file):
    '''Parse a .blt file and return a tree of ballots.'''
    f = open(file)
    # Skip over leading comments
    while True:
        line = f.readline()
        if len(line) == 0:
            raise Exception('Invalid blt')
        if len(line) and line[0] != '#':
            break

    # Get the number of candidates and seats
    numCandidates, seats = [int(x) for x in string.split(line)]
    root = Node()
    ranks = 0
    # Make sure the root has a child for every candidate
    for c in xrange(1,numCandidates+1):
        root.getChild(c)
    numBallots = 0
    while True:
        line = f.readline()
        m = re.match(r'\(.*?\) 1 ([-=0-9 ]*)0', line)
        if not m:
            break
        numBallots += 1
        choices = string.split( m.group(1) )
        ranks = max(ranks, len(choices))
        seen = set()
        curr = root
        for c in choices:
            if c == '-':
                continue
            if '=' in c:
                break
            c = int(c)
            if c not in seen:
                seen.add(c)
                curr = curr.getChild(c)
                curr.value += 1

    if line != '0\n':
        raise Exception( 'Expected 0 after ballots "%s"' % line )

    names = dict()
    for c in xrange(1, numCandidates+1):
        names[c]= f.readline()[1:-2]
    description = f.readline()[1:-2]
    f.close()
    return (root, numBallots, ranks, names, description)

def parseBLT(file):
    '''Parse a .blt file or use a cached version and return a tree of ballots.

    If the file is 'foo/bar.blt', check for the existence of 'foo/bar.pickle'.
    If it exists and it is newer than the .blt, use that. Otherwise, parse the
    .blt and update the .pickle.

    Return the tree, the number of ballots, how many candidates can be ranked,
    the names of the candidates, and a description of the contest.
    '''
    name, ext = os.path.splitext(file)
    cached = name + '.pickle'
    t1 = os.path.getmtime(file)
    try:
        t2 = os.path.getmtime(cached)
    except os.error:
        t2 = -1
    if t2 < t1:
        # Parse it and cache it
        root, numBallots, ranks, names, description = _parseBLT(file)
        f = open(cached, 'w')
        cPickle.dump((root, numBallots, ranks, names, description), f, -1)
        f.close()
    else:
        f = open(cached)
        root, numBallots, ranks, names, description = cPickle.load(f)
        f.close()
    return (root, numBallots, ranks, names, description)

def _writeBLT(f, root, ranks, b):
    '''Write the node root to f.'''
    num = 0
    for c, n in root.children.iteritems():
        num += n.value
        b.append(c)
        _writeBLT(f, n, ranks, b)
        b.pop()
    if root.value > num:
        line = '(0) 1'
        for c in b:
            line += ' %d' % c
        if len(b) < ranks:
            line += ' -' * (ranks-len(b))
        line += ' 0\n'
        f.write(line * (root.value-num))

def writeBLT(file, root, ranks, names, description):
    '''Write a "simplified" .blt file from the tree of ballots.'''
    f = open(file, 'w')
    f.write('%d 1\n' % len(names))
    _writeBLT(f, root, ranks, [])
    f.write('0\n')
    for n in range(1,len(names)+1):
        f.write('"%s"\n' % names[n])
    f.write('"%s"\n' % description)
    f.close()

def _eliminationSet(root, rules, allSets=None):
    '''Return the IRV elimination set for the tree of ballots.

    root    - The root of the tree.
    rules   - The rules to use to determine the set.
        If rules = BaseIRVRules, then return the candidate with the fewest
        top-choice votes.
        If rules = SFRCVRules, then use the San Francisco elimination rule
        which selects the largest set of candidates such that the sum of
        top-choice votes for the candidates in the set is less than the
        top-choice votes for every candidate outside of the set.
    allSets - If rules = SFRCVRules, and allSets is a list, append every
        valid elimination set.

    Note that ties are handled by selecting one of the candidates with the
    fewest top-choice votes.
    '''
    if rules == BaseIRVRules:
        # Remove the candidate with the fewest votes
        lCandidate = 0
        lVotes = sys.maxint
        for c, n in root.children.iteritems():
            if n.value < lVotes:
                lCandidate = c
                lVotes = n.value
        return set( [lCandidate] )
    elif rules == SFRCVRules:
        # S.F., Cal., Charter art. XIII s. 13.102(e)
        # If the total number of votes of the two or more candidates
        # credited with the lowest number of votes is less than the number
        # of votes credited to the candidate with the next highest number
        # of votes, those candidates with the lowest number of votes shall
        # be eliminated simultaneously and their votes transferred to the
        # next-ranked continuing candidate on each ballot in a single
        # counting operation.

        # Apparently this is supposed to mean that you take the largest
        # set E such that the sum of all votes for candidates in E is
        # smaller than the number of votes for any candidate outside of E.
        # This is the logic that OpenSTV exhibits from input/output pairs.

        # Sort the candidates based on votes received and then group them
        # by vote totals
        sortedCandidates = root.sortedChildren()
        groups = itertools.groupby(sortedCandidates, key=lambda c: root.getChild(c).value)
        groups = [(k,len(list(g))) for k, g in groups]
        n = 0 # sum of votes for sortedCandidates[:j]
        i = 0 # sortedCandidates[:i] are definitely going to be eliminated
        j = 0
        # Now iterate through them, updating i if possible
        for k, num in groups:
            if n < k:
                i = j
                if i > 0 and allSets != None:
                    allSets.append( set(sortedCandidates[:i]) )
            n += k*num
            j += num
        if i == 0:
            print 'There was a tie and not all tied candidates could be eliminated!'
            return set( sortedCandidates[:1] )
        else:
            return set( sortedCandidates[:i] )
    else:
        assert False, 'Which rules should I be using?'

def irvRound(root, rounds, rules=BaseIRVRules):
    '''Perform at most rounds rounds of IRV using rules.

    root   - The root of the tree.
    rounds - The maximum number of rounds to perform.
    rules  - The IRV rules to use for elimination.

    Return the winner, if any, the count of votes in each round, the list of
    elimination sets used, and the reduced tree after having eliminated
    candidates.
    '''
    root = root.deepcopy()
    candidates = set(root.children.keys())
    eliminated = set()
    # Return values
    winner = None
    counts = dict()
    elimination = []

    for c in candidates:
        counts[c] = rounds*[0]
    r = 0
    while r < rounds:
        r += 1
        numVotes = 0
        hCandidate = 0
        hVotes = 0

        # Record the number of votes each candidate gets in this round
        for c, n in root.children.iteritems():
            assert c not in eliminated, c
            counts[c][r-1] = n.value
            numVotes += n.value
            if n.value > hVotes:
                hCandidate = c
                hVotes = n.value

        # Check if the candidate with the most votes has a majority
        if hVotes*2 > numVotes:
            winner = hCandidate
            finalElim = candidates - eliminated
            finalElim.remove(winner)
            elimination.append(finalElim)
            break

        # Compute the candidates to be eliminated
        lowest = _eliminationSet( root, rules )

        # Eliminate these candidates
        for c in lowest:
            root.distribute(c)
            eliminated.add(c)
        # Add them to the elimination order
        elimination.append(lowest)
    
    if r < rounds:
        for c in counts.keys():
            del counts[c][r-rounds:]
    return (winner, counts, elimination, root)

def irv(root, rules=BaseIRVRules):
    '''Perform IRV using rules and return the winner, vote counts, and elimination order.'''
    winner, counts, elimination, _ = irvRound(root, len(root.children), rules=rules)
    return (winner, counts, elimination)


def irvSimpleLB(root, rules=SFRCVRules):
    '''Compute and return an IRV margin lower bound using the elimination sets dictated by the rules.'''
    lb = sys.maxint
    winner = None
    while winner == None:
        ES = _eliminationSet(root, rules=rules)
        continuing = set(root.children) - ES
        m = min(root.getChild(c).value for c in continuing) - sum(root.getChild(c).value for c in ES)
        lb = min(lb, m)
        winner, _, _, root = irvRound(root, 1, rules=rules)   
    return lb

def irvLB(root, trace=False):
    '''Compute and return an IRV margin lower bound and the optimal sequence of eliminations that gives it.

    If trace is True, then print out some messages as the algorithm computes the bound.
    '''
    # We want a max heap, Python uses a min heap, be careful
    wl = [(-sys.maxint, [], root)]
    while True:
        m, s, root = heapq.heappop(wl)
        m = -m
        if trace:
            print 'Examining %d' % m
        if len(root.children) == 1:
            if trace:
                print 'Found lb %d' % m
            return m, s
        ESs = []
        _eliminationSet(root, rules=SFRCVRules, allSets=ESs)
        for ES in ESs:
            U = root.deepcopy()
            continuing = set(U.children) - ES
            m2 = min(U.getChild(c).value for c in continuing) - sum(U.getChild(c).value for c in ES)
            for c in ES:
                U.distribute(c)
            if trace:
                print 'Pushing %d' % min(m,m2)
            s2 = list(s)
            s2.append(ES)
            heapq.heappush(wl, (-min(m, m2), s2, U))

# Margin m, old loser j, new loser k, winner w
# This changes the margin by more than m.
def _modifyMargin(U, m, j, k, elimOrder, w, trace):
    '''Modify the round-margin by more than m.

    U         - The root of the ballot tree.
    m         - The current margin (more or less).
    j         - The recipient of the shifted votes.
    k         - The one who loses votes.
    elimOrder - The current elimination order.
    w         - The current winner.
    trace     - If this is True, then print messages as votes are shifted.
    '''
    assert j in elimOrder[0]
    assert m >= 0
    B = []
    for es in elimOrder[1:]:
        B.extend( es )
    B.append( w )
    B.extend( elimOrder[0]-set([j]) )
    B.append(j)
    B.remove(k)

    def f(node, m, path):
        changed = 0
        # Try children
        for c in B:
            if node.hasChild(c):
                child = node.getChild(c)
                path.append(c)
                subtotal, m = f(child, m, path)
                path.pop()
                assert child.value >= 0
                changed += subtotal
                node.value -= subtotal
                if child.value == 0:
                    del node.children[c]
                if m < 0:
                    return (changed, m)
        # Try self
        if node.value > 0:
            x = min(node.value, numpy.floor(m/2)+1)
            assert x > 0
            node.value -= x
            U.getChild(j).value += x
            m -= 2*x
            changed += x
            if trace:
                print 'shifting %d from %s to %d' % (x, str(path), j)
        return (changed, m)
    return f( U.getChild(k), m, [k] )[0]

# Using the SF RCV rules cannot increase the upper bound; however, if the 
# base IRV rules are wanted, they can be used.
def irvUB(root, rules=SFRCVRules, trace=False):
    '''Compute and return an IRV margin upper bound.

    root  - The root of the ballot tree.
    rules - The rules to use. Should probably not be changed.
    trace - If this is True, then print messages as votes are shifted.
    '''
    candidates = set(root.children.keys())
    error = dict()
    winner, _, elimOrder = irv(root, rules=rules)
    for j in candidates:
        if j == winner:
            continue
        U = root.deepcopy()
        w = winner
        modElimOrder = elimOrder
        error[j] = 0
        while w == winner:
            l = 0
            while j not in modElimOrder[l]:
                l += 1
            if l > 0:
                _, _, _, U = irvRound(U, l, rules=rules)
            # Since j was eliminated in round l (starting with round 0), for j
            # to not be eliminated, j needs more votes than everyone else who
            # was eliminated in round l and the sum of the votes for those
            # eliminated in round l must be at least the number of votes of
            # one candidate not eliminated in round l.

            jVotes = U.getChild(j).value
            diff = sys.maxint
            for c in set(U.children) - modElimOrder[l]:
                d = U.getChild(c).value - jVotes
                if d < diff:
                    k = c
                    diff = d
            assert diff < sys.maxint
            s = sum( U.getChild(c).value for c in modElimOrder[l] )
            m = U.getChild(k).value - s
            if s > jVotes:
                m -= 1
            assert m >= 0
            error[j] += _modifyMargin(U, m, j, k, modElimOrder[l:], w, trace)
            w, _, modElimOrder = irv(U, rules=rules)
        if trace:
            print 'error[%d] = %d' % (j, error[j])
    return 2*min(error.values())


def buildCondorcet(root):
    '''Build and return a Condorcet matrix from the tree of ballots.
    
    This assumes the children of root are the integers 1, 2, ..., k. The matrix
    returned is 0-based.
    '''
    n = len(root.children)
    m = numpy.zeros((n,n), numpy.int32)
    def f(n, who, cs):
        if who in cs:
            cs = cs.copy()
            cs.remove(who)
        temp = [c-1 for c in cs]
        m[who-1,temp] = m[who-1,temp] + n.value
        if not n.children:
            return
        for c in cs:
            if n.hasChild(c):
                f( n.getChild(c), c, cs )
    candidates = set(root.children.keys())
    for c, n in root.children.items():
        f(n, c, candidates)
    return m

def condorcetWinner(m):
    '''Compute and return the Condorcet winner from the Condorcet matrix.

    The winner returned is 1-based, unlike the matrix.
    '''
    d = m - m.T
    winner = sum(numpy.sign(d).T) == len(m)-1
    if any(winner):
        return numpy.nonzero(winner)[0][0]+1
    return None

def condorcetMargin(m):
    '''Compute and return the Condorcet margin.'''
    winner = condorcetWinner(m)
    if winner is None:
        return None
    d = m - m.T
    row = d[winner-1]
    row[winner-1] = numpy.max(row)
    return min(row)

# vim: set sw=4 sts=4 tw=0 expandtab:
