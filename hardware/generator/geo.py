import sys, symbols
from engine import symdef, Part, place
for lib in sys.argv[1:]:
    lib, _, unit = lib.partition('@'); unit = int(unit or 1)
    d = symdef(lib)
    nets = {p[1]: 'X' for p in d.unit_pins(unit)}
    it = Part(None, d, nets, unit, 0); place(it, 0, 0)
    print(lib, unit, 'bbox', [round(v, 2) for v in it.bbox()])
    print('  ', ' '.join(f"{'/'.join(p[0] for p in t['g']['pins'])[:12]}:{t['g']['pins'][0][1][:10]}@({t['x']:g},{t['y']:g}){'RLDU'[[(1,0),(-1,0),(0,1),(0,-1)].index(t['o'])]}" for t in it.tips()))
