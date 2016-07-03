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
This module contains the Election class which holds all of the information about
an election.
'''

# This class has no methods at all, it's just a struct, so disable the warning
# about not having enough public messages.
# pylint: disable=R0903
class Election(object):
    '''This class holds all of the information about an election.

    When unpickling an L{Election} object C{e}, check that C{e.version}
    is the same as C{Election.VERSION}.
    @type VERSION: number
    @cvar VERSION: The version of this class.
    @type version: number
    @ivar version: The version of this instance.
    @type names: dict
    @ivar names: Mapping between candidate indices and candidate names.
    @type profile: L{Node}
    @ivar profile: The root of the tree representation of the profile.
    @type ranks: number
    @ivar ranks: The maximum number of candidates that can be ranked on a
    ballot.
    @type seats: number
    @ivar seats: The number of candidates to be elected.
    @type description: string
    @ivar description: Description of the election.
    '''
    # This should be incremented when this class changes
    VERSION = 1
    def __init__(self, names, profile, ranks, seats, description):
        '''Create a new Election

        @type  names: dict
        @param names: Mapping between candidate indices and candidate names.
        @type  profile: L{Node}
        @param profile: The root of the tree representation of the profile.
        @type  ranks: number
        @param ranks: The maximum number of candidates that can be ranked on a
        ballot.
        @type  seats: number
        @param seats: The number of candidates to be elected.
        @type  description: string
        @param description: Description of the election.
        '''
        object.__init__(self)
        self.version = Election.VERSION

        self.names = names
        self.profile = profile
        self.ranks = ranks
        self.seats = seats
        self.description = description
        assert set(names) == profile.children(), '%s != %s' % (set(names), set(profile.children()))

# vim: set sw=4 sts=4 tw=0 expandtab:
