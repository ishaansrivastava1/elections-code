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

# Split Aspen data into city council and Mayor

import sys

f = open( sys.argv[1] )
f.readline() # Skip leading line

cc = open( '2009-Aspen-City_Council.blt', 'w' )
cc.write( '# Created by Stephen Checkoway\n' )
cc.write( '11 2\n' )
m = open( '2009-Aspen-Mayor.blt', 'w' )
m.write( '# Created by Stephen Checkoway\n' )
m.write( '5 1\n' )

def clean(x):
    return tuple('-' if c == '0' else c for c in x)

for l in f:
    cvr = l.split( ',' )
    assert len(cvr) == 22, len(cvr)
    cc.write( '1 %s %s %s %s %s %s %s %s %s 0\n' % clean(cvr[1:10]) )
    m.write( '1 %s %s %s %s 0\n' % clean(cvr[14:18]) )
f.close()
cc.write( '''0
"Jackie Kasabach"
"Jack Johnson"
"Adam Frisch"
"Torre"
"Michael Behrendt"
"Jason Lasser"
"Michael Wampler"
"Derek Johnson"
"Brian Daniel Speck"
"Write-in 1"
"Write-in 2"
"2009 Aspen City Council"
''' )
cc.close()
m.write( '''0
"Marilyn Marks"
"LJ Erspamer"
"Andrew Kole"
"Michael C. 'Mick' Ireland"
"Write-in"
"2009 Aspen Mayor"
''' )
m.close()

# vim: set sw=4 sts=4 tw=0 expandtab:
