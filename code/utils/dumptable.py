#!/usr/bin/env python

import sys
import os.path
import glob

print '''The Data
========

| Year | Location | Contest | File |
|------|----------|---------|------|'''
for i in sorted(glob.glob('data/*.blt')):
    name, ext = os.path.splitext(os.path.basename(i))
    parts = name.split( '-' )
    year = parts[0]
    location = parts[1].replace('_', ' ')
    contest = parts[2].replace('_', ' ')
    if len(parts) > 3:
        if parts[3][0] == 'W':
            contest += ', ward %s' % parts[3][1:]
        else:
            contest += ', district %s' % parts[3][1:]
    # year location contest
    print '| %s | %s | %s | %s |' % (year, location, contest, name + ext)
# vim: set sw=4 sts=4 tw=0 expandtab:
