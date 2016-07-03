Background
==========

Instant-Runoff Voting
---------------------
Instant-runoff voting---also called ranked-choice voting, or the
alternative vote---is a system of voting where voters rank candidates
in order of preference rather than simply marking their most preferred
candidate. Vote counting happens in rounds. In each round, the
candidate with the fewest, top choice votes is eliminated and votes
for that candidate are distributed to the next ranked candidate on the
ballot.

Post-Election Auditing
----------------------

A post-election audit is a procedure where some subset of the cast
ballots are selected at random and compared to the electronic record
used to produce the election tallies. The goal of an audit is to
convince the losers that they did not win the election. To accomplish
this goal, the audit is designed in such a way as to provide a
statistical bound on the chance that an incorrect election outcome is
not detected and corrected.

In recent years, researchers have designed several methods of
auditing plurality elections and very recently methods have been
proposed for auditing IRV elections.

IRV Data
========

In order to design and compare post-election audits, researchers
need access to real election data. Some of this data is available, but
scattered on various county websites. As a result, researchers have to
track down different data sets, frequently posted online in different
formats. This makes comparisons difficult as there is no standard
corpus of data to use to evaluate auditing algorithms.

The data directory contains ballot data for IRV elections in a
simplified version of the .blt file format used by
[OpenSTV](http://www.openstv.org).

There does not seem to be any remaining documentation on the full
file format; however, this Stack Overflow
[answer](http://stackoverflow.com/questions/2233695/c-generating-blt-files-for-openstv-elections/2234236#2234236)
provides a good, if incomplete, overview. The version used by the
files below uses only a subset of the features that OpenSTV supports.
For example, consider the following.
```text
# Created by Stephen Checkoway
5 1
1 1 2 3 0
1 1 4 - 0
1 4 2 1 0
1 5 - - 0
1 1=2=3 2 - 0
0
"Alice"
"Bob"
"Carol"
"Dave"
"Eve"
"Example election"
```

This example contains several parts:
1. Lines at the beginning of the file starting with `#` are comments
   and are ignored.
2. The first noncomment line consists of two numbers: the number of
   candidates and the number of seats. Since these are IRV elections,
   the latter number will always be 1, except for the 2009 Aspen City
   Council election which used a modified IRV algorithm to elect two
   council members.
3. The next lines are the individual ballots. The `1` at the beginning
   is, apparently, the weight of the ballot. It will always be `1`. The
   positive, space separated numbers are the candidates ranked in order
   of preference. A `-` indicates that no candidate was given for that
   rank where as a sequence of numbers separated by `=` indicate that
   each of those candidates was marked---i.e., an overvote. A value of
   `-=-` denotes an overvote for which the official election data does
   not indicate the candidates marked. The `0` denotes the end of the
   ballot.
4. The line containing only `0` denotes the end of the ballots.
5. If there are _n_ candidates, then the next _n_ lines will be the
   names of the candidates in double quotes.
6. The final line is the description of the election in double quotes.

IRV Code
===========
The code directory contains some Python code for manipulating this data as
well as some extra scripts that were helpful for creating the data from the
official formats. The obsolete directory has some obsolete code.

The data from the San Francisco Bay Area and Pierce County was
produced from "ballot image files" and "master lookup files" provided
by the corresponding jurisdictions. The `txttoblt.py` Python script
takes the two files as input and produces a .blt file as output.

The data from the two 2009 Aspen elections was produced from an
unofficial CSV file containing the election results using the
`aspentoblt.py` Python script. (I am attempting to get the official
data.)

`code/elections` is a Python module that contains functions for
reading and writing .blt files, running IRV elections, producing
lower and upper bounds on the margin of an IRV election, and for
treating the ranked ballot data as if it were for a Condorcet method
and producing the Condorcet winner---if one exits---and a lower bound
for the Condorcet margin. In addition, if `CPLEX` is installed, the
exact margin of an IRV election can be computed. This module contains
all of the code used to produce the results in this
[technical report](https://www.uic.edu/~s/papers/nonplurality2011).

The code, and in particular the api is somewhat documented and an example
appears below.

An older version was called `ranked.py`. There is no real
documentation for the older module, but a sample interactive
session is in `obsolete`, as is the code.

For the Condorcet functions, the `numpy` Python module is required. To
compute the exact margin of an IRV election, the CPLEX optimization
library and the python wrapper need to be installed. Since CPLEX is
not free, the functionality to solve integer-linear programs is
abstracted slightly. It should be relatively simple to add a new
optimization library, if desired.

There are many different forms of IRV that differ slightly in the
details. The IRV functions in the `elections` module implement three
different candidate elimination rules: the base IRV elimination rules,
the San Francisco RCV rules, and the complete IRV rules.

Base IRV elimination rules
: These rules eliminates the candidate with
  the fewest votes in each round until a single continuing candidate
  is the top-choice on a majority of the continuing ballots. Ties are
  broken arbitrarily, but deterministically---that is, they will
  always be broken in the same way.

San Francisco RCV elimination rules
: These rules eliminates the
  largest set of candidates in each round for which the sum of the
  votes for those candidates is /less than/ the votes for all of the
  other candidates. Candidates with the same number of votes are
  treated equally, either both are eliminated or neither are. The one
  exception to this is when the largest elimination set consists of a
  single candidate who has the same number of votes as another
  candidate. As with the Base IRV elimination rule, in this case, the
  candidate selected for elimination is chosen arbitrarily, but
  deterministically. Furthermore, a warning about this case is printed
  to standard error.

Complete IRV elimination rules
: These rules are identical to the
  base rules except that they continue until there are only two
  candidates who remain rather than stopping once a single candidate
  gets a majority of the votes.

The rules to use can be selected by using the `rules` keyword argument
to the relevant functions with the values `elections.irv.BASE_IRV_RULES`,
`elections.irv.SF_RCV_RULES`, or `elections.irv.COMPLETE_IRV_RULES`.

Other rules are possible, but not implemented. For example, the 2009
Aspen City Council election used very different rules for electing two
city council members and the Burlington mayoral elections treat
overvotes differently. The Aspen rules could be implemented without
too much difficulty. The Burlington rules would require changing the
"ballot cleaning" rules and modification to the basic tree data
structure used to represent the set of ballots.

Elections Module Example
========================

Below is a simple Python script that will read in a .blt file, compute
various bound, and then print the results. Note that computing the
Condorcet winner and lower bound requires the `numpy` package and
computing the IRV margin exactly requires the `CPLEX` library and
Python wrapper.

```python
#!/usr/bin/env python

import sys

from elections import blt, irv, condorcet

if len(sys.argv) != 2:
    print 'Usage: %s election.blt' % sys.argv[0]
    sys.exit(1)

election = blt.read_blt(sys.argv[1])
winner, _, elim_order = irv.irv(election)
slb = irv.irv_simple_lb(election, rules=irv.COMPLETE_IRV_RULES)
lb = irv.irv_lb(election)
ub = irv.irv_ub(election, winner=winner, elim_order=elim_order)
margin = irv.irv_margin(election, winner=winner, elim_order=elim_order, ub=ub)
m = condorcet.build_condorcet(election)
cwinner = condorcet.condorcet_winner(m)
clb = condorcet.condorcet_lb(m, winner=cwinner)

print 'IRV: %d; %d <= %d <= %d <= %d' % (winner, slb, lb, margin, ub)
print 'Condorcet: %d; %d' % (cwinner, clb)
```
