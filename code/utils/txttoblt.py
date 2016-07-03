#!/usr/bin/env python

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

# This takes the Alameda County ballot image file and master lookup file for 
# an election and spits out a simplified .blt

import sys
import os
import codecs

name, ext = os.path.splitext(sys.argv[1])
txt = open(sys.argv[1])
master = codecs.open(sys.argv[2], 'r', 'utf-8')

contestId = None
candidates = {}
for line in master:
    rtype = line[0:10]
    if rtype == 'Candidate ': # space is important
        cid = int(line[10:17])
        name = line[17:67].strip()
        order = int(line[67:74])
        candidates[cid] = (order, name)
        conId = int(line[74:81])
        if contestId == None:
            contestId = conId
        else:
            assert contestId == conId
    elif rtype == 'Contest   ':
        description = line[17:67].strip()

overvotes = {}
votes = {}
maxrank = 0
for line in txt:
    conId = int(line[0:7])
    vid = int(line[7:16])
    pid = int(line[26:33])
    rank = int(line[33:36])
    cid = int(line[36:43])
    assert rank > 0
    assert conId == contestId
    if (pid,vid) not in votes:
        votes[(pid,vid)] = {}
    assert rank not in votes[(pid,vid)]
    if vid in overvotes and rank >= overvotes[(pid,vid)]:
        continue
    if cid == 0:
        votes[(pid,vid)][rank] = '-'
        if line[43] == '1': # overvote
            overvotes[(pid,vid)] = rank
            votes[(pid,vid)][rank] = '-=-'
        else:
            assert line [44] == '1' # undervote
    else:
        votes[(pid,vid)][rank] = candidates[cid][0]
        assert line[43:45] == '00'
    maxrank = max(rank, maxrank)
ranks = range(1,maxrank+1)
print '# Created by Stephen Checkoway'
print '%d 1' % len(candidates)
for pvid in sorted(votes):
    v = votes[pvid]
    sv = ' '.join(str(v[r]) for r in sorted(v))
    print '1 %s 0' % sv

print '0'
names = [candidates[cid][1] for cid in sorted(candidates.keys(), key=lambda c: candidates[c][0])]
for n in names:
    print ('"%s"' % n).encode('utf-8')
print ('"%s"' % description).encode('utf-8')

# vim: set sw=4 sts=4 tw=0 expandtab:
