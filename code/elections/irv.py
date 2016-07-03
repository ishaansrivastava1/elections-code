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
Implement all the functions for computing IRV margins and bounds.

@sort: BASE_IRV_RULES, SF_RCV_RULES, COMPLETE_IRV_RULES
'''

import heapq
import itertools
import math
import sys
import time

try:
    import cplex_ilp as ilp
except ImportError:
    ilp = None

BASE_IRV_RULES, SF_RCV_RULES, COMPLETE_IRV_RULES = range(3)

def _elimination_set(root, rules, all_sets=None):
    '''Return the IRV elimination set for the tree of ballots.

    @type  root: L{Node}
    @param root: The root of the tree.
    @type  rules: enum
    @param rules: The rules to use to determine the set.
    If L{BASE_IRV_RULES} or {COMPLETE_IRV_RULES}, then return the candidate
    with the fewest top-choice votes.  If L{SF_RCV_RULES}, then use the
    San Francisco elimination rule which selects the largest set of candidates
    such that the sum of top-choice votes for the candidates in the set is less
    than the top-choice votes for every candidate outside of the set.
    @type  all_sets: list
    @param all_sets: If C{rules =} L{SF_RCV_RULES}, and all_sets is a list, append
    every valid elimination set.
    @rtype: set
    @return: Returns the set of candidates to eliminate.

    Note that ties are handled by selecting one of the candidates with the
    fewest top-choice votes.
    '''
    if rules == BASE_IRV_RULES or rules == COMPLETE_IRV_RULES:
        # Remove the candidate with the fewest votes
        low_candidate = 0
        low_votes = sys.maxint
        for c, n in root.iterchildren():
            if n.value < low_votes:
                low_candidate = c
                low_votes = n.value
        return set([low_candidate])
    elif rules == SF_RCV_RULES:
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
        sorted_candidates = sorted(root.__iter__(), key=lambda c: root.get_child(c).value)
        groups = itertools.groupby(sorted_candidates, key=lambda c: root.get_child(c).value)
        groups = ((k, len(tuple(g))) for k, g in groups)
        n = 0 # sum of votes for sortedCandidates[:j]
        i = 0 # sortedCandidates[:i] are definitely going to be eliminated
        j = 0
        # Now iterate through them, updating i if possible
        for k, num in groups:
            if n < k:
                i = j
                if i > 0 and all_sets is not None:
                    all_sets.append( set(sorted_candidates[:i]) )
            n += k*num
            j += num
        if i == 0:
            print 'There was a tie and not all tied candidates could be eliminated!'
            return set(sorted_candidates[:1])
        else:
            return set(sorted_candidates[:i])
    else:
        assert False, 'Which rules should I be using?'

def irv_round(profile, rounds, rules=BASE_IRV_RULES):
    '''Perform at most rounds rounds of IRV using rules.

    @type  profile: L{Node}
    @param profile: The ballot profile.
    @type  rounds: number
    @param rounds: The maximum number of rounds to perform.
    @type  rules: enum
    @param rules: The IRV rules to use for elimination.
    @rtype: number, dict, list, L{Node}
    @return: Returns the winner, if any, the count of votes in each round, the
    list of elimination sets used, and the reduced tree after having eliminated
    candidates.
    '''
    root = profile.deepcopy()
    candidates = root.children()
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
        num_votes = 0
        high_candidate = 0
        high_votes = 0

        # Record the number of votes each candidate gets in this round
        for c, n in root.iterchildren():
            assert c not in eliminated, c
            counts[c][r-1] = n.value
            num_votes += n.value
            if n.value > high_votes:
                high_candidate = c
                high_votes = n.value

        # Check if the candidate with the most votes has a majority
        if rules != COMPLETE_IRV_RULES and high_votes*2 > num_votes \
                or root.num_children() <= 2:
            winner = high_candidate
            final_elim = candidates - eliminated
            final_elim.remove(winner)
            elimination.append(final_elim)
            break

        # Compute the candidates to be eliminated
        lowest = _elimination_set( root, rules )

        # Eliminate these candidates
        for c in lowest:
            root.eliminate(c)
            eliminated.add(c)
        # Add them to the elimination order
        elimination.append(lowest)
    
    if r < rounds:
        for c in counts.keys():
            del counts[c][r-rounds:]
    return (winner, counts, elimination, root)

def irv(election, rules=BASE_IRV_RULES):
    '''Perform IRV using C{rules} and return the winner, vote counts, and
    elimination order.
    
    @type  election: L{Election}
    @param election: The election.
    @type  rules: enum
    @param rules: The rules to use.
    @rtype: number, dict, list
    @return: Returns the winner, the vote counts, and the elimination order.
    '''
    root = election.profile
    winner, counts, elimination, _ = irv_round(root, root.num_children(), rules=rules)
    return (winner, counts, elimination)


def irv_simple_lb(election, rules=SF_RCV_RULES):
    '''Compute and return an IRV margin lower bound using the elimination sets
    dictated by the rules.
    
    @type  election: L{Election}
    @param election: The election.
    @type  rules: enum
    @param rules: The rules to use.
    @rtype: number
    @return: Returns the lower bound.
    '''
    root = election.profile
    lb = sys.maxint
    winner = None
    while winner is None:
        elim_set = _elimination_set(root, rules=rules)
        continuing = root.children() - elim_set
        m = min(root.get_child(c).value for c in continuing) - sum(root.get_child(c).value for c in elim_set)
        lb = min(lb, m)
        winner, _, _, root = irv_round(root, 1, rules=rules)   
    return lb

def irv_margin(election, winner=None, elim_order=None, ub=None, trace=False, timeout=1e75):
    '''Compute the exact IRV margin of the election.

    @type  election: L{Election}
    @param election: The election.
    @type  winner: number
    @param winner: The winner of the election. If C{None}, it will be computed.
    @type  elim_order: list
    @param elim_order: The elimination order. If C{None}, it will be computed.
    @type  ub: number
    @param ub: An upper bound on the margin. If C{None}, it will be computed via L{irv_ub}.
    @type  trace: boolean
    @param trace: If C{True}, print a trace of the computation.
    @type  timeout: number
    @param timeout: The amount of time to spend computing the margin.
    @rtype: number
    @return: Returns the IRV margin.
    '''
    if ilp is None:
        raise Exception('Cannot compute irv_margin() because no optimizer library could be loaded.')
    then = time.time()
    if winner is None or elim_order is None:
        winner, _, elim_order = irv(election)
    if ub is None:
        ub = irv_ub(election, winner=winner, elim_order=elim_order)

    # We can eliminate candidates who _must_ be eliminated first.  The
    # reasoning is that for them to not be eliminated, more votes would have to
    # be shifted than the upper bound on the margin.
    root = election.profile.deepcopy()
    while True:
        esets = []
        _elimination_set(root, all_sets=esets, rules=SF_RCV_RULES)
        max_eset = set()
        candidates = root.children()
        for eset in esets:
            if len(eset) <= len(max_eset):
                continue
            lb = min(root.get_child(c).value for c in candidates - eset) - \
                 sum(root.get_child(c).value for c in eset)
            if lb > ub:
                max_eset = eset
        if not max_eset:
            break
        for c in max_eset:
            if trace:
                print 'Eliminating candidate %d' % c
            root.eliminate(c)

    # This is the algorithm from Magrino et al., more or less
    candidates = root.children()
    k = len(candidates)
    tertiary = []
    elims = set((winner,))
    j = len(elim_order)-1
    for i in range(1, k+1):
        if i >= len(elims):
            elims = elims.union(elim_order[j])
            j -= 1
        tertiary.append(elims)
    if trace:
        print tertiary
        
    ranks = election.ranks
    fringe = []
    for c in candidates:
        if c == winner:
            continue
        if trace:
            print '\t', '(%d)' % c, 0, -1, 0
        heapq.heappush(fringe, (0, -1, 0, [c]))
    while True:
        d, s, t, elim = heapq.heappop(fringe)
        if trace:
            print tuple(elim), d, s, t
        if len(elim) == k:
            return d
        now = time.time()
        timeout -= now - then
        if timeout <= 0.0:
            return -1
        then = now
        elim_set = set(elim)
        prefixes = candidates - elim_set
        for c in prefixes:
            reduced = root.deepcopy()
            for e in prefixes - set((c,)):
                reduced.eliminate(e)
            new_elim = [c] + elim
            if trace:
                print '\t', tuple(new_elim),
                sys.stdout.flush()
            d = ilp.distance_to(reduced, ranks, new_elim, timeout)
            if d == -1:
                return -1
            if d <= ub:
                s = -len(new_elim)
                t = len(set(new_elim) - tertiary[len(new_elim)-1])
                if trace:
                    print d, s, t
                heapq.heappush(fringe, (d, s, t, new_elim))
            elif trace:
                print d

def irv_lb(election, eliminations=None, trace=False):
    '''Compute and return an IRV margin lower bound and the optimal sequence of
    eliminations that gives it.

    @type  election: L{Election}
    @param election: The election.
    @type  eliminations: list
    @param eliminations: If not C{None}, it is set to the optimal sequence of
    eliminations that gives the lower bound.
    @type  trace: boolean
    @param trace: If C{True}, then print out at trace of the computation.
    @rtype: number
    @return: Returns the lower bound.
    '''
    root = election.profile
    # We want a max heap, Python uses a min heap, be careful
    wl = [(-sys.maxint, [], root)]
    while True:
        m, s, root = heapq.heappop(wl)
        m = -m
        if trace:
            print 'Examining %d' % m
        if root.num_children() == 1:
            if trace:
                print 'Found lb %d' % m
            if eliminations is not None:
                del eliminations[:]
                eliminations.extend(s)
            return m
        elim_sets = []
        _elimination_set(root, rules=SF_RCV_RULES, all_sets=elim_sets)
        for elim_set in elim_sets:
            new_root = root.deepcopy()
            continuing = new_root.children() - elim_set
            m2 = min(new_root.get_child(c).value for c in continuing) \
                     - sum(new_root.get_child(c).value for c in elim_set)
            for c in elim_set:
                new_root.eliminate(c)
            if trace:
                print 'Pushing %d' % min(m, m2)
            s2 = list(s)
            s2.append(elim_set)
            heapq.heappush(wl, (-min(m, m2), s2, new_root))

# Margin m, old loser j, new loser k, winner w
# This changes the margin by more than m.
def _modify_margin(root, m, j, k, elim_order, w, trace):
    '''Modify the round-margin by more than m.

    @type  root: L{Node}
    @param root: The root of the ballot tree.
    @type  m: number
    @param m: The current margin (more or less).
    @type  j: number
    @param j: The recipient of the shifted votes.
    @type  k: number
    @param k: The one who loses votes.
    @type  elim_order: list
    @param elim_order: The current elimination order.
    @type  w: number
    @param w: The current winner.
    @type  trace: boolean
    @param trace: If C{True}, then print a trace of the computation.
    @rtype: number
    @return: Returns the number of ballots changed.
    '''
    assert j in elim_order[0]
    assert m >= 0
    steal_from_order = []
    for es in elim_order[1:]:
        steal_from_order.extend(es)
    steal_from_order.append(w)
    steal_from_order.extend(elim_order[0] - set((j,)))
    steal_from_order.append(j)
    steal_from_order.remove(k)

    def _steal_votes(node, m, path):
        '''Steal at least m votes'''
        changed = 0
        # Try children
        for c in steal_from_order:
            if node.has_child(c):
                child = node.get_child(c)
                path.append(c)
                subtotal, m = _steal_votes(child, m, path)
                path.pop()
                assert child.value >= 0
                changed += subtotal
                node.value -= subtotal
                if child.value == 0:
                    node.delete_child(c)
                if m < 0:
                    return (changed, m)
        # Try self
        if node.value > 0:
            x = min(node.value, math.floor(m/2)+1)
            assert x > 0
            node.value -= x
            root.get_child(j).value += x
            m -= 2*x
            changed += x
            if trace:
                print 'shifting %d from %s to %d' % (x, str(path), j)
        return (changed, m)
    return _steal_votes(root.get_child(k), m, [k])[0]

# Using the SF RCV rules cannot increase the upper bound; however, if the 
# base IRV rules are wanted, they can be used.
def irv_ub(election, rules=SF_RCV_RULES, winner=None, elim_order=None, trace=False):
    '''Compute and return an IRV margin upper bound.

    @type  election: L{Election}
    @param election: The election.
    @type  rules: enum
    @param rules: The rules to use. Should probably not be changed.
    @type  trace: boolean
    @param trace: If C{True}, then print a trace of the computation.
    @rtype: number
    @return: Returns an upper bound on the margin.
    '''
    root = election.profile
    candidates = root.children()
    error = dict()

    if winner is None or elim_order is None:
        winner, _, elim_order = irv(election, rules=rules)
    for j in candidates:
        if j == winner:
            continue
        new_root = root.deepcopy()
        w = winner
        mod_elim_order = elim_order
        error[j] = 0
        while w == winner:
            l = 0
            while j not in mod_elim_order[l]:
                l += 1
            if l > 0:
                _, _, _, new_root = irv_round(new_root, l, rules=rules)
            # Since j was eliminated in round l (starting with round 0), for j
            # to not be eliminated, j needs more votes than everyone else who
            # was eliminated in round l and the sum of the votes for those
            # eliminated in round l must be at least the number of votes of
            # one candidate not eliminated in round l.

            votes_for_j = new_root.get_child(j).value
            diff = sys.maxint
            for c in new_root.children() - mod_elim_order[l]:
                d = new_root.get_child(c).value - votes_for_j
                if d < diff:
                    k = c
                    diff = d
            assert diff < sys.maxint
            s = sum( new_root.get_child(c).value for c in mod_elim_order[l] )
            m = new_root.get_child(k).value - s
            if s > votes_for_j:
                m -= 1
            assert m >= 0
            error[j] += _modify_margin(new_root, m, j, k, mod_elim_order[l:], w, trace)
            w, _, mod_elim_order, _ = irv_round(new_root, new_root.num_children(), rules=rules)
        if trace:
            print 'error[%d] = %d' % (j, error[j])
    return 2*min(error.values())

# vim: set sw=4 sts=4 tw=0 expandtab:
