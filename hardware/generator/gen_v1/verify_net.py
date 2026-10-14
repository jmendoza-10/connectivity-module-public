import json
from collections import Counter
from sexp import parse, find
import sys
# usage: python3 verify_net.py <exported netlist> (rev 0.1 checker)
t=parse(open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/wwan.net').read())[0]
comps=find(find(t,'components')[0],'comp')
refs=Counter(find(c,'ref')[0][1][1] for c in comps); assert not [r for r,n in refs.items() if n>1]
got={}
for n in find(find(t,'nets')[0],'net'):
    got[find(n,'name')[0][1][1]]={(find(x,'ref')[0][1][1], find(x,'pin')[0][1][1]) for x in find(n,'node')}
exp=json.load(open('netlist_report.json'))
want={net:{(ref,p) for sh,ref,pins in lst if not ref.startswith('#') for p in pins.split('/')} for net,lst in exp.items()}
bynode={nd:nm for nm,nodes in got.items() for nd in nodes}
bad=0
for net,s in want.items():
    names={bynode.get(nd) for nd in s}
    if len(names)!=1 or None in names: bad+=1; print('SPLIT',net,names); continue
    gn=names.pop()
    if got[gn]!=s: bad+=1; print('MERGED',net,gn,sorted(got[gn]-s)[:5])
    if gn.split('/')[-1]!=net: print('name differs',net,gn)
nc=[k for k in got if k.startswith('unconnected')]
print(f'components {len(comps)}; intended nets {len(want)}; kicad named nets {len(got)-len(nc)}; NC pins {len(nc)}; problems {bad}')
