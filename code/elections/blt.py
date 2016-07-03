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
This module contains functions for reading and writing .blt files.
'''

import cPickle
import os
import re

from node import Node
from election import Election

# So little error checking!
def _read_blt(path):
    '''Parse a .blt file and return the L{Election}.

    @type  path: string
    @param path: File path.
    @rtype: L{Election}
    @return: Returns the L{Election}.
    '''
    f = open(path)
    # Skip over leading comments
    while True:
        line = f.readline()
        if len(line) == 0:
            raise Exception('Invalid blt')
        if len(line) and line[0] != '#':
            break

    # Get the number of candidates and seats
    num_candidates, seats = [int(x) for x in line.split()]
    root = Node()
    ranks = 0
    # Make sure the root has a child for every candidate
    for c in xrange(1, num_candidates+1):
        root.get_child(c)
    num_ballots = 0
    while True:
        line = f.readline()
        m = re.match(r'(\(.*?\) )?1 ([-=0-9 ]*)0', line)
        if not m:
            break
        num_ballots += 1
        choices = m.group(2).split()
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
                curr = curr.get_child(c)
                curr.value += 1

    if line != '0\n':
        raise Exception( 'Expected 0 after ballots "%s"' % line )

    names = dict()
    for c in xrange(1, num_candidates+1):
        names[c] = f.readline()[1:-2]
    description = f.readline()[1:-2]
    f.close()
    root.value = num_ballots
    return Election(names=names, profile=root, ranks=ranks, seats=seats, description=description)

def read_blt(path):
    '''Parse a .blt file or use a cached version and return an L{Election} instance.

    If the file is 'foo/bar.blt', check for the existence of 'foo/bar.pickle'.
    If it exists and it is newer than the .blt, use that. Otherwise, parse the
    .blt and update the .pickle.

    @type  path: string
    @param path: Path to the .blt.
    @rtype: L{Election}
    @return: An L{Election} representing the ballots at C{path}.
    '''
    name, _ = os.path.splitext(path)
    cached = name + '.pickle'
    t1 = os.path.getmtime(path)
    try:
        t2 = os.path.getmtime(cached)
    except os.error:
        t2 = -1
    election = None
    if t2 >= t1:
        f = open(cached)
        election = cPickle.load(f)
        f.close()
        # Ensure the versions match
        if election.version != Election.VERSION:
            election = None
    if election is None:
        # Parse it and cache it
        election = _read_blt(path)
        f = open(cached, 'w')
        cPickle.dump(election, f, -1)
        f.close()
    return election

def _write_blt(f, root, ranks, b):
    '''Write the node root to f.
    
    @type  f: file
    @param f: The C{file} object to write to.
    @type  root: L{Node}
    @param root: The root of the profile subtree to write.
    @type  ranks: number
    @param ranks: The number of candidates the voter was allowed to rank.
    @type  b: list
    @param b: List of candidates ranked ahead the children in the subtree.
    '''
    num = 0
    for c, n in root.iterchildren():
        num += n.value
        b.append(c)
        _write_blt(f, n, ranks, b)
        b.pop()
    if root.value > num:
        line = '1'
        for c in b:
            line += ' %d' % c
        if len(b) < ranks:
            line += ' -' * (ranks-len(b))
        line += ' 0\n'
        f.write(line * (root.value-num))

def write_blt(path, election):
    '''Write a "simplified" .blt file from the election.
    
    @type  path: string
    @param path: The path to the .blt file to write.
    @type  election: L{Election}
    @param election: The election to write out.
    '''
    f = open(path, 'w')
    f.write('%d %d\n' % (len(election.names), election.seats))
    _write_blt(f, election.profile, election.ranks, [])
    f.write('0\n')
    for n in range(1, len(election.names)+1):
        f.write('"%s"\n' % election.names[n])
    f.write('"%s"\n' % election.description)
    f.close()

# vim: set sw=4 sts=4 tw=0 expandtab:
