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
Implement all of the functions for computing the Condorcet winner and lower
bound.
'''

import numpy

def _add_child_to_matrix(n, who, cs, m):
    '''
    Add child C{who} with L{Node} C{n} to the matrix C{m}.

    @type  n: L{Node}
    @param n: Child node to add to C{m}.
    @type  who: number
    @param who: The child.
    @type  cs: list
    @param cs: Candidates.
    @type  m: C{numpy.matrix}
    @param m: The Condorcet matrix.
    '''
    if who in cs:
        cs = cs.copy()
        cs.remove(who)
    temp = [c-1 for c in cs]
    m[who-1, temp] += n.value
    for c in cs.intersection(n.children()):
        _add_child_to_matrix(n.get_child(c), c, cs, m)

def build_condorcet(election):
    '''Build and return a Condorcet matrix from an Election.
    
    This assumes the children of root are the integers 1, 2, ..., k. The matrix
    returned is 0-based.

    @type  election: L{Election}
    @param election: The election.
    @rtype: C{numpy.matrix}
    @return: Returns the 0-based Condorcet matrix representing the election.
    '''
    root = election.profile
    n = root.num_children()
    m = numpy.zeros((n, n), numpy.int32)
    candidates = root.children()
    for c, n in root.iterchildren():
        _add_child_to_matrix(n, c, candidates, m)
    return m

def condorcet_winner(m):
    '''Compute and return the Condorcet winner from the Condorcet matrix.

    @type  m: C{numpy.matrix}
    @param m: The Condorcet matrix.
    @rtype: number
    @return: The winner.

    The winner returned is 1-based, unlike the matrix.
    '''
    d = m - m.T
    winner = sum(numpy.sign(d).T) == len(m)-1
    if any(winner):
        return numpy.nonzero(winner)[0][0]+1
    return None

def condorcet_lb(m, winner=None):
    '''Return a lower bound on the Condorcet margin.

    This is the minimum pair-wise margin between the Condorcet winner and the
    other candidates. If there is no Condorcet winner, then 0 is returned.

    @type  m: C{numpy.matrix}
    @param m: The Condorcet matrix.
    @type  winner: number
    @param winner: The winner. This is computed if C{None}.
    @rtype: number
    @return: Returns the winner or 0 if there is no Condorcet winner.
    '''


    if winner is None:
        winner = condorcet_winner(m)
    if winner is None:
        return 0
    d = m - m.T
    row = d[winner-1]
    row[winner-1] = numpy.max(row)
    return min(row)

# vim: set sw=4 sts=4 tw=0 expandtab:
