ranked.py
=========

Note that this is obsolete. The `elections` module should be used instead.

The sample Python session below shows off most of the functions of the
[ranked](elections/software/ranked.py) module. Hopefully, the
comments in the code explain the rest. Note that `parseBLT('foo.blt')`
can take several seconds; however, the first time a `.blt` file is
parsed, a cached version with the extension `.pickle` is written which
makes subsequent calls to `parseBLT('foo.blt')` significantly faster.

```python
>>> import ranked
>>> root, numBallots, ranks, candidates, description = ranked.parseBLT('2010-Oakland-Mayor.blt')
>>> description
'Mayor - Oakland (RCV)'
>>> winner, counts, elimination = ranked.irv(root, rules=ranked.SFRCVRules)
>>> candidates[winner]
'JEAN QUAN'
>>> for c in sorted(candidates):
...     print '%30s:' % candidates[c], counts[c]
... 
                    DON PERATA: [40342, 45465, 51872]
               TERENCE CANDELL: [2315, 0, 0]
                  GREG HARLAND: [966, 0, 0]
                   DON MACLEAY: [1630, 0, 0]
                     JEAN QUAN: [29266, 35033, 53897]
                 ARNOLD FIELDS: [733, 0, 0]
                     JOE TUMAN: [14347, 0, 0]
                  MARCIE HODGE: [2994, 0, 0]
 LARRY LIONEL ''LL'' YOUNG JR.: [933, 0, 0]
                REBECCA KAPLAN: [25813, 32719, 0]
                      Write-In: [268, 0, 0]
>>> ranked.irvUB(root)
2026.0
>>> ranked.irvLB(root)[0]
2025
>>> m = ranked.buildCondorcet(root)
>>> candidates[ranked.condorcetWinner(m)]
'JEAN QUAN'
>>> ranked.condorcetMargin(m)
2025
```
