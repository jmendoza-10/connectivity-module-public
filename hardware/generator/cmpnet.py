"""Compare two KiCad netlists by connectivity (sets of (ref,pin) per net), ignoring net names."""
import sys
from sexp import parse, find
def load(p):
    t = parse(open(p).read())[0]
    comps = {find(c, 'ref')[0][1][1]: find(c, 'value')[0][1][1] for c in find(find(t, 'components')[0], 'comp')}
    nets = {}
    for n in find(find(t, 'nets')[0], 'net'):
        nm = find(n, 'name')[0][1][1]
        nodes = frozenset((find(x, 'ref')[0][1][1], find(x, 'pin')[0][1][1]) for x in find(n, 'node'))
        nets[nm] = nodes
    return comps, nets
ca, na = load(sys.argv[1]); cb, nb = load(sys.argv[2])
print('components', len(ca), len(cb), 'same refs+values:', ca == cb)
if ca != cb:
    for r in sorted(set(ca) ^ set(cb))[:20]: print('  ref diff', r)
    for r in sorted(set(ca) & set(cb)):
        if ca[r] != cb[r]: print('  value diff', r, ca[r], cb[r])
sa = {v: k for k, v in na.items()}; sb = {v: k for k, v in nb.items()}
onlya = set(sa) - set(sb); onlyb = set(sb) - set(sa)
print('nets', len(na), len(nb), 'identical node-sets:', len(set(sa) & set(sb)), 'only-old:', len(onlya), 'only-new:', len(onlyb))
for s_ in sorted(onlya, key=lambda x: sa[x])[:30]: print('  OLD', sa[s_], sorted(s_)[:6])
for s_ in sorted(onlyb, key=lambda x: sb[x])[:30]: print('  NEW', sb[s_], sorted(s_)[:6])
named = [(sa[k], sb[k]) for k in set(sa) & set(sb) if not sa[k].startswith('unconnected')]
ren = [(a, b) for a, b in named if a.split('/')[-1] != b.split('/')[-1]]
print('named nets matched:', len(named), 'with different leaf name:', len(ren))
for a, b in ren[:10]: print('  rename', a, '->', b)
print('RESULT:', 'EQUIVALENT' if not onlya and not onlyb and ca == cb else 'DIFFERENT')
