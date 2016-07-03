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
This module implements the integer-linear programming methods for computing
the IRV margin exactly using the CPLEX library.
'''
import os
import itertools

import cplex
from cplex._internal._constants import CPXMIP_OPTIMAL, CPXMIP_OPTIMAL_TOL

def _optimization_problem():
    '''Create a new Cplex object that won't output a stupid banner.'''
    devnull = open(os.devnull, 'w')
    stderr = os.dup(2)
    os.dup2(devnull.fileno(), 2)
    devnull.close()
    prob = cplex.Cplex()
    os.dup2(stderr, 2)
    os.close(stderr)
    prob.set_results_stream(None)
    prob.set_log_stream(None)
    prob.objective.set_sense(prob.objective.sense.minimize)
    # Set wall clock time
    # pylint can't tell that these RootParameterGroup types have the appropriate
    # instance variables. They do.
    # pylint: disable=E1103
    prob.parameters.clocktype.set(prob.parameters.clocktype.values.wall)
    prob.parameters.parallel.set(prob.parameters.parallel.values.opportunistic)
    # pylint: enable=E1103
    return prob

_prob = None

def _ballot_to_name(b):
    '''Construct a string representation of ballots'''
    return 'S' + ''.join('%02d' % c for c in b)
    
def _tree_to_map_helper(root, profile, b):
    '''Helper for constructing the ballot profile.'''
    num = 0
    for c, n in root.iterchildren():
        num += n.value
        b.append(c)
        _tree_to_map_helper(n, profile, b)
        b.pop()
    if root.value > num:
        profile[_ballot_to_name(b)] = root.value-num

def _tree_to_map(root):
    '''Construct a ballot profile from a tree.'''
    profile = {}
    _tree_to_map_helper(root, profile, [])
    return profile

def _powerset(iterable, maxsize=None):
    '''Return the powerset of iterable.'''
    s = tuple(iterable)
    if maxsize == None:
        maxsize = len(s)
    else:
        maxsize = min(len(s), maxsize)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(maxsize+1))

def _compute_special(profile, v, coef):
    '''Compute the special inequalities'''
    variables = []
    coefs = []
    rhs = 0
    for signature in v:
        variables.append('P' + signature)
        coefs.append(coef)
        if signature in profile:
            variables.append('M' + signature)
            coefs.append(-coef)
            rhs += profile[signature]
    return variables, coefs, rhs

def distance_to(root, ranks, elim_order, timeout):
    '''Compute the distance_to function from Magrino et al.

    This formulation differs from Magrino et al. in three ways.
        1. The y_S variables are all removed so all that remains are p_S and m_S;
        2. The constraints on the p_S and m_S are replaced with simple bounds; and
        3. The objective function changed for the new definition of margin.
    
    3 is the most important. The original objective function was sum_S p_S.
    We want sum_{S != ()} (p_S + m_S). This works, but seems to be horribly
    inefficient. Using sum_S p_S = sum_S m_S, we can rewrite this as
    2*sum_{S != ()} m_S - p_{()} + m_{()}.

    @type  root: L{Node}
    @param root: Root of the ballot tree.
    @type  ranks: number
    @param ranks: The maximum number of candidates a voter can rank.
    @type  elim_order: list
    @param elim_order: The elimination order we would like.
    @type  timeout: number
    @param timeout: The computation timeout.
    @rtype: number
    @return: Returns -1 on timeout. Otherwise, it returns the margin.
    '''

    k = len(elim_order)
    if k < 2:
        return 0
    global _prob
    if _prob is None:
        _prob = _optimization_problem()
    root = root.deepcopy()
    root.reduce(elim_order)
    n = root.value
    profile = _tree_to_map(root)

    # add variables and constraints
    obj = []
    ub = []
    names = []
    basic = [[], []]
    constraints = [basic]
    # Ugh, this looks awful.
    # special[i][j] is the list of ballots that count for candidate elim_order[i+j]
    # in round i in {0,1,...,k-2}
    special = [[[] for _ in range(i, k)] for i in range(k-1)]
    rhs = [0]
    for subset in _powerset(range(len(elim_order)), ranks):
        # We don't need both final round candidates on a ballot
        if k-1 in subset and k-2 in subset:
            continue

        signature = _ballot_to_name(elim_order[i] for i in subset)
        # Add P_S and M_S
        ps = 'P' + signature
        if signature in profile:
            ms = 'M' + signature
            ns = profile[signature]
            names.extend((ps, ms))
            if subset:
                obj.extend((0, 2))
            else:
                obj.extend((-1, 1))
            ub.extend((n-ns, ns))
            basic[0].extend((ps, ms))
            basic[1].extend((1, -1))
        else:
            names.append(ps)
            if subset:
                obj.append(0)
            else:
                obj.append(-1)
            ub.append(n)
            basic[0].append(ps)
            basic[1].append(1)
        # Construct the special inequality sets P_{i,j}
        r = 0
        for i in subset:
            for s in special[r:i+1]:
                s[i-r].append(signature)
                r += 1

    # Now add in the special inequalities
    for s in special:
        iset, icoef, irhs = _compute_special(profile, s[0], 1)
        for t in s[1:]:
            jset, jcoef, jrhs = _compute_special(profile, t, -1)
            constraints.append([iset + jset, icoef + jcoef])
            rhs.append(jrhs - irhs)
    numspecial = (k*(k-1)) >> 1 # sum_{i=1}^{k-1} i = k(k-1)/2
    senses = 'E' + 'L'*numspecial


    # Construct problem and solve
    _prob.variables.delete()
    _prob.linear_constraints.delete()
    _prob.variables.add(obj=obj, ub=ub, types='I'*len(obj), names=names)
    _prob.linear_constraints.add(lin_expr=constraints, senses=senses, rhs=rhs)
    # pylint: disable=E1103
    _prob.parameters.timelimit.set(timeout)
    # pylint: enable=E1103
    _prob.solve()
    #print _prob.solution.status[_prob.solution.get_status()]
    status = _prob.solution.get_status()
    if status not in (CPXMIP_OPTIMAL, CPXMIP_OPTIMAL_TOL):
        return -1
    m = _prob.solution.get_objective_value()
    #print m, zip(_prob.variables.get_names(), _prob.solution.get_values())
    return m

# vim: set sw=4 sts=4 tw=0 expandtab:
